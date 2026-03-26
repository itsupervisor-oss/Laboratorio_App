import sqlite3

conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

# Agregamos la nueva columna para guardar la fecha y hora
cursor.execute("ALTER TABLE turnos ADD COLUMN hora_registrado TEXT")

conexion.commit()
conexion.close()
print("¡Columna agregada con éxito!")