import sqlite3

def migrar():
    # Nos conectamos a la base de datos existente
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()
    
    # Lista de columnas que queremos añadir para el nuevo flujo
    nuevas_columnas = [
        ("hora_derivado", "TEXT"),
        ("hora_finalizado", "TEXT"),
        ("fecha_hora", "TEXT") # Por si acaso satisfaccion no la tiene
    ]
    
    print("🚀 Iniciando migración de la base de datos...")
    
    # 1. ACTUALIZACIÓN DE LA TABLA 'turnos'
    for nombre_col, tipo in nuevas_columnas[:2]:
        try:
            cursor.execute(f"ALTER TABLE turnos ADD COLUMN {nombre_col} {tipo}")
            print(f"✅ Columna '{nombre_col}' añadida a la tabla 'turnos'.")
        except sqlite3.OperationalError:
            print(f"ℹ️ La columna '{nombre_col}' ya existe en 'turnos', saltando...")

    # 2. ACTUALIZACIÓN DE LA TABLA 'satisfaccion'
    try:
        cursor.execute("ALTER TABLE satisfaccion ADD COLUMN fecha_hora TEXT")
        print("✅ Columna 'fecha_hora' añadida a 'satisfaccion'.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna 'fecha_hora' ya existe en 'satisfaccion', saltando...")

    conexion.commit()
    conexion.close()
    print("🏁 Migración completada con éxito.")

if __name__ == "__main__":
    migrar()