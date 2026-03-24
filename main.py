from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# --- RUTAS WEB ---

@app.get("/turnos")
def obtener_turnos(ciudad: str, sucursal: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # 1. Hacemos el SELECT pidiendo exactamente las 4 columnas que necesitamos
    cursor.execute("""
        SELECT id_turno, nombre_paciente, tipo_servicio, estado 
        FROM turnos 
        WHERE ciudad = ? AND sucursal = ?
        ORDER BY id_turno DESC
    """, (ciudad, sucursal))
    
    turnos = cursor.fetchall()
    conexion.close()
    
    # 2. LA MAGIA: Convertimos la fila cruda de SQL en un paquete con etiquetas
    # t es id_turno, t es nombre, t es servicio, t es estado
    lista_formateada = [
        {"id": t[0], "paciente": t[1], "servicio": t[2], "estado": t[3]} 
        for t in turnos
    ]
    
    return lista_formateada

@app.post("/turnos")
def registrar_paciente(turno: NuevoTurno):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # Insertamos los 5 campos
    cursor.execute("""
        INSERT INTO turnos (ciudad, sucursal, nombre_paciente, tipo_paciente, tipo_servicio) 
        VALUES (?, ?, ?, ?, ?)
    """, (turno.ciudad, turno.sucursal, turno.nombre_paciente, turno.tipo_paciente, turno.tipo_servicio))
    
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return {"mensaje": "¡Paciente registrado exitosamente!", "ticket": nuevo_id}

@app.put("/turnos/{id_turno}")
def atender_paciente(id_turno: int):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    cursor.execute("UPDATE turnos SET estado = 'Finalizado', hora_atencion = CURRENT_TIMESTAMP WHERE id_turno = ?", (id_turno,))
    conexion.commit()
    conexion.close()
    return {"mensaje": f"Turno #{id_turno} marcado como Finalizado."}

@app.post("/votar")
def registrar_voto(voto: Voto):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # Insertamos los 3 campos
    cursor.execute("INSERT INTO satisfaccion (ciudad, sucursal, puntaje) VALUES (?, ?, ?)", (voto.ciudad, voto.sucursal, voto.puntaje))
    
    conexion.commit()
    conexion.close()
    return {"mensaje": "¡Voto registrado con éxito!", "puntaje": voto.puntaje}

# NUEVO PUT: Ahora recibe si queremos "Llamar" o "Atender" al paciente
@app.put("/turnos/{id_turno}")
def actualizar_estado_turno(id_turno: int, nuevo_estado: str):
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # Si lo estamos finalizando, le ponemos la hora de atención. Si solo estamos llamando, solo cambiamos el estado.
    if nuevo_estado == 'Finalizado':
        cursor.execute("UPDATE turnos SET estado = ?, hora_atencion = CURRENT_TIMESTAMP WHERE id_turno = ?", (nuevo_estado, id_turno))
    else:
        cursor.execute("UPDATE turnos SET estado = ? WHERE id_turno = ?", (nuevo_estado, id_turno))
        
    conexion.commit()
    conexion.close()
    
    return {"mensaje": f"Turno #{id_turno} actualizado a {nuevo_estado}."}

# 5. GET: Dashboard Gerencial (Estadísticas agrupadas)
@app.get("/estadisticas")
def obtener_estadisticas():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # Consulta 1: Total de pacientes y cuántos siguen esperando por Sucursal
    cursor.execute("""
        SELECT ciudad || ' - ' || sucursal AS ubicacion, 
               COUNT(id_turno) as total_pacientes,
               SUM(CASE WHEN estado = 'Esperando' THEN 1 ELSE 0 END) as en_espera
        FROM turnos
        GROUP BY ciudad, sucursal
    """)
    turnos_stats = cursor.fetchall()
    
    # Consulta 2: Promedio de satisfacción por Sucursal
    cursor.execute("""
        SELECT ciudad || ' - ' || sucursal AS ubicacion, 
               AVG(puntaje) as promedio_satisfaccion,
               COUNT(id_voto) as total_votos
        FROM satisfaccion
        GROUP BY ciudad, sucursal
    """)
    votos_stats = cursor.fetchall()
    conexion.close()
    
    # Formateamos ambas listas
    lista_turnos = [{"ubicacion": t[0], "total": t[1], "esperando": t[2]} for t in turnos_stats]
    
    # Usamos round(v, 1) para que el promedio tenga solo 1 decimal (ej. 4.5)
    lista_votos = [{"ubicacion": v[0], "promedio": round(v[1], 1) if v[1] else 0, "votos": v[2]} for v in votos_stats]
    
    return {"turnos": lista_turnos, "satisfaccion": lista_votos}