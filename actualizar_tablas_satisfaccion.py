import sqlite3

conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

# Agregamos la columna para guardar el comentario
cursor.execute("ALTER TABLE satisfaccion ADD COLUMN comentario TEXT")

conexion.commit()
conexion.close()
print("¡Columna comentario agregada con éxito!")