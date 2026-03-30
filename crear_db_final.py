import sqlite3

# 1. Nos conectamos (o creamos) la base de datos
conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

print("🧹 Limpiando base de datos antigua...")
cursor.execute("DROP TABLE IF EXISTS turnos")
cursor.execute("DROP TABLE IF EXISTS satisfaccion")

print("🏗️ Creando estructura definitiva...")

# 2. Creamos la tabla de TURNOS (Con todos los tiempos en formato texto para que Python los controle)
cursor.execute("""
CREATE TABLE turnos (
    id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad TEXT NOT NULL,
    sucursal TEXT NOT NULL,
    nombre_paciente TEXT NOT NULL,
    tipo_paciente TEXT,
    tipo_servicio TEXT,
    hora_registro TEXT,   -- Guardado por Python al sacar ticket
    hora_atencion TEXT,   -- Guardado por Python al Llamar
    hora_registrado TEXT, -- Guardado por Python al terminar (botón morado)
    estado TEXT DEFAULT 'Esperando'
)
""")

# 3. Creamos la tabla de SATISFACCIÓN (Con comentarios y sucursales)
cursor.execute("""
CREATE TABLE satisfaccion (
    id_voto INTEGER PRIMARY KEY AUTOINCREMENT,
    ciudad TEXT NOT NULL,
    sucursal TEXT NOT NULL,
    puntaje INTEGER NOT NULL,
    comentario TEXT,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# 4. Guardamos y cerramos
conexion.commit()
conexion.close()

print("✅ ¡Base de datos 'laboratorio.db' recreada con éxito! Está lista y reluciente.")