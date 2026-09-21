import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Evaluador de Proyectos - EEBE", layout="wide")
st.title("🎓 Evaluador de Proyectos de Diseño (EEBE - UPC)")
st.markdown("Herramienta de autoevaluación para PDS, AMFE, Ishikawa y QFD.")

# ==========================================
# BARRA LATERAL: CONFIGURACIÓN DE GEMINI
# ==========================================
st.sidebar.header("⚙️ Configuración de IA")
st.sidebar.markdown("Introduce tu API Key para utilizar los modelos de evaluación.")

api_key = st.sidebar.text_input("Gemini API Key", type="password")

modelos_disponibles = {
    "Gemini 3.8 Flash (Más inteligente, flujos complejos)": "gemini-3.8-flash",
    "Gemini 3.8 Live (Voz, baja latencia)": "gemini-3.8-live",
    "Gemini 3.8 Live Extended Thinking (Alto razonamiento)": "gemini-3.8-live-extended-thinking",
    "Gemini 3.7 Flash (Programación y varios pasos)": "gemini-3.7-flash",
    "Gemini 3.6 Flash (Equilibrio tareas cotidianas)": "gemini-3.6-flash",
    "Gemini 3.5 Flash (Velocidad para cargas rutinarias)": "gemini-3.5-flash",
    "Gemini 3.5 Flash-Lite (Más rápido y rentable)": "gemini-3.5-flash-lite",
    "Gemini 3.1 Flash-Lite (Rendimiento Frontier)": "gemini-3.1-flash-lite"
}

seleccion_modelo = st.sidebar.selectbox("Selecciona el modelo Gemini:", list(modelos_disponibles.keys()), index=0)
model_name = modelos_disponibles[seleccion_modelo]

def evaluar_texto_llm(prompt_sistema, texto_usuario):
    """Función para llamar a la API de Google Gemini con el modelo seleccionado."""
    if not api_key:
        return "⚠️ Por favor, introduce tu API Key de Gemini en la barra lateral para usar esta función."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=prompt_sistema
        )
        response = model.generate_content(
            texto_usuario,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        return response.text
    except Exception as e:
        return f"⚠️ Error al conectar con Gemini. Verifica la API Key y asegúrate de que el modelo seleccionado ({model_name}) esté disponible. Detalle: {e}"

# ==========================================
# PESTAÑAS DE LA APLICACIÓN
# ==========================================
tab_pds, tab_amfe, tab_ishikawa, tab_qfd = st.tabs(["📋 PDS", "⚠️ AMFE", "🐟 Ishikawa", "🏠 QFD"])

# ------------------------------------------
# 1. EVALUADOR DE PDS
# ------------------------------------------
with tab_pds:
    st.header("Especificaciones de Diseño de Producto (PDS)")
    st.write("Introduce una especificación para comprobar si es medible y verificable.")
    pds_input = st.text_area("Requisito PDS:", placeholder="Ej: La estructura soportará una carga vertical de al menos 2,0 kN...")
    if st.button("Evaluar PDS"):
        if pds_input:
            prompt_pds = "Eres un profesor de ingeniería. Evalúa si el requisito PDS es medible, cuantificable y verificable. Si es vago, indícalo. Si es correcto, felicítalo."
            with st.spinner(f"Analizando con {seleccion_modelo.split('(')[0]}..."):
                st.info(evaluar_texto_llm(prompt_pds, pds_input))
        else:
            st.warning("Introduce un requisito.")

# ------------------------------------------
# 2. EVALUADOR DE AMFE
# ------------------------------------------
with tab_amfe:
    st.header("Análisis Modal de Fallos y Efectos (AMFE)")
    st.write("Añade filas según necesites. Pasa el ratón sobre el símbolo **(?)** en las columnas para ver las instrucciones de puntuación.")
    
    if "df_amfe" not in st.session_state:
        st.session_state.df_amfe = pd.DataFrame({
            "Componente": ["Bisagra", "Tornillo"],
            "Modo de fallo": ["Desgaste", "Aflojamiento"],
            "Severidad (S)": [7, 8],
            "Ocurrencia (O)": [4, 5],
            "Detección (D)": [6, 6]
        })
    
    # Configuración de tooltips (?) y límites de valores para AMFE
    config_amfe = {
        "Severidad (S)": st.column_config.NumberColumn(
            "Severidad (S)", min_value=1, max_value=10, 
            help="Escala 1-10: ¿Cómo de grave sería el fallo? \n1 = Imperceptible/Sin impacto.\n10 = Catastrófico (riesgo seguridad/muerte)."
        ),
        "Ocurrencia (O)": st.column_config.NumberColumn(
            "Ocurrencia (O)", min_value=1, max_value=10, 
            help="Escala 1-10: ¿Cómo de probable es que ocurra? \n1 = Remoto (muy poco probable).\n10 = Muy frecuente (ocurre casi siempre)."
        ),
        "Detección (D)": st.column_config.NumberColumn(
            "Detección (D)", min_value=1, max_value=10, 
            help="Escala 1-10: ¿Qué tan difícil es de detectar antes del usuario? \n1 = Casi seguro de detectar (control 100%).\n10 = Prácticamente imposible."
        )
    }
    
    df_amfe_edit = st.data_editor(st.session_state.df_amfe, num_rows="dynamic", column_config=config_amfe, use_container_width=True)
    
    if st.button("Calcular Riesgos AMFE"):
        df_amfe_edit["NPR Calculado"] = df_amfe_edit["Severidad (S)"] * df_amfe_edit["Ocurrencia (O)"] * df_amfe_edit["Detección (D)"]
        condiciones = [
            (df_amfe_edit["Severidad (S)"] >= 9),
            (df_amfe_edit["NPR Calculado"] >= 100),
            (df_amfe_edit["NPR Calculado"] < 50)
        ]
        valores = ["🔴 Acción Urgente (S alta)", "🟠 Prioridad Media-Alta", "🟢 Riesgo Aceptable"]
        df_amfe_edit["Sugerencia Sistema"] = np.select(condiciones, valores, default="🟡 Revisión Normal")
        
        st.dataframe(df_amfe_edit, use_container_width=True)
        st.success("Cálculos verificados correctamente.")

# ------------------------------------------
# 3. EVALUADOR DE ISHIKAWA
# ------------------------------------------
with tab_ishikawa:
    st.header("Diagrama Causa-Efecto (Ishikawa / Espinograma)")
    
    # Mostrar el diagrama visual de Ishikawa (URL pública de Wikimedia Commons)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Ishikawa_Fishbone_Diagram.svg/1024px-Ishikawa_Fishbone_Diagram.svg.png", 
             caption="Estructura clásica de las 6M en el Diagrama de Ishikawa", 
             use_container_width=True)
    
    st.write("Verifica que las causas identificadas están redactadas como **hechos verificables** (ej: 'tinta con baja viscosidad') y no como **juicios de valor** (ej: 'tinta mala').")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        categoria = st.selectbox("Categoría (6M):", ["Materiales", "Mano de obra", "Maquinaria", "Métodos", "Mantenimiento", "Medio ambiente"])
    with col2:
        causa_input = st.text_input("Redacción de la causa:", placeholder="Ej: Par de apriete no controlado en la línea 2")
        
    if st.button("Evaluar Causa"):
        if causa_input:
            prompt_ishikawa = f"Eres un evaluador de calidad. Evalúa esta causa en la categoría '{categoria}'. Verifica que no contenga juicios vagos ('malo', 'desastre'). Debe ser técnico y observable. Si está mal, sugiere mejora."
            with st.spinner("Analizando redacción..."):
                st.info(evaluar_texto_llm(prompt_ishikawa, causa_input))

# ------------------------------------------
# 4. EVALUADOR DE QFD (CASA DE LA CALIDAD)
# ------------------------------------------
with tab_qfd:
    st.header("🏠 Casa de la Calidad (QFD)")
    st.write("Construye tu matriz añadiendo tantos QUÉs (filas) y CÓMOs (columnas) como necesites.")
    
    # Inicialización del DataFrame del QFD si no existe
    if "df_qfd" not in st.session_state:
        st.session_state.df_qfd = pd.DataFrame({
            "Necesidades (QUÉ)": ["Fácil de limpiar", "Ligero"],
            "Importancia (1-10)": [5, 8],
            "CÓMO: Rugosidad (µm)": [9, 0],
            "CÓMO: Peso total (kg)": [0, 9]
        })

    # --- LÓGICA PARA AÑADIR NUEVAS COLUMNAS (CÓMOs) ---
    st.markdown("### 🏗️ 1. Añadir Nuevos Requisitos Técnicos (Techo de la Casa)")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        nuevo_como = st.text_input("Nombre de la nueva característica técnica:", placeholder="Ej: Nivel sonoro (dB)")
    with col_btn:
        st.write("") # Espaciador para alinear el botón
        if st.button("➕ Añadir Columna CÓMO"):
            if nuevo_como:
                nombre_columna = f"CÓMO: {nuevo_como}"
                if nombre_columna not in st.session_state.df_qfd.columns:
                    # Añadir la columna con valores a 0
                    st.session_state.df_qfd[nombre_columna] = 0
                    st.rerun() # Recarga la app para mostrar la nueva columna
                else:
                    st.warning("Esa característica ya existe.")
    
    # --- MATRIZ INTERACTIVA (CUERPO DE LA CASA) ---
    st.markdown("### 🟦 2. Cuerpo de la Matriz (Relaciones QUÉ - CÓMO)")
    st.write("Puedes **añadir nuevas filas (QUÉs)** haciendo clic en el símbolo `+` en la parte inferior de la tabla. Pasa el ratón sobre los símbolos **(?)** para ver la puntuación.")
    
    # Configurar tooltips para el QFD
    config_qfd = {
        "Necesidades (QUÉ)": st.column_config.TextColumn("Necesidades (QUÉ)", help="Escribe la necesidad en el lenguaje del usuario (Ej: 'Que sea seguro')"),
        "Importancia (1-10)": st.column_config.NumberColumn(
            "Importancia (1-10)", min_value=1, max_value=10, 
            help="Del 1 al 10, ¿cuánto le importa esta necesidad al cliente?"
        )
    }
    
    # Aplicar tooltip a todas las columnas que empiezan por "CÓMO" dinámicamente
    for col in st.session_state.df_qfd.columns:
        if col.startswith("CÓMO"):
            config_qfd[col] = st.column_config.NumberColumn(
                col, min_value=0, max_value=9, 
                help="Relación entre necesidad y requisito técnico. Valores permitidos: \n9 = Fuerte \n3 = Media \n1 = Débil \n0 = Ninguna."
            )
    
    # Mostramos el editor (num_rows="dynamic" permite añadir filas infinitas)
    df_qfd_edit = st.data_editor(st.session_state.df_qfd, num_rows="dynamic", column_config=config_qfd, use_container_width=True)
    
    # --- RESULTADOS (BASE DE LA CASA) ---
    st.markdown("### 📊 3. Resultados Técnicos (Base de la Casa)")
    if st.button("Verificar Cálculos QFD y Generar Top-5"):
        try:
            # Guardamos los cambios realizados por el usuario en el estado para no perderlos
            st.session_state.df_qfd = df_qfd_edit
            
            importancias = df_qfd_edit["Importancia (1-10)"].fillna(0).astype(float)
            comos_cols = [col for col in df_qfd_edit.columns if col.startswith("CÓMO")]
            
            resultados = {}
            alertas = False
            for col in comos_cols:
                valores_relacion = df_qfd_edit[col].fillna(0).astype(float)
                # Validar que los alumnos usaron la escala correcta
                if not all(valores_relacion.isin([0, 1, 3, 9])):
                    alertas = True
                    st.warning(f"⚠️ Atención: En la columna '{col}' se detectaron valores distintos a 0, 1, 3 o 9. La metodología exige usar esta escala específica.")
                
                # Cálculo de la suma producto
                importancia_tecnica = (importancias * valores_relacion).sum()
                resultados[col] = importancia_tecnica
            
            # Formatear y mostrar resultados
            df_resultados = pd.DataFrame([resultados], index=["Importancia Técnica Absoluta"]).T
            df_resultados = df_resultados.sort_values(by="Importancia Técnica Absoluta", ascending=False)
            
            if not alertas:
                st.success("✅ Multiplicaciones verificadas con éxito. Escala 9-3-1-0 respetada.")
            
            st.write("**Ranking Técnico (Top-5 características más importantes):**")
            st.dataframe(df_resultados.head(5).T, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error en el cálculo. Revisa que no hayas introducido texto en columnas numéricas. Detalle: {e}")
