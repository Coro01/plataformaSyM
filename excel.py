import pandas as pd
import sqlite3
import os
import datetime

# ==========================================================
# 🛑🛑🛑 CONFIGURACIÓN DE VARIABLES 🛑🛑🛑
# ==========================================================
archivo_excel = 'PRODUCTOS.xlsx'
nombre_bd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
nombre_tabla = 'Inventario'
# ==========================================================

# Campos numéricos con 'null=False' en la BD
COLUMNAS_NUMERICAS_REQUERIDAS = [
    'Cantidad',
    'MinimoAdmisible',
    'MaximoAdmisible',
    'PrecioGS',
    'PrecioUSD',
    'PrecioTotalGS'
]

# Campo de fecha con 'null=False' en la BD
NOMBRE_CAMPO_FECHA = 'FechaUltimoMovimiento' 

# Unimos todas las columnas que requieren tratamiento de NULOS
COLUMNAS_QUE_NO_PUEDEN_SER_NULAS = COLUMNAS_NUMERICAS_REQUERIDAS + [NOMBRE_CAMPO_FECHA]


try:
    print(f"Iniciando la lectura del archivo: {archivo_excel}...")

    # 1. Lectura del archivo Excel
    # Añadimos 'keep_default_na=False' para tratar celdas vacías como '' en lugar de NaN
    df = pd.read_excel(archivo_excel, keep_default_na=False)

    # 2. Limpieza de nombres de columna
    df.columns = df.columns.str.replace('[^A-Za-z0-9_]+', '', regex=True).str.replace(' ', '_', regex=False)
    print("✅ Nombres de columnas limpiados.")
    
    # 2.5. CRÍTICO: Eliminación de filas duplicadas
    print("🗑️ Eliminando filas duplicadas en CodigoProducto...")
    df.drop_duplicates(subset=['CodigoProducto'], keep='first', inplace=True)
    
    # 2.6. 🛑 NUEVA SOLUCIÓN PARA EL ERROR DE CodigoProducto
    # Eliminamos filas donde CodigoProducto sea nulo (NaN) o una cadena vacía ('')
    print("🗑️ Limpiando filas con CodigoProducto nulo/vacío...")
    
    # Convierte cadenas vacías a NaN para tratarlas
    df['CodigoProducto'] = df['CodigoProducto'].replace('', pd.NA)
    
    # Elimina filas donde CodigoProducto es NaN
    df.dropna(subset=['CodigoProducto'], inplace=True)
    
    # Convierte el CodigoProducto de vuelta a string (VARCHAR)
    df['CodigoProducto'] = df['CodigoProducto'].astype(str)

    print(f"✅ Duplicados y nulos/vacíos en CodigoProducto eliminados. Filas restantes: {len(df)}")


    # 3. Tratamiento de Valores Nulos en columnas obligatorias
    print("🔄 Rellenando valores nulos en columnas obligatorias...")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    for col in COLUMNAS_QUE_NO_PUEDEN_SER_NULAS:
        if col not in df.columns:
            print(f"   ⚠️ ADVERTENCIA CRÍTICA: Columna requerida '{col}' no encontrada en el Excel.")
            continue

        if col == NOMBRE_CAMPO_FECHA:
            # Rellena los nulos en la columna de fecha con la hora actual UTC
            df[col] = df[col].fillna(now_utc)
            print(f"   -> Columna '{col}' rellenada con la hora actual UTC **por defecto**.")
        
        elif col in COLUMNAS_NUMERICAS_REQUERIDAS:
            # Rellena los nulos en columnas numéricas con 0 y fuerza el tipo
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) 
            print(f"   -> Columna '{col}' rellenada con 0 si contenía nulos/texto.")

    print("✅ Datos preparados para la inserción.")

    # 4. Conexión a la Base de Datos SQLite3
    conn = sqlite3.connect(nombre_bd)

    # 5. Escribir el DataFrame en la base de datos
    df.to_sql(nombre_tabla, conn, if_exists='append', index=False)

    # 6. Cierra la Conexión
    conn.close()

    print("\n=============================================")
    print("🚀 ¡PROCESO TERMINADO CON ÉXITO! 🚀")
    print(f"Los datos de {archivo_excel} fueron *añadidos* a la tabla: **{nombre_tabla}**")
    print("=============================================")

except FileNotFoundError:
    print(f"\n❌ ERROR: El archivo '{archivo_excel}' no se encontró.")
    print("Por favor, verifica el nombre del archivo o su ubicación.")
except Exception as e:
    print(f"\n❌ Ocurrió un error inesperado durante la inserción: {e}")
    print("\n**ÚLTIMA VERIFICACIÓN:** Confirma la existencia y el nombre correcto de la columna **CodigoProducto** en tu archivo Excel.")