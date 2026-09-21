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
st.sidebar.markdown("Consigue tu API Key gratuita en [Google AI Studio](https://aistudio.google.com/).")

api_key = st.sidebar.text_input("Gemini API Key", type="password")
model_name = st.sidebar.selectbox("Modelo", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0, help="Flash es más rápido, Pro es más analítico.")

def evaluar_texto_llm(prompt_sistema, texto_usuario):
    """Función para llamar a la API de Google Gemini."""
    if not api_key:
        return "⚠️ Por favor, introduce tu API Key de Gemini en la barra lateral para usar esta función."
    
    try:
        # Configurar la clave de autenticación
        genai.configure(api_key=api_key)
        
        # Inicializar el modelo con las instrucciones de sistema
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=prompt_sistema
        )
        
        # Generar la respuesta con baja temperatura para respuestas objetivas
        response = model.generate_content(
            texto_usuario,
            generation_config=genai.types.GenerationConfig(temperature=0.3)
        )
        return response.text
    except Exception as e:
        return f"⚠️ Error al conectar con Gemini. Verifica la API Key. Detalle: {e}"

# ==========================================
# PESTAÑAS DE LA APLICACIÓN
# ==========================================
tab_pds, tab_amfe, tab_ishikawa, tab_qfd = st.tabs(["📋 PDS", "⚠️ AMFE", "🐟 Ishikawa", "🏠 QFD"])

# ------------------------------------------
# 1. EVALUADOR DE PDS
# ------------------------------------------
with tab_pds:
    st.header("Especificaciones de Diseño de Producto (PDS)")
    st.write("Introduce una especificación para comprobar si es correcta (medible y clara) o si es demasiado ambigua.")
    
    pds_input = st.text_area("Requisito PDS:", placeholder="Ej: La estructura soportará una carga vertical de al menos 2,0 kN...")
    
    if st.button("Evaluar PDS"):
        if pds_input:
            prompt_pds = """Eres un profesor de ingeniería de diseño. Evalúa si el siguiente requisito PDS es medible, cuantificable y verificable. 
            Si es vago (ej. 'fácil de usar', 'resistente', 'barato'), indícale al alumno que está mal y explícale que debe usar valores numéricos, métricas o normativas. 
            Si es correcto, felicítalo brevemente y confirma por qué lo es."""
            
            with st.spinner("Analizando con Gemini..."):
                resultado = evaluar_texto_llm(prompt_pds, pds_input)
            st.info(resultado)
        else:
            st.warning("Por favor, introduce un requisito.")

# ------------------------------------------
# 2. EVALUADOR DE AMFE
# ------------------------------------------
with tab_amfe:
    st.header("Análisis Modal de Fallos y Efectos (AMFE)")
    st.write("Introduce tus valores (1-10) para calcular automáticamente el NPR (Número de Prioridad de Riesgo) y sugerir la criticidad.")
    
    # DataFrame por defecto
    if "df_amfe" not in st.session_state:
        st.session_state.df_amfe = pd.DataFrame({
            "Componente": ["Bisagra", "Tornillo"],
            "Modo de fallo": ["Desgaste", "Aflojamiento"],
            "Severidad (S)": [7, 8],
            "Ocurrencia (O)": [4, 5],
            "Detección (D)": [6, 6]
        })
    
    df_amfe_edit = st.data_editor(st.session_state.df_amfe, num_rows="dynamic")
    
    if st.button("Calcular Riesgos AMFE"):
        df_amfe_edit["NPR Calculado"] = df_amfe_edit["Severidad (S)"] * df_amfe_edit["Ocurrencia (O)"] * df_amfe_edit["Detección (D)"]
        
        condiciones = [
            (df_amfe_edit["Severidad (S)"] >= 9),
            (df_amfe_edit["NPR Calculado"] >= 100),
            (df_amfe_edit["NPR Calculado"] < 50)
        ]
        valores = ["🔴 Acción Urgente (S alta)", "🟠 Prioridad Media-Alta", "🟢 Riesgo Aceptable"]
        df_amfe_edit["Sugerencia Sistema"] = np.select(condiciones, valores, default="🟡 Revisión Normal")
        
        st.dataframe(df_amfe_edit)
        st.success("Cálculos verificados correctamente.")

# ------------------------------------------
# 3. EVALUADOR DE ISHIKAWA
# ------------------------------------------
with tab_ishikawa:
    st.header("Diagrama Causa-Efecto (Ishikawa)")
    st.write("Verifica que las causas identificadas están redactadas como hechos verificables y no como juicios de valor.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        categoria = st.selectbox("Categoría (6M):", ["Materiales", "Mano de obra", "Maquinaria", "Métodos", "Mantenimiento", "Medio ambiente"])
    with col2:
        causa_input = st.text_input("Redacción de la causa:", placeholder="Ej: Tinta con viscosidad inferior a 2000 cP")
        
    if st.button("Evaluar Causa"):
        if causa_input:
            prompt_ishikawa = f"""Eres un evaluador de calidad industrial. Evalúa esta causa clasificada en la categoría '{categoria}'. 
            Verifica que no contenga juicios de valor vagos como 'malo', 'desastre', 'negligencia' o 'poco'. 
            Debe ser un hecho técnico y observable (ej. 'par de apriete no controlado'). Si está mal, sugiere cómo corregirlo. Si está bien, confírmalo."""
            
            with st.spinner("Analizando redacción..."):
                resultado_ish = evaluar_texto_llm(prompt_ishikawa, causa_input)
            st.info(resultado_ish)

# ------------------------------------------
# 4. EVALUADOR DE QFD
# ------------------------------------------
with tab_qfd:
    st.header("Casa de la Calidad (QFD)")
    st.write("El sistema comprobará que has realizado bien las multiplicaciones de los pesos (QUÉ vs CÓMO). Usa 9 (Fuerte), 3 (Media), 1 (Débil) o 0.")
    
    if "df_qfd" not in st.session_state:
        st.session_state.df_qfd = pd.DataFrame({
            "Necesidad (QUÉ)": ["Fácil de limpiar", "Ligero"],
            "Importancia (1-10)": [5, 8],
            "CÓMO 1: Rugosidad": [9, 0],
            "CÓMO 2: Peso total": [0, 9]
        })
    
    df_qfd_edit = st.data_editor(st.session_state.df_qfd, num_rows="dynamic")
    
    if st.button("Verificar Cálculos QFD"):
        try:
            importancias = df_qfd_edit["Importancia (1-10)"].astype(float)
            comos_cols = [col for col in df_qfd_edit.columns if col.startswith("CÓMO")]
            
            resultados = {}
            for col in comos_cols:
                valores_relacion = df_qfd_edit[col].astype(float)
                if not all(valores_relacion.isin([0, 1, 3, 9])):
                    st.warning(f"⚠️ Atención: En '{col}' hay valores distintos a 0, 1, 3 o 9.")
                
                importancia_tecnica = (importancias * valores_relacion).sum()
                resultados[col] = importancia_tecnica
            
            st.write("### 📊 Importancia Técnica Calculada por el Sistema:")
            df_resultados = pd.DataFrame([resultados], index=["Importancia Técnica"])
            st.dataframe(df_resultados)
            st.success("Si los cálculos manuales de tu equipo no coinciden con estos, revisad las sumas ponderadas de la matriz.")
        except Exception as e:
            st.error(f"Error en el cálculo. Asegúrate de que las columnas de números no tengan letras. Detalle: {e}")
