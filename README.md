# 🛠️ Evaluador de Diseño de Producto

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Aplicación interactiva desarrollada en **Streamlit** para la autoevaluación y validación metódica de proyectos de ingeniería. 

La herramienta combina lógica matemática estricta con evaluación por **Inteligencia Artificial Multimodelo** para guiarse en el aprendizaje de metodologías clave de diseño industrial y desarrollo de producto.

---

## 🚀 Funcionalidades Principales

La aplicación se divide en 4 módulos metodológicos indispensables en la ingeniería de diseño:

### 1. 📋 Especificaciones de Diseño de Producto (PDS)
- **Evaluación mediante IA:** Analiza semánticamente las especificaciones de diseño.
- **Filtro de Ambigüedad:** Detecta e identifica adjetivos subjetivos o vagos (ej. *"resistente"*, *"fácil de usar"*).
- **Verificación de Métricas:** Comprueba la presencia de valores numéricos, unidades del SI, tolerancias o normativas de verificación (ISO/UNE).

### 2. ⚠️ Análisis Modal de Fallos y Efectos (AMFE)
- **Tabla Dinámica Interactiva:** Entrada y edición directa de componentes, modos de fallo y puntuaciones de Severidad ($S$), Ocurrencia ($O$) y Detección ($D$).
- **Cálculo Automático de Criticidad:**
  $$\text{NPR} = S \times O \times D$$
- **Alertas Automatizadas:** 
  - 🔴 **Acción Urgente:** Si $S \ge 9$ o $\text{NPR} \ge 100$.
  - 🟠 **Prioridad Media-Alta:** Para valores intermedios.
  - 🟢 **Riesgo Aceptable:** Para $\text{NPR} < 50$.

### 3. 🐟 Diagrama Causa-Efecto (Ishikawa)
- **Filtro de Redacción Técnica por IA:** Clasificación por las 6M (*Materiales, Mano de obra, Maquinaria, Métodos, Mantenimiento, Medio ambiente*).
- **Validación Causa-Efecto:** Distingue entre **hechos físicos observables/medibles** y **juicios de valor**, forzando al estudiante a reformular causas objetivas.

### 4. 🏠 Casa de la Calidad (QFD)
- **Gestión Flexibles de Columnas (CÓMOs):** Permite añadir, renombrar y eliminar requisitos técnicos dinámicamente.
- **Matriz QUÉ - CÓMO:** Asignación de relaciones usando la escala metodológica normalizada ($9, 3, 1, 0$).
- **Priorización Técnica:** Cálculo de la **Puntuación Absoluta** y del **Porcentaje de Importancia Relativa (%)** para establecer el Top-5 de especificaciones técnicas prioritarias para el diseño.

---

## ⚙️ Proveedores y Modelos de IA Integrados

La aplicación soporta de forma nativa múltiples proveedores de modelos de lenguaje (LLM) a través de claves de API configurables en la barra lateral:

| Proveedor | API Key / Fuente | Modelos Integrados |
| :--- | :--- | :--- |
| **Google Gemini** | [Google AI Studio](https://aistudio.google.com/) | `gemini-3.8-flash`, `gemini-3.8-live`, `gemini-3.8-live-extended-thinking`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` |
| **NVIDIA NIM** | [NVIDIA Build](https://build.nvidia.com/) | `nvidia/nemotron-3-ultra-550b-a55b`, `nvidia/nemotron-4-340b-instruct` |
| **OpenRouter** | [OpenRouter AI](https://openrouter.ai/) | `nvidia/nemotron-3-ultra-550b-a55b:free`, `stealth/space-bunny-alpha` |
| **Groq** | [Groq Console](https://console.groq.com/) | `openai/gpt-oss-120b`, `openai/gpt-oss-20b` |

---

## 📦 Instalación y Ejecución Local

### Prerrequisitos
Tener instalado **Python 3.9** o superior.

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/cce-ops/Dise-de-producto.git
   cd Dise-de-producto
   ```

2. **Crear y activar un entorno virtual (recomendado):**
   ```bash
   # En macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate

   # En Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   Crea un archivo `requirements.txt` con el siguiente contenido o instálalas directamente:
   ```bash
   pip install streamlit pandas numpy google-generativeai openai
   ```

4. **Ejecutar la aplicación Streamlit:**
   ```bash
   streamlit run app.py
   ```

5. **Abrir en el navegador:**
   La aplicación se desplegará automáticamente en `http://localhost:8501`.

---

## 📂 Estructura del Repositorio

```text
Dise-de-producto/
├── app.py              # Código principal de la aplicación Streamlit
├── README.md           # Documentación del proyecto
└── requirements.txt    # Librerías y dependencias necesarias
```

---


