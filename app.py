import os
import time
import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# -----------------------------------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS DE LECTURA E IA
# -----------------------------------------------------------------------------
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y CONSTANTES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Evaluación Académica con IA",
    page_icon="🎓",
    layout="wide"
)

# ⚠️ PEGA AQUÍ EL ID DE TU CARPETA DE GOOGLE DRIVE ANTES DE SUBIRLO A GITHUB
DRIVE_FOLDER_ID = "PEGA_AQUI_TU_FOLDER_ID" 

FORMATOS_SOPORTADOS = ["pdf", "pptx", "xlsx", "xls", "csv", "docx", "txt", "py", "m"]

# Opciones de modelos solicitados
MODELOS_GEMINI = {
    "Gemini 3.8 Flash (Recomendado)": "gemini-3.8-flash",
    "Gemini 3.8 Live": "gemini-3.8-live",
    "Gemini 3.8 Live Extended Thinking": "gemini-3.8-live-extended-thinking",
    "Gemini 3.7 Flash": "gemini-3.7-flash",
    "Gemini 3.6 Flash": "gemini-3.6-flash",
    "Gemini 3.5 Flash": "gemini-3.5-flash",
    "Gemini 3.5 Flash-Lite": "gemini-3.5-flash-lite",
    "Gemini 3.1 Flash-Lite": "gemini-3.1-flash-lite"
}

# -----------------------------------------------------------------------------
# CONEXIÓN A GOOGLE DRIVE Y EXTRACCIÓN DE TEXTO
# -----------------------------------------------------------------------------
def obtener_servicio_drive():
    """Autentica con Google Drive en local (JSON) o en la nube (Secrets)."""
    try:
        if os.path.exists("credenciales_drive.json"):
            creds = service_account.Credentials.from_service_account_file(
                "credenciales_drive.json", scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
        elif "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
        else:
            st.error("No se encontraron credenciales. Falta 'credenciales_drive.json' o configurar los Secrets.")
            return None
            
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Error de credenciales de Drive: {str(e)}")
        return None

def procesar_archivo_path_o_bytes(file_obj, filename_hint=""):
    """Extrae el texto de un archivo independientemente de su formato."""
    nombre = (filename_hint if filename_hint else getattr(file_obj, "name", str(file_obj))).lower()
    
    if nombre.endswith(".pdf") and HAS_PYPDF:
        reader = pypdf.PdfReader(file_obj)
        texto = ""
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt:
                texto += f"\n--- PÁGINA {i+1} ---\n" + txt
        return texto
    elif nombre.endswith(".docx") and HAS_DOCX:
        doc = docx.Document(file_obj)
        return "\n".join([p.text for p in doc.paragraphs if p.text])
    elif nombre.endswith((".xlsx", ".xls")) and HAS_PANDAS:
        excel_file = pd.ExcelFile(file_obj)
        texto = ""
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            texto += f"\n--- HOJA: {sheet_name} ---\n" + df.to_string(index=False) + "\n"
        return texto
    return "Contenido procesado (formato de texto plano u otros soportados)."

@st.cache_resource(ttl=3600) # Refresca Google Drive cada hora para no saturar la API
def cargar_materiales_drive():
    """Descarga los archivos de Drive a la memoria y extrae el texto."""
    base_conocimiento = {}
    servicio = obtener_servicio_drive()
    
    if not servicio:
        return base_conocimiento
        
    try:
        resultados = servicio.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name, mimeType)"
        ).execute()
        archivos = resultados.get('files', [])

        for archivo in archivos:
            extension = archivo['name'].split(".")[-1].lower()
            if extension in FORMATOS_SOPORTADOS:
                request = servicio.files().get_media(fileId=archivo['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                fh.seek(0)
                fh.name = archivo['name'] 
                texto = procesar_archivo_path_o_bytes(fh, filename_hint=archivo['name'])
                base_conocimiento[archivo['name']] = texto
                
        return base_conocimiento
    except Exception as e:
        st.error(f"Error al sincronizar con Google Drive: {str(e)}")
        return base_conocimiento

# -----------------------------------------------------------------------------
# ESTADO DE LA SESIÓN Y FUNCIONES DE IA
# -----------------------------------------------------------------------------
if "base_conocimiento" not in st.session_state:
    st.session_state.base_conocimiento = cargar_materiales_drive()

def obtener_contexto_asignatura():
    if not st.session_state.base_conocimiento:
        return "No hay materiales subidos. Se evaluará con criterios generales."
    contexto = "=== MATERIALES Y RÚBRICAS OFICIALES DE LA ASIGNATURA ===\n\n"
    for nombre_file, contenido in st.session_state.base_conocimiento.items():
        contexto += f"--- DOCUMENTO DOCENTE: {nombre_file} ---\n{contenido}\n\n"
    return contexto

def consultar_gemini_con_reintentos(prompt_sistema, prompt_usuario, api_key, model_id_principal):
    if not api_key:
        return "⚠️ Introduce tu API Key de Gemini."
    if not HAS_GEMINI:
        return "⚠️ La librería 'google-genai' no está instalada."
        
    client = genai.Client(api_key=api_key.strip())
    contenido_completo = f"{prompt_sistema}\n\nENTRADA DEL USUARIO / TRABAJO ENTREGADO:\n{prompt_usuario}"
    
    # Cascada de supervivencia: si falla el principal, intenta progresivamente con los modelos de respaldo
    modelos_a_probar = [
        model_id_principal, 
        "gemini-3.8-flash", 
        "gemini-3.7-flash", 
        "gemini-3.6-flash", 
        "gemini-3.5-flash", 
        "gemini-3.5-flash-lite", 
        "gemini-3.1-flash-lite"
    ]
    modelos_a_probar = list(dict.fromkeys(modelos_a_probar)) # Eliminar duplicados si el seleccionado ya está en la lista
    
    for modelo_actual in modelos_a_probar:
        for intento in range(2): 
            try:
                response = client.models.generate_content(
                    model=modelo_actual,
                    contents=contenido_completo,
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                return response.text
            except Exception as e:
                error_str = str(e).lower()
                # Si el error es de cuota agotada o límite de peticiones (429), salta al siguiente modelo
                if "429" in error_str or "quota" in error_str or "exhausted" in error_str:
                    break 
                
                # Si es un error temporal de servidor (503), espera 2 segundos e reintenta
                if intento < 1:
                    time.sleep(2)
                    continue

    return "⚠️ Los servidores de IA están saturados en este momento. Por favor, espera unos minutos e inténtalo de nuevo."

# -----------------------------------------------------------------------------
# INTERFAZ WEB PRINCIPAL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key_env = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key (Oculta):", value=api_key_env, type="password")
    modelo_label = st.selectbox("Modelo Principal:", options=list(MODELOS_GEMINI.keys()), index=0)
    modelo_seleccionado = MODELOS_GEMINI[modelo_label]
    st.markdown("*(El sistema cambiará automáticamente a modelos más ligeros si los servidores se saturan).*")

st.title("🎓 Plataforma Integrada de Evaluaciones Académicas")
st.markdown("Evaluación automática basada en los materiales de Google Drive del profesor.")

tab_rubrica, tab_evaluador = st.tabs([
    "📋 Paso 1: Lista de Cotejo",
    "📤 Paso 2: Entrega y Feedback"
])

with tab_rubrica:
    st.subheader("Verificación Previa a la Entrega")
    req1 = st.checkbox("Estructura adecuada según la guía docente.")
    req2 = st.checkbox("Uso correcto de la metodología explicada en clase.")
    if req1 and req2:
        st.success("✅ ¡Lista completada! Procede al Paso 2.")

with tab_evaluador:
    st.subheader("Envío de Tareas y Documentos")
    
    if st.session_state.base_conocimiento:
        st.info(f"📚 **Materiales sincronizados desde Drive:** {len(st.session_state.base_conocimiento)} archivo(s)")
        
        with st.expander("💡 ¿No ves un documento recién subido por el profesor?"):
            st.markdown("""
            Para no saturar el sistema, la aplicación revisa si hay nuevos materiales en la nube de forma periódica. 
            Si el equipo docente acaba de subir un documento y necesitas evaluarte ahora mismo:
            1. Haz clic en los **tres puntos (`⋮`)** o en **Manage app** arriba a la derecha de esta web.
            2. Selecciona **`Clear cache`**.
            3. La página se recargará y los nuevos archivos de la asignatura aparecerán sincronizados al instante.
            """)
    else:
        st.warning("⚠️ No se han detectado archivos en la carpeta de Drive.")

    archivos_alumno = st.file_uploader(
        "Sube tus entregables (PDF, DOCX, Excel):", 
        type=FORMATOS_SOPORTADOS, accept_multiple_files=True
    )

    if st.button("🚀 Analizar Tareas", type="primary"):
        if archivos_alumno:
            contenido_estudiante = ""
            for arch in archivos_alumno:
                txt_arch = procesar_archivo_path_o_bytes(arch)
                contenido_estudiante += f"\n=== ENTREGABLE: {arch.name} ===\n" + txt_arch + "\n\n"

            with st.spinner(f"Analizando entregables con {modelo_seleccionado}..."):
                contexto_docente = obtener_contexto_asignatura()
                system_prompt_evaluador = f"""
                Eres un evaluador académico objetivo.
                MATERIALES DE LA ASIGNATURA Y RÚBRICAS: {contexto_docente}

                REGLAS ESTRICTAS DE EVALUACIÓN:
                1. Evalúa ÚNICAMENTE basándote en los criterios explícitos de los MATERIALES DE LA ASIGNATURA proporcionados.
                2. NO inventes criterios de evaluación, normativas, ni penalizaciones que no aparezcan en los documentos del docente.
                3. Si la rúbrica no especifica un criterio (ej. formato, ortografía, extensión), no lo evalúes ni lo menciones.
                4. Si no estás seguro de si el alumno ha cumplido un punto porque su texto es ambiguo, indícalo como una "sugerencia de revisión" en lugar de darlo por incorrecto.

                Estructura el feedback en Markdown con: Resumen, Calificación, Fortalezas, y Correcciones necesarias.
                """
                resultado = consultar_gemini_con_reintentos(system_prompt_evaluador, contenido_estudiante, api_key, modelo_seleccionado)

            st.markdown("---")
            st.markdown("## 📊 Informe de Retroalimentación Automática")
            st.markdown(resultado)
        else:
            st.error("Sube al menos un archivo para evaluar.")
