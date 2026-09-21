import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Evaluador de Proyectos - EEBE", layout="wide")
st.title("Evaluador de Proyectos de Diseño (EEBE - UPC)")
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
        return f"⚠️ Error al conectar con Gemini. Verifica la API Key y el modelo. Detalle: {e}"

# ==========================================
# PESTAÑAS DE LA APLICACIÓN
# ==========================================
tab_pds, tab_amfe, tab_ishikawa, tab_qfd = st.tabs(["📋 PDS", "⚠️ AMFE", "🐟 Ishikawa", "🏠 QFD"])

# ------------------------------------------
# 1. EVALUADOR DE PDS
# ------------------------------------------
with tab_pds:
    st.header("Especificaciones de Diseño de Producto (PDS)")
    
    with st.expander("ℹ️ ¿Cómo funciona esta evaluación? (Caja Blanca)"):
        st.write("""
        **Lo que hace el sistema:**
        El modelo de IA analiza semánticamente tu frase buscando dos cosas críticas:
        1. **Ausencia de ambigüedad:** Penaliza adjetivos subjetivos como "fácil", "resistente", "bonito".
        2. **Presencia de métricas:** Busca activamente números, unidades de medida (kg, mm, W), normativas (ISO, UNE) o condiciones de verificación claras.
        """)

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
    
    with st.expander("ℹ️ ¿Cómo funciona este cálculo? (Caja Blanca)"):
        st.write("""
        **Lo que hace el sistema matemáticamente:**
        1. Extrae los valores que has puesto en $S$, $O$ y $D$.
        2. Aplica la fórmula: **$NPR = Severidad \times Ocurrencia \times Detección$**.
        3. Evalúa la criticidad mediante lógica condicional:
           - Si la **Severidad es $\ge 9$** o el **$NPR \ge 100$**, marca **🔴 Acción Urgente**.
           - Si el **$NPR < 50$**, lo considera **🟢 Riesgo Aceptable**.
           - El resto cae en **🟡 Revisión Normal** o **🟠 Prioridad Media-Alta**.
        """)

    st.write("Añade filas según necesites. Pasa el ratón sobre el símbolo **(?)** en las columnas para ver las instrucciones de puntuación.")
    
    if "df_amfe" not in st.session_state:
        st.session_state.df_amfe = pd.DataFrame({
            "Componente": ["Bisagra", "Tornillo"],
            "Modo de fallo": ["Desgaste", "Aflojamiento"],
            "Severidad (S)": [7, 8],
            "Ocurrencia (O)": [4, 5],
            "Detección (D)": [6, 6]
        })
    
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
    st.header("Diagrama Causa-Efecto (Ishikawa)")
    
    with st.expander("ℹ️ ¿Cómo funciona esta evaluación? (Caja Blanca)"):
        st.write("""
        **Lo que hace el sistema:**
        La IA actúa como un filtro de calidad de redacción técnica. Al leer tu causa, escanea si has usado adjetivos que emiten un "juicio de valor" (ej. ineficiente, desastroso, malo). Si los encuentra, te obligará a reformular la causa hacia un **hecho físico, medible u observable** (ej. "el operario no tiene el manual", "el par de apriete no se verifica").
        """)

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
    
    with st.expander("ℹ️ ¿Cómo funciona este cálculo? (Caja Blanca)"):
        st.write("""
        **Lo que hace el algoritmo matemáticamente:**
        Aplica un modelo de **Suma Producto**. 
        Por cada columna de requisitos (CÓMO), el sistema toma el valor de relación que has introducido (0, 1, 3 o 9) y lo multiplica por la "Importancia" del QUÉ correspondiente de esa fila.
        Luego, suma todos esos resultados parciales de la columna para darte la **Importancia Técnica Absoluta**. 
        No importa si evalúas la importancia inicial del 1 al 5, del 1 al 10 o usas valores absolutos mayores; el cálculo priorizará correctamente las columnas más relevantes.
        """)

    st.write("Construye tu matriz gestionando tus propias columnas (CÓMOs) y filas (QUÉs).")
    
    if "df_qfd" not in st.session_state:
        st.session_state.df_qfd = pd.DataFrame({
            "Necesidades (QUÉ)": ["Fácil de limpiar", "Ligero"],
            "Importancia": [5.0, 8.0],
            "CÓMO: Requisito 1": [9, 0],
            "CÓMO: Requisito 2": [0, 9]
        })

    # --- 1. GESTIÓN DE COLUMNAS (CÓMOs) ---
    st.markdown("### 🛠️ 1. Gestión de Requisitos Técnicos (Columnas CÓMO)")
    
    comos_actuales = [col for col in st.session_state.df_qfd.columns if col.startswith("CÓMO:")]
    col_add, col_ren, col_del = st.columns(3)
    
    with col_add:
        st.write("**Añadir nuevo CÓMO**")
        nuevo_como = st.text_input("Nombre de la característica:", placeholder="Ej: Rugosidad (µm)", key="add_como")
        if st.button("➕ Añadir Columna"):
            if nuevo_como:
                nombre_columna = f"CÓMO: {nuevo_como}"
                if nombre_columna not in st.session_state.df_qfd.columns:
                    st.session_state.df_qfd[nombre_columna] = 0
                    st.rerun()
                else:
                    st.warning("Esa característica ya existe.")
                    
    with col_ren:
        st.write("**Renombrar un CÓMO**")
        if comos_actuales:
            como_a_renombrar = st.selectbox("Columna a modificar:", comos_actuales)
            nuevo_nombre = st.text_input("Nuevo nombre:", placeholder="Ej: Nivel sonoro (dB)", key="ren_como")
            if st.button("✏️ Renombrar Columna"):
                if nuevo_nombre:
                    nuevo_nombre_col = f"CÓMO: {nuevo_nombre}"
                    st.session_state.df_qfd.rename(columns={como_a_renombrar: nuevo_nombre_col}, inplace=True)
                    st.rerun()

    with col_del:
        st.write("**Eliminar un CÓMO**")
        if comos_actuales:
            como_a_eliminar = st.selectbox("Columna a borrar:", comos_actuales)
            if st.button("🗑️ Eliminar Columna"):
                if len(comos_actuales) > 1:
                    st.session_state.df_qfd.drop(columns=[como_a_eliminar], inplace=True)
                    st.rerun()
                else:
                    st.error("⚠️ Debe quedar al menos una columna CÓMO en la matriz.")
    
    # --- 2. MATRIZ INTERACTIVA (CUERPO DE LA CASA) ---
    st.markdown("---")
    st.markdown("### 🟦 2. Cuerpo de la Matriz (Relaciones QUÉ - CÓMO)")
    st.write("Puedes **añadir nuevas filas (QUÉs)** haciendo clic en el símbolo `+` en la parte inferior de la tabla. Pasa el ratón sobre los símbolos **(?)** para ver la puntuación.")
    
    config_qfd = {
        "Necesidades (QUÉ)": st.column_config.TextColumn("Necesidades (QUÉ)", help="Escribe la necesidad en el lenguaje del usuario (Ej: 'Que sea seguro')"),
        "Importancia": st.column_config.NumberColumn(
            "Importancia", min_value=0.0, max_value=1000.0, 
            help="Valora cuánto le importa esto al cliente. Puedes usar una escala básica (1-5 o 1-10) o valores avanzados de Importancia Absoluta. El cálculo de los CÓMOs se ajustará automáticamente a tu escala."
        )
    }
    
    for col in st.session_state.df_qfd.columns:
        if col.startswith("CÓMO:"):
            config_qfd[col] = st.column_config.NumberColumn(
                col, min_value=0, max_value=9, 
                help="Relación entre necesidad y requisito técnico. Valores permitidos: \n9 = Fuerte \n3 = Media \n1 = Débil \n0 = Ninguna."
            )
    
    df_qfd_edit = st.data_editor(st.session_state.df_qfd, num_rows="dynamic", column_config=config_qfd, use_container_width=True)
    
    # --- 3. RESULTADOS (BASE DE LA CASA) ---
    st.markdown("### 📊 3. Resultados Técnicos (Base de la Casa)")
    if st.button("Verificar Cálculos QFD y Generar Top-5"):
        try:
            st.session_state.df_qfd = df_qfd_edit
            
            importancias = df_qfd_edit["Importancia"].fillna(0).astype(float)
            comos_cols = [col for col in df_qfd_edit.columns if col.startswith("CÓMO:")]
            
            resultados = {}
            alertas = False
            for col in comos_cols:
                valores_relacion = df_qfd_edit[col].fillna(0).astype(float)
                if not all(valores_relacion.isin([0, 1, 3, 9])):
                    alertas = True
                    st.warning(f"⚠️ Atención: En la columna '{col}' se detectaron valores distintos a 0, 1, 3 o 9. La metodología exige usar esta escala específica.")
                
                importancia_tecnica = (importancias * valores_relacion).sum()
                resultados[col] = importancia_tecnica
            
            df_resultados = pd.DataFrame([resultados], index=["Importancia Técnica Absoluta"]).T
            df_resultados = df_resultados.sort_values(by="Importancia Técnica Absoluta", ascending=False)
            
            if not alertas:
                st.success("✅ Multiplicaciones verificadas con éxito. Escala 9-3-1-0 respetada.")
            
            st.write("**Ranking Técnico (Características más importantes para el usuario):**")
            st.dataframe(df_resultados.T, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error en el cálculo. Revisa que no hayas introducido texto en columnas numéricas. Detalle: {e}")
