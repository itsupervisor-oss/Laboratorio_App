import sqlite3

# 1. Abrimos la conexión
conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

# 2. Simulamos los datos que llegarían de la pantalla (Capa de Presentación)
# En Python, esto entre paréntesis se llama "Tupla"
datos_paciente = ("María Gómez", "Normal", "Análisis")

# 3. Preparamos el INSERT con los signos de interrogación (?)
sql_insert = """
INSERT INTO turnos (nombre_paciente, tipo_paciente, tipo_servicio)
VALUES (?, ?, ?)
"""

# 4. Ejecutamos uniendo el SQL con los datos
cursor.execute(sql_insert, datos_paciente)

# 5. ¡El clásico COMMIT!
conexion.commit()

# Un truco genial: Python nos puede decir qué ID le asignó la base de datos
print(f"✅ Paciente registrado con éxito. Ticket/Turno ID: {cursor.lastrowid}")

# 6. Cerramos la puerta
conexion.close()