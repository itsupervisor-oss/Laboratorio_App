import sqlite3

def actualizar_base_datos_empleados_corregida():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # 1. Borramos la tabla de prueba anterior para hacerla bien desde cero
    cursor.execute("DROP TABLE IF EXISTS tomadores;")

    # 2. Creamos la nueva tabla incluyendo CIUDAD y SUCURSAL
    cursor.execute("""
        CREATE TABLE tomadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ciudad TEXT NOT NULL,
            sucursal TEXT NOT NULL,
            estado TEXT DEFAULT 'Activo'
        );
    """)
    print("✅ Tabla 'tomadores' creada correctamente con Ciudad y Sucursal.")

    # 3. Insertamos datos de prueba con la estructura correcta
    # (Basado en los logs anteriores donde vi que usabas LaPaz, SanJorge y Calacoto)
    cursor.execute("INSERT INTO tomadores (nombre, ciudad, sucursal) VALUES ('María Gómez', 'LaPaz', 'SanJorge')")
    cursor.execute("INSERT INTO tomadores (nombre, ciudad, sucursal) VALUES ('Carlos Pérez', 'LaPaz', 'SanJorge')")
    cursor.execute("INSERT INTO tomadores (nombre, ciudad, sucursal) VALUES ('Ana López', 'LaPaz', 'Calacoto')")
    cursor.execute("INSERT INTO tomadores (nombre, ciudad, sucursal) VALUES ('Mardoqueo Perka', 'SantaCruz', 'Equipetrol')")
    cursor.execute("INSERT INTO tomadores (nombre, ciudad, sucursal) VALUES ('Rocío Sanchez', 'SantaCruz', 'Equipetrol')")
    print("✅ Datos de prueba insertados.")

    # 4. Agregamos la columna 'tomador' a la tabla turnos (por si no corriste el script anterior)
    try:
        cursor.execute("ALTER TABLE turnos ADD COLUMN tomador TEXT;")
        print("✅ Columna 'tomador' agregada a los turnos.")
    except sqlite3.OperationalError:
        print("✅ La columna 'tomador' ya existía en la tabla turnos, todo en orden.")

    conexion.commit()
    conexion.close()
    print("🚀 ¡Base de datos lista para el nuevo módulo!")

actualizar_base_datos_empleados_corregida()