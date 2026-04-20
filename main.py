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


# 1. Creamos un "molde" para los datos del nuevo empleado
class NuevoEmpleado(BaseModel):
    nombre: str
    ciudad: str
    sucursal: str
# 2. Ruta para ver a TODOS los empleados (activos e inactivos)
@app.get("/admin/empleados")
def obtener_todos_empleados():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, ciudad, sucursal, estado FROM tomadores")
    datos = cursor.fetchall()
    conexion.close()
    
    lista = [{"id": i, "nombre": n, "ciudad": c, "sucursal": s, "estado": e} for i, n, c, s, e in datos]

    return {"empleados": lista}

# 3. Ruta para agregar un empleado nuevo
@app.post("/admin/empleados")
def agregar_empleado(empleado: NuevoEmpleado):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO tomadores (nombre, ciudad, sucursal, estado) 
        VALUES (?, ?, ?, 'Activo')
    """, (empleado.nombre, empleado.ciudad, empleado.sucursal))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Empleado registrado exitosamente"}

# 4. Ruta para activar o desactivar un empleado
@app.put("/admin/empleados/{id_empleado}/estado")
def cambiar_estado_empleado(id_empleado: int, estado: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("UPDATE tomadores SET estado = ? WHERE id = ?", (estado, id_empleado))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Estado cambiado a {estado}"}

@app.put("/admin/empleados/{id_empleado}/reasignar")
def reasignar_empleado(id_empleado: int, datos: dict):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    # Actualizamos ciudad y sucursal al mismo tiempo
    cursor.execute(
        "UPDATE tomadores SET ciudad = ?, sucursal = ? WHERE id = ?",
        (datos['ciudad'], datos['sucursal'], id_empleado)
    )
    conexion.commit()
    conexion.close()
    return {"mensaje": "Empleado reasignado con éxito"}

# ---------------------------------------------------------
# RUTAS PARA LOS COMBOS DEPENDIENTES (CIUDAD Y SUCURSAL)
# ---------------------------------------------------------

# 1. Obtener lista de ciudades únicas
@app.get("/ciudades")
def obtener_ciudades():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    # Usamos DISTINCT para que no nos repita "LaPaz" tres veces
    cursor.execute("SELECT DISTINCT ciudad FROM sucursales")
    datos = cursor.fetchall()
    conexion.close()
    
    # Extraemos el texto de la tupla (usamos d para evitar el error de hace rato 😉)
    lista_ciudades = [c for (c,) in datos]
    return {"ciudades": lista_ciudades}

# 2. Obtener sucursales según la ciudad seleccionada
@app.get("/sucursales/{ciudad}")
def obtener_sucursales(ciudad: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    # Buscamos solo las sucursales que pertenecen a la ciudad que nos mandan
    cursor.execute("SELECT nombre_sucursal FROM sucursales WHERE ciudad = ? AND estado = 'Activo'", (ciudad,))
    datos = cursor.fetchall()
    conexion.close()
    
    lista_sucursales = [s for (s,) in datos]
    return {"sucursales": lista_sucursales}


# --- RUTAS PARA GESTIONAR EL DIRECTORIO DE SUCURSALES ---

# 1. Obtener TODAS las sucursales (para la tabla de administración)
@app.get("/admin/sucursales")
def obtener_todas_sucursales():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT id, ciudad, nombre_sucursal, estado FROM sucursales")
    datos = cursor.fetchall()
    conexion.close()
    # Usamos el desempacado seguro para evitar errores de formato
    lista = [{"id": i, "ciudad": c, "nombre": n, "estado": e} for i, c, n, e in datos]
    return {"sucursales": lista}

# 2. Crear una nueva sucursal (POST)
@app.post("/admin/sucursales")
def crear_sucursal(datos: dict):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "INSERT INTO sucursales (ciudad, nombre_sucursal, estado) VALUES (?, ?, 'Activo')",
            (datos['ciudad'], datos['nombre'])
        )
        conexion.commit()
        return {"mensaje": "Sucursal creada con éxito"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conexion.close()

# 3. Cambiar estado de una sucursal (PUT)
@app.put("/admin/sucursales/{id}/estado")
def cambiar_estado_sucursal(id: int, estado: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("UPDATE sucursales SET estado = ? WHERE id = ?", (estado, id))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Sucursal actualizada a {estado}"}
#--------------------------------------------------------
#--------------------------------------------------------

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


from typing import Optional # 👈 Asegúrate de que esta línea esté al inicio de tu archivo

@app.put("/turnos/{id_turno}")
def actualizar_estado(id_turno: int, nuevo_estado: str, tomador: Optional[str] = None): # 👈 Añadimos tomador aquí
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # Capturamos la hora exacta en el momento del clic
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    conexion.close()
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

@app.get("/tomadores")
def obtener_tomadores(ciudad: str, sucursal: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # Buscamos solo los empleados activos de esa sucursal específica
    cursor.execute("""
        SELECT nombre 
        FROM tomadores 
        WHERE ciudad = ? AND sucursal = ? AND estado = 'Activo'
    """, (ciudad, sucursal))
    
    # Empaquetamos los nombres en una lista
    nombres_db = cursor.fetchall()
    lista_tomadores = [fila for fila in nombres_db]

    conexion.close()
    return {"tomadores": lista_tomadores}

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
    lista_rendimiento_tomadores = [] # 👈 Inicializamos el nuevo ranking
    
    filtro_turnos = ""
    filtro_satisfaccion = ""
    filtro_eficiencia = ""
    parametros = []
    filtro_muuestras = "" # 👈 Nuevo filtro

    # 2. CONFIGURAR FILTROS DE FECHA
    if fecha_inicio and fecha_fin:
        filtro_turnos = "WHERE date(hora_registro) BETWEEN ? AND ?"
        filtro_satisfaccion = "WHERE date(fecha_hora) BETWEEN ? AND ?"
        filtro_eficiencia = "AND date(hora_registro) BETWEEN ? AND ?"
        filtro_muuestras = "WHERE date(hora_toma_muestra) BETWEEN ? AND ?" # 👈 Para la tabla de muestras
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
    lista_alertas = [
        {"sucursal": suc, "estrellas": puntaje, "comentario": coment or "Sin comentario", "fecha": fecha} 
        for suc, puntaje, coment, fecha in alertas_db
    ]

    # 6.5 RANKING DE RAPIDEZ DE TOMADORES (Consulta Limpia)
    cursor.execute(f"""
        SELECT 
            tomador, 
            sucursal,
            COUNT(id_turno) as total_muestras,
            ROUND(AVG((julianday(hora_toma_muestra) - julianday(hora_inicio_muestra)) * 1440), 1) as promedio_min
        FROM turnos
        WHERE tomador IS NOT NULL 
          AND hora_inicio_muestra IS NOT NULL 
          AND hora_toma_muestra IS NOT NULL
          {filtro_turnos.replace("WHERE", "AND")} 
        GROUP BY tomador, sucursal
        ORDER BY promedio_min ASC
    """, parametros)
    rendimiento_db = cursor.fetchall()
    
    lista_rendimiento_tomadores = [
        {"nombre": n, "sucursal": s, "cantidad": c, "minutos": m or 0} 
        for n, s, c, m in rendimiento_db
    ]

    # --- LÓGICA DE ABANDONO PRE-PAGO ---
# Definimos los minutos límite directamente aquí para que sea claro
    MIN_PREFERENCIAL = 30 
    MIN_NORMAL = 90

    # Consulta para detectar pacientes que sacaron ticket pero no llegaron a ventanilla
    cursor.execute(f"""
        SELECT 
            sucursal,
            COUNT(id_turno) as total_tickets,
            SUM(CASE 
                WHEN hora_atencion IS NULL AND (
                    -- Caso A: Paciente Preferencial que esperó más de {MIN_PREFERENCIAL} min
                    (tipo_paciente IN ('Preferencial', 'Tercera Edad', 'Embarazada') 
                    AND (julianday('now', 'localtime') - julianday(hora_registro)) * 1440 > {MIN_PREFERENCIAL})
                    
                    OR 
                    
                    -- Caso B: Paciente Normal que esperó más de {MIN_NORMAL} min
                    (tipo_paciente NOT IN ('Preferencial', 'Tercera Edad', 'Embarazada') 
                    AND (julianday('now', 'localtime') - julianday(hora_registro)) * 1440 > {MIN_NORMAL})
                ) THEN 1 ELSE 0 END) as abandonos_estimados
        FROM turnos
        {filtro_turnos}
        GROUP BY sucursal
    """, parametros)

    res_abandono = cursor.fetchall()
    lista_abandono = [
        {
            "sucursal": s, 
            "total": t, 
            "abandonos": a, 
            "porcentaje": round((a / t * 100), 1) if t > 0 else 0
        } for s, t, a in res_abandono
    ]

    # --- MÉTRICA: PRODUCTIVIDAD DE BOXES ---
    cursor.execute(f"""
        SELECT 
            sucursal,
            COUNT(id_turno) as total_muestras,
            AVG((julianday(hora_finalizado) - julianday(hora_atencion)) * 1440) as tiempo_promedio_box
        FROM turnos
        WHERE hora_atencion IS NOT NULL AND hora_finalizado IS NOT NULL
        {filtro_turnos.replace("WHERE", "AND")}
        GROUP BY sucursal
    """, parametros)
    datos_box = cursor.fetchall()

    lista_productividad = [
        {
            "sucursal": s, 
            "total": t, 
            "promedio_min": round(p, 1) if p else 0
        } for s, t, p in datos_box
    ]

    # --- MÉTRICA: HORAS PICO (Afluencia de pacientes) ---
    cursor.execute(f"""
        SELECT 
            strftime('%H', hora_registro) as hora,
            COUNT(id_turno) as volumen
        FROM turnos
        WHERE hora_registro IS NOT NULL
        {filtro_turnos.replace("WHERE", "AND")}
        GROUP BY hora
        ORDER BY hora ASC
    """, parametros)
    datos_horas = cursor.fetchall()

    # Formateamos para que se lea bonito (ej: "07:00")
    lista_horas_pico = [
        {"hora": f"{h}:00", "volumen": v} 
        for h, v in datos_horas if h is not None
    ]

    conexion.close()
    # print("🚀 ESTOY LLEGANDO AL RETURN Y ESTAS SON LAS HORAS:", lista_horas_pico)
    # 7. RETORNO DE RESULTADOS (El gran paquete de datos)
    return {
        "turnos": lista_turnos,
        "satisfaccion": lista_satisfaccion,
        "eficiencia": lista_eficiencia,
        "alertas": lista_alertas,
        "rendimiento_tomadores": lista_rendimiento_tomadores,
        "abandono_prepago": lista_abandono,  # <--- Recién agregada
        "productividad": lista_productividad,  # <--- Recién agregada
        "horas_pico": lista_horas_pico  # <--- Recién agregada
    }

