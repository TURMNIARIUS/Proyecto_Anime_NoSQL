import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title="Anime Data Terminal v1.0", layout="wide")

# URL base del backend (FastAPI)
BACKEND_URL = "http://127.0.0.1:8000"

# =========================================================================
# INYECCIÓN DE CSS (Transparencias y Colores Específicos)
# =========================================================================
st.markdown("""
<style>
    /* Fondo del pánel principal: Azul eléctrico oscuro / falsa transparencia */
    .stApp {
        background-color: rgba(15, 35, 80, 0.95) !important;
    }
    /* Fondo del pánel lateral: Azul profundo */
    [data-testid="stSidebar"] {
        background-color: #050A15 !important;
    }
    /* Estilo para la caja de estatus verde neón */
    .status-neon {
        background-color: rgba(0, 255, 0, 0.1);
        color: #39FF14;
        padding: 10px;
        border-radius: 3px;
        border: 1px solid #39FF14;
        font-family: monospace;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("SISTEMA CONTROL")
    st.sidebar.markdown("---")
    
    menu = ["1. Exploración del Catálogo", 
            "2. Analítica Global", 
            "3. Recomendador (Colaborativo)", 
            "4. Recomendador (Por Contenido)"]
    
    eleccion = st.sidebar.selectbox("Seleccione un directorio:", menu)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="status-neon">Estatus: CONECTADO_</div>', unsafe_allow_html=True)
    
    # =========================================================================
    # VISTA 1: EXPLORACIÓN DEL CATÁLOGO (Top 15 y Selección)
    # =========================================================================
    if eleccion == "1. Exploración del Catálogo":
        st.title("📂 EXPLORACIÓN DE DOCUMENTOS (ANIME)")
        
        busqueda = st.text_input("Ingrese el título a consultar:")
        
        if busqueda:
            try:
                response = requests.get(f"{BACKEND_URL}/api/anime/buscar/{busqueda}")
                if response.status_code == 200:
                    resultados = response.json()
                    df_resultados = pd.DataFrame(resultados)
                    
                    # Limpiamos la tabla para que sea agradable a la vista
                    df_mostrar = df_resultados[['title', 'score', 'episodes']].copy()
                    df_mostrar.columns = ['Título', 'Puntuación', 'Episodios']
                    df_mostrar.index = range(1, len(df_mostrar) + 1)
                    
                    st.write("Seleccione una fila para ver el detalle completo:")
                    
                    # Tabla interactiva (requiere Streamlit >= 1.35)
                    evento_seleccion = st.dataframe(
                        df_mostrar, 
                        use_container_width=True, 
                        selection_mode="single-row",
                        on_select="rerun"
                    )
                    
                    # Si el usuario hace clic en una fila, mostramos el detalle
                    filas_seleccionadas = evento_seleccion.selection.rows
                    if filas_seleccionadas:
                        indice = filas_seleccionadas[0]
                        anime_seleccionado = resultados[indice] # Recuperamos el JSON original
                        
                        st.markdown("---")
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            if pd.notna(anime_seleccionado.get("img_url")):
                                st.image(anime_seleccionado["img_url"], width=200)
                        with col_info:
                            st.subheader(anime_seleccionado['title'])
                            st.write(f"**Score:** {anime_seleccionado.get('score', 'N/A')}")
                            st.write(f"**Géneros:** {anime_seleccionado.get('genre', 'N/A')}")
                            st.write(f"**Sinopsis:** {anime_seleccionado.get('synopsis', 'N/A')}")
                            
                elif response.status_code == 404:
                    st.warning("No se encontraron resultados.")
            except Exception as e:
                st.error("Error de conexión con la API.")

    # =========================================================================
    # VISTA 2: ANALÍTICA GLOBAL (Gráfica, Índice Numérico y Sub-Vista)
    # =========================================================================
    elif eleccion == "2. Analítica Global":
        st.title("📊 PROCESAMIENTO DE ESTADÍSTICOS")
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/analytics/top-generos")
            if response.status_code == 200:
                datos = response.json()
                
                # VALIDACIÓN DEFENSIVA: ¿La API devolvió datos vacíos?
                if not datos:
                    st.warning("⚠️ La consulta se ejecutó, pero no devolvió resultados. Verifica que la colección 'animes' en MongoDB tenga datos y cumpla con el mínimo de 50 registros por género.")
                else:
                    df = pd.DataFrame(datos)
                    df = df.rename(columns={"_id": "Género", "promedio_score": "Score Promedio", "total_animes": "Volumen"})
                    
                    df.index = range(1, len(df) + 1)
                    
                    fig = px.bar(
                        df, x="Score Promedio", y="Género", orientation='h',
                        text="Score Promedio", color="Score Promedio", color_continuous_scale="Blues"
                    )
                    
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'}, 
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#FFFFFF")     
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("**SELECCIONE UNA COMBINACIÓN EN LA TABLA PARA VER RECOMENDACIONES:**")
                    
                    evento_tabla = st.dataframe(
                        df, 
                        use_container_width=True,
                        selection_mode="single-row",
                        on_select="rerun"
                    )
                    
                    filas_tabla = evento_tabla.selection.rows
                    if filas_tabla:
                        indice_tabla = filas_tabla[0]
                        genero_seleccionado = df.iloc[indice_tabla]["Género"]
                        
                        terminos_prohibidos = ["Hentai", "Ecchi", "Erotica", "Smut"]
                        es_seguro = not any(termino in genero_seleccionado for termino in terminos_prohibidos)
                        
                        st.markdown("---")
                        if es_seguro:
                            st.subheader(f"Mejores animes para: {genero_seleccionado}")
                            termino_busqueda = genero_seleccionado.replace("['", "").split("',")[0].replace("']", "")
                            
                            resp_genero = requests.get(f"{BACKEND_URL}/api/anime/genero/{termino_busqueda}")
                            if resp_genero.status_code == 200:
                                top_animes = resp_genero.json()
                                cols = st.columns(len(top_animes))
                                for idx, anime in enumerate(top_animes):
                                    with cols[idx]:
                                        if pd.notna(anime.get("img_url")):
                                            st.image(anime["img_url"], use_container_width=True)
                                        st.markdown(f"**{anime['title']}**")
                                        st.write(f"Score: {anime.get('score', 0)}")
                        else:
                            st.error("⚠️ El género seleccionado contiene material restringido. La sub-vista ha sido bloqueada.")
                            
        except Exception as e:
            # Ahora mostraremos el error real en pantalla si algo falla
            st.error(f"Fallo en la ejecución: {type(e).__name__} - {str(e)}")
    
    # =========================================================================
    # VISTA 3: MOTOR DE RECOMENDACIÓN FILTRADO COLABORATIVO
    # =========================================================================
    elif eleccion == "3. Recomendador (Colaborativo)":
        st.title("🧠 FILTRADO COLABORATIVO: K-NEAREST NEIGHBORS")
        st.write("Generación de predicciones calculando la Similitud del Coseno sobre matrices de comportamiento de usuarios.")
        st.markdown("---")
        
        col_ctrl, col_visual = st.columns([1, 2])
        
        with col_ctrl:
            st.markdown('<div style="color: #39FF14; font-weight: bold;">[ RECUPERACIÓN DE DATOS ]</div>', unsafe_allow_html=True)
            
            # Botón para cargar perfiles aleatorios. Se guardan en session_state para que no desaparezcan.
            if st.button("Generar Perfiles de Prueba"):
                with st.spinner("Muestreando MongoDB..."):
                    try:
                        res_rand = requests.get(f"{BACKEND_URL}/api/users/random")
                        if res_rand.status_code == 200:
                            st.session_state['perfiles_muestra'] = res_rand.json()
                    except:
                        st.error("Error de conexión.")
                        
            muestras = st.session_state.get('perfiles_muestra', ["Haga clic en 'Generar Perfiles'"])
            st.selectbox("Muestra extraída (Solo lectura):", muestras)
            
        with col_visual:
            st.markdown('<div style="color: #39FF14; font-weight: bold;">[ EJECUCIÓN DEL ALGORITMO ]</div>', unsafe_allow_html=True)
            usuario_input = st.text_input("Ingrese el ID del Perfil Objetivo:")
            
            if st.button("CALCULAR RECOMENDACIONES"):
                if usuario_input:
                    with st.spinner("Construyendo matriz dispersa y calculando vectores..."):
                        try:
                            res_reco = requests.get(f"{BACKEND_URL}/api/recommend/collaborative/{usuario_input}")
                            
                            if res_reco.status_code == 200:
                                recos = res_reco.json()
                                if recos:
                                    st.success(f"Cálculo completado. Coincidencias para: {usuario_input}")
                                    st.markdown("---")
                                    
                                    # Despliegue de los 5 animes devueltos por el algoritmo
                                    columnas_img = st.columns(len(recos))
                                    for idx, anime in enumerate(recos):
                                        with columnas_img[idx]:
                                            if pd.notna(anime.get("img_url")):
                                                st.image(anime["img_url"], use_container_width=True)
                                            st.markdown(f"**{anime['title']}**")
                                            st.write(f"Score Global: {anime.get('score', 0)}")
                                else:
                                    st.warning("El motor no encontró recomendaciones nuevas que superen el umbral de confianza.")
                                    
                            elif res_reco.status_code == 404:
                                st.warning(res_reco.json().get("detail", "Error de datos."))
                            else:
                                st.error("Error interno en el servidor API.")
                        except Exception as e:
                            st.error(f"Fallo en la ejecución: {type(e).__name__} - {str(e)}")
                else:
                    st.warning("Debe ingresar un perfil válido antes de ejecutar el cálculo.")
    
    # =========================================================================
    # VISTA 4: RECOMENDACIÓN SEMÁNTICA POR CONTENIDO
    # =========================================================================
    elif eleccion == "4. Recomendador (Por Contenido)":
        st.title("🔬 BÚSQUEDA SEMÁNTICA Y FILTROS")
        st.write("Análisis TF-IDF para medir la distancia matemática entre tu idea y las sinopsis del catálogo.")
        st.markdown("---")
        
        col_filtros, col_texto = st.columns(2)
        
        with col_filtros:
            st.markdown('<div style="color: #39FF14; font-weight: bold;">[ FILTROS ESTRUCTURADOS ]</div>', unsafe_allow_html=True)
            opciones_generos = ['Action', 'Adventure', 'Comedy', 'Drama', 'Sci-Fi', 'Fantasy', 'Romance', 'Slice of Life', 'Mecha', 'Sports', 'Psychological', 'Horror', 'Mystery']
            generos_seleccionados = st.multiselect("Géneros requeridos:", opciones_generos)
            
            anio_min, anio_max = st.slider("Periodo de emisión:", 1970, 2023, (1995, 2010))
            
        with col_texto:
            st.markdown('<div style="color: #39FF14; font-weight: bold;">[ ANÁLISIS DE TEXTO ]</div>', unsafe_allow_html=True)
            descripcion = st.text_area(
                "Describe la trama en español:", 
                placeholder="Ej. Una academia militar donde adolescentes pilotan robots para pelear...",
                height=130
            )
            
        if st.button("EJECUTAR BÚSQUEDA SEMÁNTICA"):
            with st.spinner("Procesando matriz de texto..."):
                payload = {
                    "generos": generos_seleccionados,
                    "anio_min": anio_min,
                    "anio_max": anio_max,
                    "descripcion": descripcion
                }
                
                try:
                    res_content = requests.post(f"{BACKEND_URL}/api/recommend/content", json=payload)
                    
                    if res_content.status_code == 200:
                        resultados = res_content.json()
                        st.success("Análisis completado exitosamente.")
                        st.markdown("---")
                        
                        cols = st.columns(len(resultados))
                        for idx, anime in enumerate(resultados):
                            with cols[idx]:
                                if pd.notna(anime.get("img_url")):
                                    st.image(anime["img_url"], use_container_width=True)
                                st.markdown(f"**{anime['title']}**")
                                if "match_semantico" in anime:
                                    st.caption(f"🎯 Match Textual: {anime['match_semantico']}%")
                                st.write(f"Score: {anime.get('score', 0)}")
                                
                    elif res_content.status_code == 404:
                        st.warning(res_content.json().get("detail", "Sin resultados."))
                    else:
                        st.error("Error en el servidor API.")
                except Exception as e:
                    st.error(f"Fallo en la ejecución: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    main()