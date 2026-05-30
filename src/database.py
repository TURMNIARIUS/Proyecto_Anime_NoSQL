"""Conexión y acceso a la base de datos MongoDB.

Este módulo centraliza la creación del cliente MongoDB usando las
variables de entorno (`MONGO_URI`, `DATABASE_NAME`). Proporciona la
función `get_db()` para obtener el handle a la base de datos.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DATABASE_NAME", "myanimelist_db")


def get_db():
    """Crea (o reutiliza) un cliente MongoDB y devuelve la base de datos.

    Retorna:
        Objeto de base de datos (`pymongo.database.Database`) configurado
        según la variable `DB_NAME`.
    """
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]
