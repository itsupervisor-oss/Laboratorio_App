# Dentro de tu script de migración, añade esta columna
import sqlite3

def agregar_columna_seguro():
    try:
        conexion = sqlite3.connect("laboratorio.db") #
        cursor = conexion.cursor()
        
        # Intentamos agregar la columna
        cursor.execute("ALTER TABLE turnos ADD COLUMN hora_toma_muestra TEXT")
        
        conexion.commit()
        print("✅ ¡Éxito! Columna 'hora_toma_muestra' añadida correctamente.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Confirmado: La columna ya existe.")
        else:
            print(f"❌ Error de SQLite: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    agregar_columna_seguro()