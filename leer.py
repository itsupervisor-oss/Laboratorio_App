import sqlite3

# 1. Abrimos la conexión
conexion = sqlite3.connect("laboratorio.db")
cursor = conexion.cursor()

# 2. Tu consulta SQL clásica
sql_select = "SELECT id_turno, nombre_paciente, tipo_paciente, tipo_servicio, estado FROM turnos"

# 3. Ejecutamos la consulta
cursor.execute(sql_select)

# 4. Hacemos el FETCH de todos los datos
# fetchall() nos devuelve una lista con todos los registros encontrados
registros = cursor.fetchall()

print("--- LISTA DE TURNOS EN EL LABORATORIO ---")

# 5. El Bucle (Loop): Recorremos fila por fila
# En Python, las filas llegan como "Tuplas" (grupos de datos), y accedemos a ellos por su posición: 0, 1, 2...
for fila in registros:
    id_turno = fila[0]
    nombre = fila[1]
    tipo_paciente = fila[2]
    servicio = fila[3]
    estado = fila[4]
    
    # Imprimimos dándole un formato bonito. 
    # La 'f' antes de las comillas nos permite meter variables entre llaves {}
    print(f"Turno #{id_turno} | Paciente: {nombre} ({tipo_paciente}) | Va a: {servicio} | Estado: {estado}")

# 6. Cerramos la conexión
conexion.close()