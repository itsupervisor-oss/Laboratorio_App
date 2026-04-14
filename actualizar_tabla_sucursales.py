import sqlite3

def agregar_estado_a_sucursales():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    try:
        # 1. Intentamos agregar la columna 'estado'
        # Usamos DEFAULT 'Activo' para que las que ya existen no queden vacías
        cursor.execute("ALTER TABLE sucursales ADD COLUMN estado TEXT DEFAULT 'Activo'")
        print("✅ Columna 'estado' agregada con éxito.")
    except sqlite3.OperationalError:
        # Si ya existía (por si acaso volviste a correr el script), no dará error
        print("⚠️ La columna 'estado' ya existe o hubo un problema.")

    # 2. Por seguridad, nos aseguramos de que todas las actuales digan 'Activo'
    cursor.execute("UPDATE sucursales SET estado = 'Activo' WHERE estado IS NULL")
    
    conexion.commit()
    conexion.close()
    print("🚀 Base de datos actualizada: Las sucursales ahora tienen control de estado.")

agregar_estado_a_sucursales()