import pandas as pd
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from fastapi import FastAPI, HTTPException
from src.database import get_db
import re
import gc

# Definimos el esquema de datos que recibirá el endpoint
class ConsultaContenido(BaseModel):
    generos: list[str]
    anio_min: int
    anio_max: int
    descripcion: str

# Inicializar la aplicación
app = FastAPI(
    title="Anime Analytics API",
    description="API NoSQL para gestión de datos y recomendaciones",
    version="1.0.0"
)

# Conexión a MongoDB
db = get_db()
coleccion_animes = db["animes"]
coleccion_reviews = db["reseñas"]

def eliminar_duplicados(lista_animes, limite=None):
    """Filtra una lista de diccionarios dejando solo títulos únicos."""
    vistos = set()
    unicos = []
    for anime in lista_animes:
        titulo = anime.get("title")
        if titulo not in vistos:
            vistos.add(titulo)
            unicos.append(anime)
            
        if limite and len(unicos) == limite:
            break
    return unicos

@app.get("/")
def read_root():
    return {"status": "online", "mensaje": "API conectada a MongoDB correctamente"}

# --- ENDPOINT PARA VISTA 1: Búsqueda de Anime ---
@app.get("/api/anime/buscar/{titulo}")
def buscar_anime(titulo: str):
    regex = re.compile(f".*{titulo}.*", re.IGNORECASE)
    
    # .find() devuelve un cursor, lo ordenamos por score descendente y limitamos a 50
    # Liimpiamos duplicados para que nos queden al menos 15 únicos
    cursor = coleccion_animes.find(
        {"title": regex}, 
        {"_id": 0, "uid": 1, "title": 1, "synopsis": 1, "genre": 1, "score": 1, "img_url": 1, "episodes": 1}
    ).sort("score", -1).limit(50)
    
    resultados_unicos = eliminar_duplicados(list(cursor), limite=15)
    
    if not resultados_unicos:
        raise HTTPException(status_code=404, detail="No se encontraron coincidencias")
        
    return resultados_unicos

# --- ENDPOINT PARA VISTA 2: Analítica Global (Pipelines) ---
@app.get("/api/analytics/top-generos")
def top_generos_calificados():
    # Pipeline de agregación equivalente a un GROUP BY
    pipeline = [
        # Separar el array de géneros en documentos individuales
        {"$unwind": "$genre"},
        # Agrupar por género y calcular el promedio de score
        {"$group": {
            "_id": "$genre",
            "promedio_score": {"$avg": "$score"},
            "total_animes": {"$sum": 1}
        }},
        # Filtrar géneros con menos de 50 animes para tener significancia estadística
        {"$match": {"total_animes": {"$gte": 50}}},
        # Ordenar de mayor a menor promedio
        {"$sort": {"promedio_score": -1}},
        # Limitar a los 10 mejores
        {"$limit": 10}
    ]
    
    resultados = list(coleccion_animes.aggregate(pipeline))
    return resultados

# --- NUEVO ENDPOINT PARA VISTA 2: Top por Género ---
@app.get("/api/anime/genero/{genero}")
def top_por_genero(genero: str):
    # Buscamos animes que contengan la cadena del género exacto
    regex = re.compile(f".*{genero}.*", re.IGNORECASE)
    
    # Extraemos 30 para asegurar 5 únicos
    cursor = coleccion_animes.find(
        {"genre": regex},
        {"_id": 0, "title": 1, "score": 1, "img_url": 1}
    ).sort("score", -1).limit(30)
    
    return eliminar_duplicados(list(cursor), limite=5)

# --- ENDPOINT PARA VISTA 3: Obtener Usuarios Aleatorios ---
@app.get("/api/users/random")
def obtener_usuarios_aleatorios():
    # Usamos $sample directo para recuperar un puñado de perfiles de forma rápida y sin validaciones extra
    pipeline = [
        {"$sample": {"size": 20}},
        {"$group": {"_id": "$profile"}},
        {"$limit": 5}
    ]
    usuarios = list(coleccion_reviews.aggregate(pipeline))
    return [u["_id"] for u in usuarios if u["_id"]]

# --- ENDPOINT PARA VISTA 3: Motor Matemático (Filtrado Colaborativo) ---
@app.get("/api/recommend/collaborative/{profile}")
def recomendacion_colaborativa(profile: str):
    # 1. Obtener las reseñas del usuario de prueba
    user_reviews = list(coleccion_reviews.find({"profile": profile}, {"_id": 0, "profile": 1, "anime_uid": 1, "score": 1}))
    if not user_reviews:
        raise HTTPException(status_code=404, detail="El perfil no tiene reseñas registradas.")
    
    user_animes = [r["anime_uid"] for r in user_reviews]
    
    # 2. Recuperar Muestra Inteligente: Usuarios que interactuaron con el mismo contenido
    pipeline = [
        {"$match": {"anime_uid": {"$in": user_animes}, "profile": {"$ne": profile}}},
        {"$sample": {"size": 3000}} # Acotado a 3000 registros para evitar colapso de RAM
    ]
    similar_users_reviews = list(coleccion_reviews.aggregate(pipeline))
    
    if not similar_users_reviews:
        raise HTTPException(status_code=404, detail="No hay intersección de datos suficientes para este perfil.")
        
    perfiles_similares = list(set([r["profile"] for r in similar_users_reviews]))
    
    # 3. Traer el historial completo de esos vecinos
    historial_vecinos = list(coleccion_reviews.find(
        {"profile": {"$in": perfiles_similares}}, 
        {"_id": 0, "profile": 1, "anime_uid": 1, "score": 1}
    ).limit(15000))
    
    # 4. Construcción de la Matriz Dispersa con Pandas
    df = pd.DataFrame(user_reviews + historial_vecinos)
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
    matriz_usuario_item = df.pivot_table(index='profile', columns='anime_uid', values='score').fillna(0)
    
    if profile not in matriz_usuario_item.index:
        raise HTTPException(status_code=500, detail="Error en la generación del vector objetivo.")
        
    # 
    # 5. Cálculo de Distancias: Similitud del Coseno
    matriz_similitud = cosine_similarity(matriz_usuario_item)
    df_similitud = pd.DataFrame(matriz_similitud, index=matriz_usuario_item.index, columns=matriz_usuario_item.index)
    
    # Aislar a los 5 vecinos más idénticos matemáticamente
    vecinos_cercanos = df_similitud[profile].sort_values(ascending=False)[1:6].index.tolist()
    
    # 6. Inferir Recomendaciones
    historial_filtrado = df[df['profile'].isin(vecinos_cercanos)]
    # Eliminar lo que el usuario objetivo ya vio
    recomendaciones_potenciales = historial_filtrado[~historial_filtrado['anime_uid'].isin(user_animes)]
    
    # Ordenar por el score promedio dado por los vecinos
    top_animes_uid = recomendaciones_potenciales.groupby('anime_uid')['score'].mean().sort_values(ascending=False).head(5).index.tolist()
    
    # 7. Recuperar metadatos visuales de MongoDB
    resultado_bruto = list(coleccion_animes.find(
        {"uid": {"$in": top_animes_uid}},
        {"_id": 0, "title": 1, "img_url": 1, "score": 1}
    ))
    
    # Ordenar por score y limpiar posibles series duplicadas
    resultado_bruto.sort(key=lambda x: x.get("score", 0), reverse=True)
    return eliminar_duplicados(resultado_bruto, limite=5)

# --- ENDPOINT PARA VISTA 4: Recomendación por Contenido (TF-IDF) ---
@app.post("/api/recommend/content")
def recomendacion_por_contenido(consulta: ConsultaContenido):
    filtro = {}
    
    if consulta.generos:
        filtro["genre"] = {"$all": consulta.generos}
        
    rango_anios = "|".join([str(anio) for anio in range(consulta.anio_min, consulta.anio_max + 1)])
    filtro["aired"] = {"$regex": f"({rango_anios})"}
    filtro["synopsis"] = {"$exists": True, "$ne": ""}

    # LÍMITE DURO ANTI-PAGINACIÓN: Máximo 1000 documentos a RAM
    catalogo_bruto = list(coleccion_animes.find(
        filtro, 
        {"_id": 0, "uid": 1, "title": 1, "synopsis": 1, "img_url": 1, "score": 1, "genre": 1}
    ).limit(1000))
    
    if not catalogo_bruto:
        raise HTTPException(status_code=404, detail="Ningún anime cumple con los filtros seleccionados.")
        
    # Limpiamos los duplicados ANTES de meterlos a Scikit-learn
    catalogo_filtrado = eliminar_duplicados(catalogo_bruto)

    if not consulta.descripcion.strip():
        catalogo_filtrado.sort(key=lambda x: x.get("score", 0), reverse=True)
        return catalogo_filtrado[:5]

    # Traducción del prompt (Español -> Inglés)
    prompt_ingles = GoogleTranslator(source='es', target='en').translate(consulta.descripcion)
    
    sinopsis_lista = [anime["synopsis"] for anime in catalogo_filtrado]
    textos_a_vectorizar = [prompt_ingles] + sinopsis_lista
    
    # Límite de vocabulario para mantener la matriz dispersa muy pequeña
    vectorizador = TfidfVectorizer(stop_words='english', max_features=3000)
    matriz_tfidf = vectorizador.fit_transform(textos_a_vectorizar)
    
    # Cálculo de Similitud
    similitudes = cosine_similarity(matriz_tfidf[0:1], matriz_tfidf[1:]).flatten()
    indices_top5 = similitudes.argsort()[-5:][::-1]
    
    resultados_finales = []
    for idx in indices_top5:
        if similitudes[idx] > 0:
            anime_recomendado = catalogo_filtrado[idx]
            anime_recomendado["match_semantico"] = round(float(similitudes[idx]) * 100, 2)
            resultados_finales.append(anime_recomendado)
            
    # FORZAR LIBERACIÓN DE MEMORIA RAM
    del matriz_tfidf
    del vectorizador
    del textos_a_vectorizar
    del similitudes
    gc.collect()
            
    if not resultados_finales:
        raise HTTPException(status_code=404, detail="No se encontraron coincidencias semánticas con tu descripción.")
        
    return resultados_finales