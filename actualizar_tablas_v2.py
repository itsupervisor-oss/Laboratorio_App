import sqlite3

conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

print("Actualizando el modelo de datos para Multi-Sucursal...")

# 1. Eliminamos las tablas viejas
cursor.execute("DROP TABLE IF EXISTS turnos")
cursor.execute("DROP TABLE IF EXISTS satisfaccion")

# 2. Creamos la nueva tabla de TURNOS con Ciudad y Sucursal
cursor.execute("""
CREATE TABLE turnos (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad TEXT NOT NULL,
    sucursal TEXT NOT NULL,
    nombre_paciente TEXT NOT NULL,
    tipo_paciente TEXT,
    tipo_servicio TEXT,
    hora_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    hora_atencion DATETIME,
    estado TEXT DEFAULT 'Esperando'
)
""")

# 3. Creamos la nueva tabla de SATISFACCIÓN con Ciudad y Sucursal
cursor.execute("""
CREATE TABLE satisfaccion (
    id_voto INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad TEXT NOT NULL,
    sucursal TEXT NOT NULL,
    puntaje INTEGER NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conexion.commit()
conexion.close()

print("✅ Base de datos actualizada. ¡Lista para implementarse en múltiples ciudades y sucursales!")