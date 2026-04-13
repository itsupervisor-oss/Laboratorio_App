from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional # 🟢 Asegúrate de tener esto importado arriba
from fastapi.staticfiles import StaticFiles
import sqlite3
import os # 👈 Añade esta importación arriba del todo

app = FastAPI(title="API del Laboratorio Multi-Sucursal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛠️ CONFIGURACIÓN DE RUTAS
base_path = os.path.dirname(os.path.abspath(__file__))

# 🔍 PRUEBA DE DIAGNÓSTICO
#print(f"--- DIAGNÓSTICO DE RUTAS ---")
#print(f"📍 Carpeta del servidor: {base_path}")
#print(f"📂 Archivos encontrados: {os.listdir(base_path)}")
#print(f"---------------------------")

app.mount("/estatico", StaticFiles(directory=base_path, html=True), name="static")

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
    conexion = sqlite3.connect("laboratorio.db") #
    cursor = conexion.cursor()

    # Capturamos la hora exacta en el momento del clic
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if nuevo_estado == "Llamado":
        # Recepcionista llama al paciente
        cursor.execute("""
            UPDATE turnos SET estado = ?, hora_atencion = ? WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))
        
    elif nuevo_estado == "Registrado":
        # Recepcionista termina el registro/cobro
        cursor.execute("""
            UPDATE turnos SET estado = ?, hora_registrado = ? WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))
        
    elif nuevo_estado == "Derivado":
        # Recepcionista envía al paciente a toma de muestra
        cursor.execute("""
            UPDATE turnos SET estado = ?, hora_derivado = ? WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))

    elif nuevo_estado == "Muestra Tomada":
        # 🧪 La tomadora de muestra confirma el procedimiento
        cursor.execute("""
            UPDATE turnos SET estado = ?, hora_toma_muestra = ? WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))

    elif nuevo_estado == "Finalizado":
        # 🟢 El paciente termina su visita y se retira
        cursor.execute("""
            UPDATE turnos SET estado = ?, hora_finalizado = ? WHERE id_turno = ?
        """, (nuevo_estado, hora_actual, id_turno))
        
    else:
        # Fallback para cualquier otro cambio de estado
        cursor.execute("""
            UPDATE turnos SET estado = ? WHERE id_turno = ?
        """, (nuevo_estado, id_turno))

    conexion.commit() #
    conexion.close() #
    return {"mensaje": f"Estado cambiado a {nuevo_estado} exitosamente"}


@app.put("/iniciar_muestra/{id_turno}")
def iniciar_muestra(id_turno: int):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Actualizamos el estado y guardamos la hora exacta en la que entra al box
    cursor.execute("""
        UPDATE turnos 
        SET estado = 'En Box', 
            hora_inicio_muestra = ?
        WHERE id_turno = ?
    """, (hora_actual, id_turno,))

    conexion.commit()
    conexion.close()
    
    return {"mensaje": "El paciente ha ingresado a la toma de muestra"}

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

    # 1. INICIALIZACIÓN DE SEGURIDAD (Evita el NameError)
    lista_turnos = []
    lista_satisfaccion = []
    lista_eficiencia = []
    lista_alertas = []
    
    filtro_turnos = ""
    filtro_satisfaccion = ""
    filtro_eficiencia = ""
    parametros = []

    # 2. CONFIGURAR FILTROS DE FECHA
    if fecha_inicio and fecha_fin:
        filtro_turnos = "WHERE date(hora_registro) BETWEEN ? AND ?"
        filtro_satisfaccion = "WHERE date(fecha_hora) BETWEEN ? AND ?"
        filtro_eficiencia = "AND date(hora_registro) BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]

    # 3. DATOS DE TURNOS (Pacientes hoy)
    cursor.execute(f"""
        SELECT sucursal, COUNT(*) as total,
               SUM(CASE WHEN estado = 'Esperando' THEN 1 ELSE 0 END) as esperando,
               SUM(CASE WHEN estado = 'Derivado' THEN 1 ELSE 0 END) as en_muestreo
        FROM turnos 
        {filtro_turnos}
        GROUP BY sucursal
    """, parametros)
    turnos_db = cursor.fetchall()
    lista_turnos = [{"ubicacion": suc, "total": tot, "esperando": esp, "en_muestreo": mues} for suc, tot, esp, mues in turnos_db]

    # 4. DATOS DE SATISFACCIÓN (Promedio de estrellas)
    cursor.execute(f"""
        SELECT sucursal, COUNT(*) as votos, AVG(puntaje) as promedio
        FROM satisfaccion 
        {filtro_satisfaccion}
        GROUP BY sucursal
    """, parametros)
    satisfaccion_db = cursor.fetchall()
    lista_satisfaccion = [{"ubicacion": suc, "votos": vot, "promedio": round(prom, 1) if prom else 0} for suc, vot, prom in satisfaccion_db]

    # 5. DATOS DE EFICIENCIA (Tiempos de espera y atención)
    cursor.execute(f"""
        SELECT sucursal, 
               COALESCE(AVG((julianday(hora_atencion) - julianday(hora_registro)) * 1440), 0) as prom_espera,
               COALESCE(AVG((julianday(hora_registrado) - julianday(hora_atencion)) * 1440), 0) as prom_atencion,
               COALESCE(AVG((julianday(hora_inicio_muestra) - julianday(hora_derivado)) * 1440), 0) as prom_espera_lab,    
               COALESCE(AVG((julianday(hora_toma_muestra) - julianday(hora_inicio_muestra)) * 1440), 0) as prom_muestreo
        FROM turnos 
        WHERE hora_registro IS NOT NULL
        {filtro_eficiencia}
        GROUP BY sucursal
    """, parametros)
    eficiencia_db = cursor.fetchall()
    lista_eficiencia = [
        {"sucursal": suc, 
         "espera": round(esp, 1), 
         "atencion": round(ate, 1), 
         "espera_lab": round(esp_lab, 1),       # 👈 Nuevo dato
         "extraccion": round(extraccion, 1)}    # 👈 Nuevo dato
        for suc, esp, ate, esp_lab, extraccion in eficiencia_db
    ]

    # 6. ALERTAS CRÍTICAS (Satisfacción baja)
    cursor.execute(f"""
        SELECT sucursal, 
               puntaje, 
               comentario, date(fecha_hora) 
        FROM satisfaccion 
        WHERE puntaje <= 3 {filtro_satisfaccion.replace("WHERE", "AND")}
        ORDER BY fecha_hora DESC LIMIT 5
    """, parametros)
    alertas_db = cursor.fetchall()
    lista_alertas = [{"sucursal": suc, "estrellas": puntaje, "comentario": coment or "Sin comentario", "fecha": fecha} for suc, puntaje, coment, fecha in alertas_db]

    conexion.close()
    
    # 7. RETORNO DE RESULTADOS
    return {
        "turnos": lista_turnos,
        "satisfaccion": lista_satisfaccion,
        "eficiencia": lista_eficiencia,
        "alertas": lista_alertas
    }