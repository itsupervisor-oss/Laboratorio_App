import sqlite3

def actualizar_base_datos():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    try:
        # Agregamos la nueva columna a la tabla existente
        cursor.execute("ALTER TABLE turnos ADD COLUMN hora_inicio_muestra DATETIME;")
        print("✅ ¡Éxito! Columna 'hora_inicio_muestra' agregada correctamente.")
    except sqlite3.OperationalError as e:
        # Si corres el script dos veces por error, no pasa nada, te avisa esto:
        print(f"⚠️ Aviso: {e} (La columna ya existe).")

    conexion.commit()
    conexion.close()

actualizar_base_datos()