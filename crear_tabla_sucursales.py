import sqlite3

def actualizar_base_datos_sucursales():
    conexion = sqlite3.connect("laboratorio.db")
    cursor = conexion.cursor()

    # 1. Creamos la nueva tabla para las sucursales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sucursales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciudad TEXT NOT NULL,
            nombre_sucursal TEXT NOT NULL
        );
    """)
    print("✅ Tabla 'sucursales' creada correctamente.")

    # 2. Limpiamos la tabla por si ya tenía datos de una prueba anterior
    cursor.execute("DELETE FROM sucursales")

    # 3. Insertamos el directorio oficial de la clínica
    # Ciudades y sus sucursales correspondientes
    datos_oficiales = [
        ('LaPaz', 'SanJorge'),
        ('LaPaz', 'Calacoto'),
        ('SantaCruz', 'Centro'),
        ('SantaCruz', 'Equipetrol'),
        ('SantaCruz', 'Norte'),
        ('Cochabamba', 'Prado'),
        ('Cochabamba', 'CalaCala')
    ]

    cursor.executemany("""
        INSERT INTO sucursales (ciudad, nombre_sucursal) 
        VALUES (?, ?)
    """, datos_oficiales)
    
    print(f"✅ {len(datos_oficiales)} sucursales registradas con éxito en el directorio.")

    conexion.commit()
    conexion.close()
    print("🚀 ¡Base de datos lista para los combos dependientes!")

actualizar_base_datos_sucursales()