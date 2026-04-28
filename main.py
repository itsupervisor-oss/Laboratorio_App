from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional # 🟢 Asegúrate de tener esto importado arriba
from fastapi.staticfiles import StaticFiles
import sqlite3
import os # 👈 Añade esta importación arriba del todo

app = FastAPI(title="API del Laboratorio Multi-Sucursal")

# 3. TU NUEVA FÁBRICA DE CONEXIONES (Justo aquí)
def obtener_conexion():
    conexion = sqlite3.connect("laboratorio.db", timeout=15.0, check_same_thread=False)
    conexion.execute("PRAGMA journal_mode=WAL;")
    return conexion

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


# 1. Creamos un "molde" para los datos del nuevo empleado
class NuevoEmpleado(BaseModel):
    nombre: str
    ciudad: str
    sucursal: str
# 2. Ruta para ver a TODOS los empleados (activos e inactivos)
@app.get("/admin/empleados")
def obtener_todos_empleados():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, ciudad, sucursal, estado FROM tomadores")
        datos = cursor.fetchall()
        #conexion.close()  
    lista = [{"id": i, "nombre": n, "ciudad": c, "sucursal": s, "estado": e} for i, n, c, s, e in datos]
    return {"empleados": lista}

# 3. Ruta para agregar un empleado nuevo
@app.post("/admin/empleados")
def agregar_empleado(empleado: NuevoEmpleado):
    # Abrimos la puerta con tu nueva fábrica blindada
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO tomadores (nombre, ciudad, sucursal, estado) 
            VALUES (?, ?, ?, 'Activo')
        """, (empleado.nombre, empleado.ciudad, empleado.sucursal))
        
        conexion.commit()
    
    return {"mensaje": "Empleado registrado exitosamente"}

# 4. Ruta para activar o desactivar un empleado
@app.put("/admin/empleados/{id_empleado}/estado")
def cambiar_estado_empleado(id_empleado: int, estado: str):
    
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE tomadores SET estado = ? WHERE id = ?", (estado, id_empleado))
        
        conexion.commit()
        
    return {"mensaje": f"Estado cambiado a {estado}"}

@app.put("/admin/empleados/{id_empleado}/reasignar")
def reasignar_empleado(id_empleado: int, datos: dict):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        
        cursor.execute(
            "UPDATE tomadores SET ciudad = ?, sucursal = ? WHERE id = ?",
            (datos['ciudad'], datos['sucursal'], id_empleado)
        )
        # Guardamos los cambios antes de salir
        conexion.commit()
        
    return {"mensaje": "Empleado reasignado con éxito"}

# ---------------------------------------------------------
# RUTAS PARA LOS COMBOS DEPENDIENTES (CIUDAD Y SUCURSAL)
# ---------------------------------------------------------

# 1. Obtener lista de ciudades únicas
@app.get("/ciudades")
def obtener_ciudades():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        # Usamos DISTINCT para que no nos repita "LaPaz" tres veces
        cursor.execute("SELECT DISTINCT ciudad FROM sucursales")
        datos = cursor.fetchall()
    
    # Extraemos el texto de la tupla (usamos d para evitar el error de hace rato 😉)
    lista_ciudades = [c for (c,) in datos]
    return {"ciudades": lista_ciudades}

# 2. Obtener sucursales según la ciudad seleccionada
@app.get("/sucursales/{ciudad}")
def obtener_sucursales(ciudad: str):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        # Buscamos solo las sucursales que pertenecen a la ciudad que nos mandan
        cursor.execute("SELECT nombre_sucursal FROM sucursales WHERE ciudad = ? AND estado = 'Activo'", (ciudad,))
        datos = cursor.fetchall()
    
    lista_sucursales = [s for (s,) in datos]
    return {"sucursales": lista_sucursales}


# --- RUTAS PARA GESTIONAR EL DIRECTORIO DE SUCURSALES ---

# 1. Obtener TODAS las sucursales (para la tabla de administración)
@app.get("/admin/sucursales")
def obtener_todas_sucursales():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT id, ciudad, nombre_sucursal, estado FROM sucursales")
        datos = cursor.fetchall()

    # Usamos el desempacado seguro para evitar errores de formato
    lista = [{"id": i, "ciudad": c, "nombre": n, "estado": e} for i, c, n, e in datos]
    return {"sucursales": lista}

# 2. Crear una nueva sucursal (POST)
@app.post("/admin/sucursales")
def crear_sucursal(datos: dict):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO sucursales (ciudad, nombre_sucursal, estado) VALUES (?, ?, 'Activo')",
                (datos['ciudad'], datos['nombre'])
            )
            conexion.commit()
        # Al salir de esta sangría, el portero (with) CIERRA LA PUERTA automáticamente.
        # ¡No necesitamos el 'finally: conexion.close()'!
        
        # Una vez que la base de datos está libre y segura, respondemos:
        return {"mensaje": "Sucursal creada con éxito"}
        
    except Exception as e:
        # Si algo falla (ej. faltan datos), atrapamos el error aquí
        return {"error": f"Hubo un problema al crear la sucursal: {str(e)}"}

# 3. Cambiar estado de una sucursal (PUT)
@app.put("/admin/sucursales/{id}/estado")
def cambiar_estado_sucursal(id: int, estado: str):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE sucursales SET estado = ? WHERE id = ?", (estado, id))
        conexion.commit()
    return {"mensaje": f"Sucursal actualizada a {estado}"}
#--------------------------------------------------------
#--------------------------------------------------------

# --- RUTAS WEB ---

@app.get("/turnos")
def obtener_turnos(ciudad: str, sucursal: str):
    # 1. Obtenemos la fecha de hoy
    hoy = datetime.now().strftime("%Y-%m-%d")
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()        
       
        # 2. Pedimos los campos y ordenamos por ID de forma DESCENDENTE
        # Esto pone el ID más alto (el más nuevo) al principio de la lista
        cursor.execute("""
            SELECT id_turno, nombre_paciente, tipo_paciente, tipo_servicio, estado 
            FROM turnos 
            WHERE ciudad = ? AND sucursal = ? AND date(hora_registro) = ?
            ORDER BY id_turno DESC
        """, (ciudad, sucursal, hoy))
        
        turnos_crudos = cursor.fetchall()    
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
    # 🟢 OBLIGAMOS a que la hora inicial se guarde con el reloj local de Bolivia
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        # Insertamos los datos, incluyendo explícitamente la hora_registro
        cursor.execute("""
            INSERT INTO turnos (ciudad, sucursal, nombre_paciente, tipo_paciente, tipo_servicio, hora_registro) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (turno.ciudad, turno.sucursal, turno.nombre_paciente, turno.tipo_paciente, turno.tipo_servicio, hora_actual))
        
        conexion.commit()
        nuevo_id = cursor.lastrowid
    return {"mensaje": "¡Paciente registrado exitosamente!", "ticket": nuevo_id}


from typing import Optional # 👈 Asegúrate de que esta línea esté al inicio de tu archivo

@app.put("/turnos/{id_turno}")
def actualizar_estado(id_turno: int, nuevo_estado: str, tomador: Optional[str] = None): # 👈 Añadimos tomador aquí
    # Capturamos la hora exacta en el momento del clic
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        if nuevo_estado == "Llamado":
            cursor.execute("""
                UPDATE turnos SET estado = ?, hora_atencion = ? WHERE id_turno = ?
            """, (nuevo_estado, hora_actual, id_turno))
            
        elif nuevo_estado == "Registrado":
            cursor.execute("""
                UPDATE turnos SET estado = ?, hora_registrado = ? WHERE id_turno = ?
            """, (nuevo_estado, hora_actual, id_turno))
            
        elif nuevo_estado == "Derivado":
            cursor.execute("""
                UPDATE turnos SET estado = ?, hora_derivado = ? WHERE id_turno = ?
            """, (nuevo_estado, hora_actual, id_turno))

        elif nuevo_estado == "Muestra Tomada":
            # 🧪 Aquí es donde guardamos quién hizo la extracción
            cursor.execute("""
                UPDATE turnos 
                SET estado = ?, hora_toma_muestra = ?, tomador = ? 
                WHERE id_turno = ?
            """, (nuevo_estado, hora_actual, tomador, id_turno)) # 👈 Agregamos tomador al UPDATE

        elif nuevo_estado == "Finalizado":
            cursor.execute("""
                UPDATE turnos SET estado = ?, hora_finalizado = ? WHERE id_turno = ?
            """, (nuevo_estado, hora_actual, id_turno))
            
        else:
            cursor.execute("""
                UPDATE turnos SET estado = ? WHERE id_turno = ?
            """, (nuevo_estado, id_turno))
        conexion.commit()

    return {"mensaje": f"Estado cambiado a {nuevo_estado} exitosamente"}


@app.put("/iniciar_muestra/{id_turno}")
def iniciar_muestra(id_turno: int):
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        # Actualizamos el estado y guardamos la hora exacta en la que entra al box
        cursor.execute("""
            UPDATE turnos 
            SET estado = 'En Box', 
                hora_inicio_muestra = ?
            WHERE id_turno = ?
        """, (hora_actual, id_turno,))

        conexion.commit()

    return {"mensaje": "El paciente ha ingresado a la toma de muestra"}

@app.post("/votar")
def registrar_voto(voto: Voto):
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        
        # 2. Actualizamos el INSERT para que guarde los 4 datos
        cursor.execute("""
            INSERT INTO satisfaccion (ciudad, sucursal, puntaje, comentario, fecha_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (voto.ciudad, voto.sucursal, voto.puntaje, voto.comentario, hora_actual))
        
        conexion.commit()
    return {"mensaje": "Voto registrado correctamente"}

@app.get("/tomadores")
def obtener_tomadores(ciudad: str, sucursal: str):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        # Buscamos solo los empleados activos de esa sucursal específica
        cursor.execute("""
            SELECT nombre 
            FROM tomadores 
            WHERE ciudad = ? AND sucursal = ? AND estado = 'Activo'
        """, (ciudad, sucursal))
        
        nombres_db = cursor.fetchall()
        
    # <-- ¡AQUÍ CERRAMOS LA PUERTA!
    
    # Empaquetamos los nombres sacándolos de la tupla: (n,)
    lista_tomadores = [n for (n,) in nombres_db]

    return {"tomadores": lista_tomadores}
# 5. GET: Dashboard Gerencial (Estadísticas agrupadas con filtro de fecha)
@app.get("/estadisticas")
def obtener_estadisticas(fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None):
    # 1. PREPARAR FILTROS (Afuera de la base de datos)
    filtro_turnos = ""
    filtro_satisfaccion = ""
    filtro_eficiencia = ""
    filtro_muuestras = ""
    parametros = []

    if fecha_inicio and fecha_fin:
        filtro_turnos = "WHERE date(hora_registro) BETWEEN ? AND ?"
        filtro_satisfaccion = "WHERE date(fecha_hora) BETWEEN ? AND ?"
        filtro_eficiencia = "AND date(hora_registro) BETWEEN ? AND ?"
        filtro_muuestras = "WHERE date(hora_toma_muestra) BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]

    MIN_PREFERENCIAL = 30 
    MIN_NORMAL = 90

    # 2. LA MISIÓN RELÁMPAGO (Entrar, sacar datos crudos y salir)
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()

        # Turnos
        cursor.execute(f"SELECT sucursal, COUNT(*) as total, SUM(CASE WHEN estado = 'Esperando' THEN 1 ELSE 0 END) as esperando, SUM(CASE WHEN estado = 'Derivado' THEN 1 ELSE 0 END) as en_muestreo FROM turnos {filtro_turnos} GROUP BY sucursal", parametros)
        turnos_db = cursor.fetchall()

        # Satisfacción
        cursor.execute(f"SELECT sucursal, COUNT(*) as votos, AVG(puntaje) as promedio FROM satisfaccion {filtro_satisfaccion} GROUP BY sucursal", parametros)
        satisfaccion_db = cursor.fetchall()

        # Eficiencia
        cursor.execute(f"SELECT sucursal, COALESCE(AVG((julianday(hora_atencion) - julianday(hora_registro)) * 1440), 0), COALESCE(AVG((julianday(hora_registrado) - julianday(hora_atencion)) * 1440), 0), COALESCE(AVG((julianday(hora_inicio_muestra) - julianday(hora_derivado)) * 1440), 0), COALESCE(AVG((julianday(hora_toma_muestra) - julianday(hora_inicio_muestra)) * 1440), 0) FROM turnos WHERE hora_registro IS NOT NULL {filtro_eficiencia} GROUP BY sucursal", parametros)
        eficiencia_db = cursor.fetchall()

        # Alertas
        cursor.execute(f"SELECT sucursal, puntaje, comentario, date(fecha_hora) FROM satisfaccion WHERE puntaje <= 3 {filtro_satisfaccion.replace('WHERE', 'AND')} ORDER BY fecha_hora DESC LIMIT 5", parametros)
        alertas_db = cursor.fetchall()

        # Rendimiento Tomadores
        cursor.execute(f"SELECT tomador, sucursal, COUNT(id_turno), ROUND(AVG((julianday(hora_toma_muestra) - julianday(hora_inicio_muestra)) * 1440), 1) FROM turnos WHERE tomador IS NOT NULL AND hora_inicio_muestra IS NOT NULL AND hora_toma_muestra IS NOT NULL {filtro_turnos.replace('WHERE', 'AND')} GROUP BY tomador, sucursal ORDER BY 4 ASC", parametros)
        rendimiento_db = cursor.fetchall()

        # Abandono
        cursor.execute(f"SELECT sucursal, COUNT(id_turno), SUM(CASE WHEN hora_atencion IS NULL AND ((tipo_paciente IN ('Preferencial', 'Tercera Edad', 'Embarazada') AND (julianday('now', 'localtime') - julianday(hora_registro)) * 1440 > {MIN_PREFERENCIAL}) OR (tipo_paciente NOT IN ('Preferencial', 'Tercera Edad', 'Embarazada') AND (julianday('now', 'localtime') - julianday(hora_registro)) * 1440 > {MIN_NORMAL})) THEN 1 ELSE 0 END) FROM turnos {filtro_turnos} GROUP BY sucursal", parametros)
        res_abandono = cursor.fetchall()

        # Productividad
        cursor.execute(f"SELECT sucursal, COUNT(id_turno), AVG((julianday(hora_finalizado) - julianday(hora_atencion)) * 1440) FROM turnos WHERE hora_atencion IS NOT NULL AND hora_finalizado IS NOT NULL {filtro_turnos.replace('WHERE', 'AND')} GROUP BY sucursal", parametros)
        datos_box = cursor.fetchall()

        # Horas Pico
        cursor.execute(f"SELECT strftime('%H', hora_registro) as hora, COUNT(id_turno) as volumen FROM turnos WHERE hora_registro IS NOT NULL {filtro_turnos.replace('WHERE', 'AND')} GROUP BY hora ORDER BY hora ASC", parametros)
        datos_horas = cursor.fetchall()

    # <-- ¡AQUÍ SE CIERRA LA PUERTA AUTOMÁTICAMENTE! 
    # La base de datos ya está libre para que recepción siga trabajando.

    # 3. PROCESAMIENTO CON CALMA (Afuera del with)
    lista_turnos = [{"ubicacion": suc, "total": tot, "esperando": esp, "en_muestreo": mues} for suc, tot, esp, mues in turnos_db]
    lista_satisfaccion = [{"ubicacion": suc, "votos": vot, "promedio": round(prom, 1) if prom else 0} for suc, vot, prom in satisfaccion_db]
    lista_eficiencia = [{"sucursal": suc, "espera": round(esp, 1), "atencion": round(ate, 1), "espera_lab": round(esp_lab, 1), "extraccion": round(ext, 1)} for suc, esp, ate, esp_lab, ext in eficiencia_db]
    lista_alertas = [{"sucursal": suc, "estrellas": ptj, "comentario": com or "Sin comentario", "fecha": fec} for suc, ptj, com, fec in alertas_db]
    lista_rendimiento_tomadores = [{"nombre": n, "sucursal": s, "cantidad": c, "minutos": m or 0} for n, s, c, m in rendimiento_db]
    lista_abandono = [{"sucursal": s, "total": t, "abandonos": a, "porcentaje": round((a / t * 100), 1) if t > 0 else 0} for s, t, a in res_abandono]
    lista_productividad = [{"sucursal": s, "total": t, "promedio_min": round(p, 1) if p else 0} for s, t, p in datos_box]
    lista_horas_pico = [{"hora": f"{h}:00", "volumen": v} for h, v in datos_horas if h is not None]

    # 4. RETORNO DE RESULTADOS
    return {
        "turnos": lista_turnos,
        "satisfaccion": lista_satisfaccion,
        "eficiencia": lista_eficiencia,
        "alertas": lista_alertas,
        "rendimiento_tomadores": lista_rendimiento_tomadores,
        "abandono_prepago": lista_abandono,
        "productividad": lista_productividad,
        "horas_pico": lista_horas_pico
    }

