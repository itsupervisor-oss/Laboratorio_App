import sqlite3

# 1. Conexión: Si el archivo no existe, Python lo crea automáticamente.
conexion = sqlite3.connect("laboratorio.db")

# 2. Cursor: Es como tu consola de comandos en Oracle para ejecutar sentencias.
cursor = conexion.cursor()

# 3. Tu especialidad: ¡Código SQL puro!
# Creamos la tabla de Turnos
cursor.execute("""
CREATE TABLE IF NOT EXISTS turnos (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_paciente TEXT NOT NULL,
    tipo_paciente TEXT,
    tipo_servicio TEXT,
    hora_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    hora_atencion DATETIME,
    estado TEXT DEFAULT 'Esperando'
)
""")

# Creamos la tabla de Satisfacción (Anónima)
cursor.execute("""
CREATE TABLE IF NOT EXISTS satisfaccion (
    id_voto INTEGER PRIMARY KEY AUTOINCREMENT,
    puntaje INTEGER NOT NULL,
    tipo_paciente_ref TEXT,
    tipo_servicio_ref TEXT,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 4. Guardamos los cambios (El clásico COMMIT transaccional)
conexion.commit()

# 5. Cerramos la conexión
conexion.close()

print("¡Base de datos 'laboratorio.db' y tablas creadas con éxito! Bienvenido a Python.")