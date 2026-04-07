import sqlite3

conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

# Pedimos a SQLite la estructura actual de la tabla
cursor.execute("PRAGMA table_info(turnos)")
columnas = cursor.fetchall()

print("📋 Columnas encontradas en 'turnos':")
encontrada = False
for c in columnas:
    nombre_col = c
    print(f"- {nombre_col}")
    if nombre_col == "hora_toma_muestra":
        encontrada = True

if encontrada:
    print("\n✅ La columna SÍ existe en el archivo 'laboratorio.db'.")
else:
    print("\n❌ La columna NO existe.")

conexion.close()