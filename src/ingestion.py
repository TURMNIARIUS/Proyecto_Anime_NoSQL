"""Módulo de ingestión ETL para cargar CSVs a MongoDB.

Contiene utilidades para limpiar campos específicos (por ejemplo,
géneros) y funciones para insertar datos en lotes para evitar
consumir demasiada memoria en procesos masivos.
"""

import pandas as pd
from database import get_db
import ast
import os

db = get_db()

def limpiar_genero(val):
    """Normaliza el campo `genre` leído desde CSV.

    Parámetros:
        val: valor leído desde el CSV (usualmente una cadena que
             representa una lista, p.ej. "['Action', 'Drama']").

    Devuelve:
        Lista de géneros (lista Python). En caso de error retorna lista vacía.
    """
    try:
        if isinstance(val, str) and val.startswith('['):
            # ast.literal_eval convierte "['Action', 'Drama']" en ['Action', 'Drama']
            return ast.literal_eval(val)
        return []
    except Exception:
        return []

def ingresar_csv_en_lotes(ruta_csv, nombre_coleccion, volumen_lote=10000):
    """Inserta un CSV en la colección indicada en MongoDB por lotes.

    Args:
        ruta_csv: ruta al archivo CSV de entrada.
        nombre_coleccion: nombre de la colección destino en MongoDB.
        volumen_lote: número de filas por lote (chunksize) para insert_many.

    La función valida existencia del archivo y evita reingestar si la
    colección ya contiene documentos.
    """
    print(f"Iniciando importación de {ruta_csv} en '{nombre_coleccion}'...")

    if not os.path.exists(ruta_csv):
        print(f"Error: No se encontró el archivo en {ruta_csv}")
        return

    coleccion = db[nombre_coleccion]
    if coleccion.count_documents({}) > 0:
        print(f"La colección '{nombre_coleccion}' ya tiene datos. Saltando.")
        return

    total_insertado = 0
    for chunk in pd.read_csv(ruta_csv, chunksize=volumen_lote):

        # PROCESO DE LIMPIEZA ETL SOLO PARA ANIMES
        if nombre_coleccion == "animes":
            # 1. Asegurar que score sea un número flotante (si hay error, lo pone como NaN y luego 0)
            chunk['score'] = pd.to_numeric(chunk['score'], errors='coerce').fillna(0)

            # 2. Transformar el string de géneros a un Arreglo real
            chunk['genre'] = chunk['genre'].apply(limpiar_genero)

        registros = chunk.to_dict(orient="records")

        if registros:
            coleccion.insert_many(registros)
            total_insertado += len(registros)
            print(f"Insertados {total_insertado} registros...")

    print(f"¡Éxito! Total de documentos en '{nombre_coleccion}': {total_insertado}\n")

if __name__ == "__main__":
    # Punto de entrada para ejecución directa del módulo de ingestión.
    ingresar_csv_en_lotes("data/animes.csv", "animes")
    ingresar_csv_en_lotes("data/profiles.csv", "usuarios")
    ingresar_csv_en_lotes("data/reviews.csv", "reseñas")
