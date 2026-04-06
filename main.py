from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional # 🟢 Asegúrate de tener esto importado arriba
import sqlite3

app = FastAPI(title="API del Laboratorio Multi-Sucursal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. NUEVOS MODELOS: Ahora exigimos la ciudad y sucursal en ambos procesos
class NuevoTurno(BaseModel):
    ciudad: str
    sucursal: str
    nombre_paciente: str
    tipo_paciente: str
    tipo_servicio: str

class Voto(BaseModel):
    ciudad: str
    sucursal: str
    puntaje: int
    comentario: Optional[str] = "" # 🟢 NUEVO CAMPO OPCIONAL

# --- RUTAS WEB ---

@app.get("/turnos")
def obtener_turnos(ciudad: str, sucursal: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # 1. Obtenemos la fecha de hoy
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    # 2. Pedimos los campos y ordenamos por ID de forma DESCENDENTE
    # Esto pone el ID más alto (el más nuevo) al principio de la lista
    cursor.execute("""
        SELECT id_turno, nombre_paciente, tipo_paciente, tipo_servicio, estado 
        FROM turnos 
        WHERE ciudad = ? AND sucursal = ? AND date(hora_registro) = ?
        ORDER BY id_turno DESC
    """, (ciudad, sucursal, hoy))
    
    turnos_crudos = cursor.fetchall()
    conexion.close()
    
    # 3. Formateamos los datos para enviarlos a la web
    lista_formateada = []
    for fila in turnos_crudos:
        id_t, nombre, tipo, servicio, est = fila
        lista_formateada.append({
            "id": id_t,
            "paciente": nombre,
            "tipo": tipo,
            "servicio": servicio,
            "estado": est
        })
    
    return lista_formateada


@app.post("/turnos")
def registrar_paciente(turno: NuevoTurno):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # 🟢 OBLIGAMOS a que la hora inicial se guarde con el reloj local de Bolivia
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insertamos los datos, incluyendo explícitamente la hora_registro
    cursor.execute("""
        INSERT INTO turnos (ciudad, sucursal, nombre_paciente, tipo_paciente, tipo_servicio, hora_registro) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (turno.ciudad, turno.sucursal, turno.nombre_paciente, turno.tipo_paciente, turno.tipo_servicio, hora_actual))
    
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "¡Paciente registrado exitosamente!", "ticket": nuevo_id}


@app.put("/turnos/{id_turno}")
def actualizar_estado(id_turno: int, nuevo_estado: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # Capturamos la hora exacta en el momento en que se presiona cualquier botón
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nuevo_estado == "Llamado":
        # 🟢 RESTAURADO: Guarda la hora_atencion cuando la recepcionista presiona "Llamar"
        cursor.execute("""
            UPDATE turnos 
            SET estado = ?, hora_atencion = ? 
            WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))
        
    elif nuevo_estado == "Registrado":
        # 🟣 NUEVO: Guarda la hora_registrado cuando presiona el botón morado
        cursor.execute("""
            UPDATE turnos 
            SET estado = ?, hora_registrado = ? 
            WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))
        
    else:
        # Para los demás estados (como "Finalizado")
        cursor.execute("""
            UPDATE turnos 
            SET estado = ? 
            WHERE id_turno = ?
        """, (nuevo_estado, id_turno))

    conexion.commit()
    conexion.close()
    return {"mensaje": f"Estado cambiado a {nuevo_estado} exitosamente"}

@app.post("/votar")
def registrar_voto(voto: Voto):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 2. Actualizamos el INSERT para que guarde los 4 datos
    cursor.execute("""
        INSERT INTO satisfaccion (ciudad, sucursal, puntaje, comentario, fecha_hora)
        VALUES (?, ?, ?, ?, ?)
    """, (voto.ciudad, voto.sucursal, voto.puntaje, voto.comentario, hora_actual))
    
    conexion.commit()
    conexion.close()
    return {"mensaje": "Voto registrado correctamente"}


# 5. GET: Dashboard Gerencial (Estadísticas agrupadas con filtro de fecha)
@app.get("/estadisticas")
def obtener_estadisticas(fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # 🟢 PREPARAMOS LOS FILTROS DE FECHA
    # Si el usuario mandó fechas, armamos el trozo de código SQL para filtrar
    filtro_turnos = ""
    filtro_satisfaccion = ""
    filtro_eficiencia = ""
    parametros = []

    if fecha_inicio and fecha_fin:
        # date() extrae solo el 'YYYY-MM-DD' de nuestra columna para comparar exacto
        filtro_turnos = "WHERE date(hora_registro) BETWEEN ? AND ?"
        filtro_satisfaccion = "WHERE date(fecha_hora) BETWEEN ? AND ?"
        filtro_eficiencia = "AND date(hora_registro) BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]

    # 1. Datos de Turnos (Pacientes)
    cursor.execute(f"""
        SELECT sucursal, COUNT(*) as total,
               SUM(CASE WHEN estado = 'Esperando' THEN 1 ELSE 0 END) as esperando
        FROM turnos 
        {filtro_turnos}
        GROUP BY sucursal
    """, parametros)
    turnos_db = cursor.fetchall()
    
    lista_turnos = [{"ubicacion": suc, "total": tot, "esperando": esp} for suc, tot, esp in turnos_db]

    # 2. Datos de Satisfacción
    cursor.execute(f"""
        SELECT sucursal, COUNT(*) as votos, AVG(puntaje) as promedio
        FROM satisfaccion 
        {filtro_satisfaccion}
        GROUP BY sucursal
    """, parametros)
    satisfaccion_db = cursor.fetchall()
    
    lista_satisfaccion = [{"ubicacion": suc, "votos": vot, "promedio": round(prom, 1) if prom else 0} for suc, vot, prom in satisfaccion_db]

    # 3. Datos de Eficiencia (Espera y Atención)
    cursor.execute(f"""
        SELECT sucursal, 
               COALESCE(AVG((julianday(hora_atencion) - julianday(hora_registro)) * 1440), 0) as prom_espera,
               COALESCE(AVG((julianday(hora_registrado) - julianday(hora_atencion)) * 1440), 0) as prom_atencion
        FROM turnos 
        WHERE hora_registro IS NOT NULL AND hora_atencion IS NOT NULL AND hora_registrado IS NOT NULL
        {filtro_eficiencia}
        GROUP BY sucursal
    """, parametros)
    eficiencia_db = cursor.fetchall()
    
    lista_eficiencia = [{"sucursal": suc, "espera": round(esp, 1), "atencion": round(ate, 1)} for suc, esp, ate in eficiencia_db]
    # ------------------------------------
    
    # 🟢 4. NUEVO: ALERTAS CRÍTICAS (1 y 2 estrellas)
    # Buscamos los comentarios más recientes que necesitan atención inmediata
    cursor.execute(f"""
        SELECT sucursal, 
                   CASE WHEN puntaje = 3 THEN 2 ELSE puntaje END as puntaje, 
                   comentario, date(fecha_hora) 
        FROM satisfaccion 
        WHERE puntaje <= 3 {filtro_satisfaccion.replace("WHERE", "AND")}
        ORDER BY fecha_hora DESC LIMIT 5
    """, parametros)
    
    alertas_db = cursor.fetchall()
    lista_alertas = [{"sucursal": suc, "estrellas": puntaje, "comentario": coment or "Sin comentario", "fecha": fecha} for suc, puntaje, coment, fecha in alertas_db]

    # ------------------------------------
    conexion.close()
    
    return {
        "turnos": lista_turnos,
        "satisfaccion": lista_satisfaccion,
        "eficiencia": lista_eficiencia,
        "alertas": lista_alertas # 🟢 Añadimos las alertas a la respuesta
    }