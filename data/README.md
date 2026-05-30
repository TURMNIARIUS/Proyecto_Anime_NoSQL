# Datos del Proyecto

Este directorio debe contener los archivos CSV que alimentan la aplicación.

## Obtención del Dataset

El dataset completo proviene de **MyAnimeList Dataset** en Kaggle:

https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews

### Archivos Requeridos

El proyecto espera los siguientes archivos CSV en este directorio:

1. **`animes.csv`** (~12 MB)
   - Información sobre animes: títulos, géneros, sinopsis, puntuaciones, etc.

2. **`profiles.csv`** (~8.3 MB)
   - Perfiles de usuarios que han reseñado animes.

3. **`reviews.csv`** (~655 MB)
   - Reseñas de usuarios: puntuaciones y comentarios sobre animes.

## Descarga e Instalación

### Opción 1: Descarga Manual desde Kaggle

1. Accede a https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews
2. Descarga los archivos CSV
3. Colócalos en este directorio (`data/`)

### Opción 2: Usando la API de Kaggle (Recomendado)

Si tienes la CLI de Kaggle instalada:

```bash
# Instalar kaggle-cli
pip install kaggle

# Configurar credenciales (ver https://github.com/Kaggle/kaggle-api)
mkdir -p ~/.kaggle
# Copiar tu kaggle.json desde Kaggle Settings

# Descargar el dataset
kaggle datasets download -d marlesson/myanimelist-dataset-animes-profiles-reviews -p ./data --unzip
```

## Ingestión en MongoDB

Una vez que los archivos CSV estén presentes en este directorio, ejecuta:

```bash
# Activar el entorno virtual (si no está activo)
source venv/Scripts/activate

# Ejecutar el módulo de ingestión
python -m src.ingestion
```

El script automáticamente:

1. Validará que los archivos existan
2. Evitará reingestar si la colección ya tiene datos
3. Procesará los datos en lotes para minimizar consumo de memoria
4. Para la colección `animes`, normalizará géneros y puntuaciones

## Notas Importantes

- **Tamaño:** El dataset completo ocupa aproximadamente 675 MB descomprimido.
- **Duración de ingestión:** Dependiendo de tu hardware, la ingestión puede tomar 5-15 minutos.
- **MongoDB debe estar corriendo:** Asegúrate de que Docker Compose haya iniciado MongoDB antes de ejecutar `ingestion.py`.

```bash
docker-compose up -d
```

## Estructura del Repositorio

Los archivos CSV **no se versionan en Git** para mantener el repositorio ligero. Si necesitas los datos en otra máquina:

1. Descárgalos nuevamente desde Kaggle
2. O usa la API de Kaggle como se indica arriba
