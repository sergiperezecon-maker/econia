import streamlit as st
import requests
from duckduckgo_search import DDGS
import os
from datetime import date

st.set_page_config(
    page_title="EconIA — Inteligencia Económica",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, .stApp {
        background-color: #080808;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #111 !important;
        color: #e0e0e0 !important;
        border: 1px solid #222 !important;
        border-radius: 6px !important;
        font-size: 0.95rem !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #444 !important;
        box-shadow: none !important;
    }
    .stButton > button {
        background-color: #e0e0e0 !important;
        color: #080808 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px !important;
        padding: 0.6rem 1.5rem !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    .stSelectbox > div > div {
        background-color: #111 !important;
        border: 1px solid #222 !important;
        color: #e0e0e0 !important;
        border-radius: 6px !important;
    }
    .stSpinner > div { border-top-color: #e0e0e0 !important; }
    .stExpander { background-color: #0d0d0d !important; border: 1px solid #1a1a1a !important; border-radius: 6px !important; }
    [data-testid="stCodeBlock"] pre { background-color: #0d0d0d !important; border: 1px solid #1a1a1a !important; }
    .divider { border-top: 1px solid #1a1a1a; margin: 1.5rem 0; }
    .counter-free    { color: #888; font-size: 0.8rem; }
    .counter-warning { color: #ffaa00; font-size: 0.8rem; }
    .counter-empty   { color: #ff5252; font-size: 0.8rem; }
    .premium-badge {
        background: linear-gradient(90deg, #1a1400, #2a2000);
        border: 1px solid #5a4500;
        color: #ffcc44;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .result-box {
        background-color: #0d0d0d;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 1.5rem;
        line-height: 1.75;
        font-size: 0.95rem;
    }
    .source-item { color: #444; font-size: 0.78rem; margin-top: 0.3rem; }
    .category-pill {
        display: inline-block;
        background: #111;
        border: 1px solid #222;
        color: #888;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

FREE_LIMIT = 5

CATEGORIES = {
    "Economía España":    "economia españa inflación desempleo PIB política fiscal",
    "Europa y BCE":       "zona euro banco central europeo tipos interés eurozona",
    "Economía Global":    "economia mundial reserva federal dólar china mercados",
    "Geopolítica":        "geopolitica conflictos internacionales sanciones comercio",
    "Mercados y Bolsa":   "bolsa mercados financieros acciones inversión",
    "Criptomonedas":      "bitcoin criptomonedas blockchain defi web3",
}


def init_session():
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
        st.session_state.query_date = date.today()
        st.session_state.is_premium = False
        st.session_state.last_result = None
        st.session_state.last_sources = []
    if st.session_state.query_date != date.today():
        st.session_state.query_count = 0
        st.session_state.query_date = date.today()


def get_api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def get_premium_codes() -> list:
    try:
        raw = st.secrets.get("PREMIUM_CODES", "")
        return [c.strip().upper() for c in raw.split(",") if c.strip()]
    except Exception:
        return []


def queries_remaining() -> int:
    if st.session_state.is_premium:
        return 9999
    return max(0, FREE_LIMIT - st.session_state.query_count)


def search_web(query: str, category_context: str = "") -> tuple[str, list]:
    full_query = f"{query} {category_context}".strip()
    sources = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(full_query, max_results=6, region="es-es"))
        if not results:
            with DDGS() as ddgs:
                results = list(ddgs.text(full_query, max_results=6))
        parts = []
        for r in results:
            parts.append(
                f"Título: {r.get('title','')}\n"
                f"Contenido: {r.get('body','')}\n"
                f"URL: {r.get('href','')}"
            )
            if r.get("href"):
                sources.append({"title": r.get("title",""), "url": r.get("href","")})
        return "\n\n---\n\n".join(parts), sources
    except Exception as e:
        return f"Error al buscar: {e}", []


def analyze(question: str, category: str, api_key: str) -> tuple[str, list]:
    context, sources = search_web(question, CATEGORIES.get(category, ""))

    prompt = f"""Eres EconIA, un analista económico y geopolítico de élite.
Respondes en español, con claridad y precisión. Tu estilo es directo, sin rodeos, con autoridad.
No eres una IA genérica — eres un experto que habla como si explicara algo importante a alguien inteligente.

CATEGORÍA DE LA CONSULTA: {category}

DATOS DE INTERNET (úsalos para basar tu respuesta en hechos reales actuales):
{context}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES:
- Responde en 3-5 párrafos bien estructurados
- Empieza con el dato o hecho más importante, sin introducción genérica
- Usa **negritas** para los datos clave
- Si hay números o fechas relevantes, inclúyelos
- Al final, incluye una sección "**Lo que esto significa**:" con las implicaciones prácticas en 2-3 puntos
- No digas "según mis datos" ni "como IA" — habla con autoridad directa
- Si la pregunta tiene implicación geopolítica, analiza también el impacto en España y Europa"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload, timeout=30)
    if not resp.ok:
        raise ValueError(f"Error {resp.status_code}: {resp.text}")
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return text, sources


# ─── UI ────────────────────────────────────────────────────────────────────────

init_session()
api_key = get_api_key()

# Header
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown("# EconIA")
    st.markdown("<p style='color:#444; margin-top:-0.8rem; font-size:0.9rem;'>Inteligencia económica y geopolítica en tiempo real</p>", unsafe_allow_html=True)
with col_badge:
    if st.session_state.is_premium:
        st.markdown("<br><span class='premium-badge'>PREMIUM</span>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Premium unlock (sidebar-style expander)
with st.expander("🔓 Código Premium — consultas ilimitadas"):
    code_input = st.text_input("", placeholder="Introduce tu código", label_visibility="collapsed")
    if st.button("Activar", key="activate"):
        valid_codes = get_premium_codes()
        if code_input.strip().upper() in valid_codes:
            st.session_state.is_premium = True
            st.success("Acceso premium activado. Consultas ilimitadas.")
            st.rerun()
        else:
            st.error("Código incorrecto.")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Query counter
remaining = queries_remaining()
if st.session_state.is_premium:
    st.markdown("<span class='premium-badge'>PREMIUM · ILIMITADO</span>", unsafe_allow_html=True)
elif remaining > 2:
    st.markdown(f"<p class='counter-free'>Consultas gratuitas restantes hoy: {remaining}/{FREE_LIMIT}</p>", unsafe_allow_html=True)
elif remaining > 0:
    st.markdown(f"<p class='counter-warning'>⚠ Solo te quedan {remaining} consultas hoy.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p class='counter-empty'>Has agotado tus consultas gratuitas de hoy. Vuelve mañana o activa un código premium.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Category + Question
category = st.selectbox(
    "Categoría",
    options=list(CATEGORIES.keys()),
    label_visibility="visible"
)

question = st.text_area(
    "Tu pregunta",
    height=120,
    placeholder="¿Qué está pasando con la inflación en España? ¿Qué implica la subida de tipos del BCE para las hipotecas? ¿Cómo afecta el conflicto en Oriente Medio al precio del petróleo?",
    label_visibility="collapsed"
)

ask_button = st.button("Analizar", use_container_width=True, disabled=(remaining == 0 and not st.session_state.is_premium))

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Process
if ask_button:
    if not api_key:
        st.error("API Key no configurada. Contacta con el administrador.")
    elif not question.strip():
        st.warning("Escribe una pregunta.")
    else:
        with st.spinner("Analizando datos en tiempo real..."):
            result, sources = analyze(question.strip(), category, api_key)

        if not st.session_state.is_premium:
            st.session_state.query_count += 1

        st.session_state.last_result = result
        st.session_state.last_sources = sources

# Show result
if st.session_state.last_result:
    st.markdown(f"<span class='category-pill'>{category}</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='result-box'>{st.session_state.last_result}</div>", unsafe_allow_html=True)

    if st.session_state.last_sources:
        with st.expander("🔗 Fuentes consultadas"):
            for s in st.session_state.last_sources[:5]:
                st.markdown(f"<div class='source-item'>→ <a href='{s['url']}' target='_blank' style='color:#555; text-decoration:none;'>{s['title']}</a></div>", unsafe_allow_html=True)

# Footer
st.markdown("<br><br>")
st.markdown("<p style='color:#222; font-size:0.75rem; text-align:center;'>EconIA · Datos en tiempo real · Impulsado por Gemini</p>", unsafe_allow_html=True)
