# Sistema de Análisis y Recomendación de Anime (Arquitectura NoSQL)

[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-lightgrey)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0-green)](https://www.mongodb.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30.0-orange)](https://streamlit.io/)
[![License](https://img.shields.io/badge/licencia-MIT-brightgreen)](LICENSE)

## Tabla de contenidos

- [Resumen](#resumen)
- [Autores](#autores)
- [Fuente de datos](#fuente-de-datos)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
  - [Requisitos previos](#requisitos-previos)
  - [Entorno virtual](#entorno-virtual)
  - [Dependencias](#dependencias)
- [Ejecución](#ejecución)
  - [Iniciar MongoDB con Docker](#iniciar-mongodb-con-docker)
  - [Iniciar el backend FastAPI](#iniciar-el-backend-fastapi)
  - [Iniciar el dashboard Streamlit](#iniciar-el-dashboard-streamlit)
- [Módulos y funcionalidades](#módulos-y-funcionalidades)
- [Optimización de hardware](#optimización-de-hardware)
- [Notas de diseño](#notas-de-diseño)
- [Agradecimientos y créditos](#agradecimientos-y-créditos)

## Resumen

Este proyecto desarrolla un sistema de análisis y recomendación de anime basado en una arquitectura NoSQL. La aplicación integra una API REST construida con FastAPI, una base de datos documental MongoDB alojada localmente mediante Docker, y una interfaz de visualización interactiva con Streamlit y Plotly.

El objetivo es procesar y explorar información de perfiles, animes y reseñas, además de generar recomendaciones mediante enfoques colaborativos y de contenido, siempre priorizando el rendimiento en entornos con recursos limitados.

## Autores

- Ayala Castillo Miguel Ángel
- Calderon Calderon Michelle Monzerrat
- Estrada Miranda Marisol
- Villalba González Alejandro

## Fuente de datos

El dataset utilizado proviene de "MyAnimeList Dataset" disponible en Kaggle:

- https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews

### Descarga e Ingestión

Los datos deben descargarse manualmente desde Kaggle o mediante la API de Kaggle. Véase [data/README.md](data/README.md) para instrucciones detalladas.

Una vez descargados, los archivos CSV se procesan e ingieren automáticamente en una base de datos documental MongoDB usando el módulo `src.ingestion`. Este proceso:

- Valida integridad de archivos
- Transforma y normaliza campos (géneros, puntuaciones)
- Inserta datos en lotes para optimizar memoria
- Evita duplicados en reingestiones

## Stack tecnológico

- Python 3.11+
- FastAPI
- Uvicorn
- MongoDB
- Motor (driver asíncrono de MongoDB para Python)
- Pandas
- Scikit-learn
- Jupyter
- Python-dotenv
- Streamlit
- Plotly
- Requests
- Deep-translator
- Pydantic

Las dependencias se encuentran en `requirements.txt`.

## Arquitectura del sistema

- **Backend:** API REST con FastAPI conectada a MongoDB local mediante Docker.
- **Frontend:** Dashboard interactivo con Streamlit y visualizaciones Plotly en estilo retro/terminal.
- **Base de datos:** MongoDB con tres colecciones principales:
  - `animes`
  - `perfiles`
  - `reseñas`

## Estructura del proyecto

El repositorio contiene los siguientes componentes principales:

- `src/`: lógica de la aplicación y módulos del backend.
- `data/`: archivos CSV de entrada procesados para ingestión.
- `notebooks/`: análisis exploratorio y pruebas de datos.
- `docker-compose.yml`: configuración de MongoDB local.
- `README.md`: documentación del proyecto.

## Instalación

### Requisitos previos

- Docker y Docker Compose instalados.
- Python 3.11 o superior.
- Cuenta de usuario con permisos para ejecutar contenedores.

### Entorno virtual

Se recomienda usar un entorno virtual para aislar dependencias.

```bash
cd {tu ruta}/Proyecto_Anime_NoSQL
python -m venv venv
source venv/Scripts/activate
```

En Windows PowerShell:

```powershell
cd {tu ruta}\Proyecto_Anime_NoSQL
python -m venv venv
venv\Scripts\Activate.ps1
```

### Dependencias

Instala las dependencias desde `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Dataset (Archivos CSV)

Los archivos CSV del dataset **no están incluidos** en el repositorio por su tamaño (~675 MB). 

Consulta **[data/README.md](data/README.md)** para instrucciones completas sobre:
- Descarga desde Kaggle
- Configuración de la API de Kaggle
- Ingestión automática en MongoDB

Resumen rápido:

```bash
# Después de descargar/obtener los CSVs en data/:
docker-compose up -d
python -m src.ingestion
```

## Ejecución

### Iniciar MongoDB con Docker

La aplicación depende de un servicio MongoDB local desplegado mediante Docker Compose.

```bash
docker-compose up -d
```

Verifica que el contenedor esté en ejecución:

```bash
docker ps
```

### Iniciar el backend FastAPI

Arranca la API REST con Uvicorn:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Iniciar el dashboard Streamlit

Lanza la interfaz interactiva:

```bash
streamlit run src/dashboard.py
```

## Módulos y funcionalidades

- **Exploración y CRUD:** búsqueda de animes y visualización de metadatos a partir de la colección `animes`.
- **Analítica global:** uso de Aggregation Pipelines de MongoDB (`$unwind`, `$group`, `$match`) para obtener estadísticas agregadas en tiempo real.
- **Motor de filtrado colaborativo:** similitud del coseno y KNN con `scikit-learn` y `pandas` sobre matrices dispersas de interacciones usuario-anime.
- **Motor de recomendación por contenido (NLP):** traducción de prompts en tiempo real con `deep-translator` al inglés y vectorización TF-IDF de sinopsis, combinada con filtrado previo por año y género desde MongoDB.

## Optimización de hardware

El proyecto está diseñado para ejecutarse en equipos con recursos limitados. Entre las optimizaciones incluidas están:

- Recolección de basura manual con `gc.collect()` en puntos críticos.
- Límites estrictos en el vocabulario de TF-IDF para reducir memoria y tamaño de matrices dispersas.
- Proyecciones NoSQL en consultas MongoDB para transferir solo los campos necesarios.
- Control cuidadoso de las operaciones en memoria para evitar la paginación de Windows (swap) y proteger el almacenamiento SSD en equipos con pocos recursos disponibles.

## Notas de diseño

- La base de datos documenta la relación entre animes, perfiles y reseñas sin esquemas rígidos.
- El uso de MongoDB permite ejecutar análisis agregados sin necesidad de cargas complejas en el servidor.
- El dashboard retro/terminal prioriza la claridad de métricas y la experiencia de exploración.
- El uso de Docker para MongoDB facilita la reproducibilidad del entorno local.

## Créditos

Se reconoce el dataset original de MyAnimeList y la comunidad de Kaggle por facilitar los datos y la investigación.
