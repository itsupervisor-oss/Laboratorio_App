import sqlite3

# 1. Nos conectamos a nuestra base de datos
conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

print("Actualizando el modelo de datos...")

# 2. Eliminamos la tabla vieja de satisfacción (¡Adiós a los campos de referencia!)
cursor.execute("DROP TABLE IF EXISTS satisfaccion")

# 3. Creamos la NUEVA tabla de satisfacción, totalmente desacoplada
cursor.execute("""
CREATE TABLE satisfaccion (
    id_voto INTEGER PRIMARY KEY AUTOINCREMENT,
    puntaje INTEGER NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
    -- ¡Ya no hay tipo_paciente_ref ni tipo_servicio_ref!
)
""")

# 4. Guardamos los cambios
conexion.commit()
conexion.close()

print("✅ Tabla 'satisfaccion' recreada con éxito. ¡Lista para el kiosco anónimo!")