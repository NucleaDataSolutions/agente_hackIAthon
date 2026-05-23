 
import streamlit as st
from agent import run_agent
from database import init_db

# Inicializar BD al arrancar
init_db()

# ── CONFIGURACION DE PAGINA ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Estimador de Copago",
    page_icon="🏥",
    layout="centered"
)

# ── ESTILOS ──────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .header-box {
            background-color: #1a6fa8;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        .header-box h1 {
            color: white;
            font-size: 28px;
            margin: 0;
        }
        .header-box p {
            color: #d0e8f5;
            margin: 6px 0 0;
            font-size: 14px;
        }
        .info-box {
            background-color: #eaf4fb;
            border-left: 4px solid #1a6fa8;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #1a3a4a;
        }
    </style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="header-box">
        <h1>🏥 Estimador de Copago y Cobertura</h1>
        <p>Consulta cuanto pagarias antes de atenderte en la red de hospitales</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="info-box">
        💡 <strong>Como funciona:</strong> Describe tu sintoma, ingresa tu cedula
        y el agente te indicara la especialidad sugerida, el copago exacto
        y los hospitales disponibles ordenados del mas economico al mas costoso.
    </div>
""", unsafe_allow_html=True)

# ── CEDULAS DE PRUEBA ─────────────────────────────────────────────────────────
with st.expander("📋 Cedulas de prueba disponibles"):
    st.markdown("""
    | Paciente | Cedula | Seguro | Nivel |
    |---|---|---|---|
    | Enrique Calle | 0932001001 | Saludsa | 3 - Plus (copago 20%) |
    | Cristhian Gallegos | 0932001002 | Saludsa | 4 - Premium (copago 10%) |
    | Kenny Pizarro | 0932001003 | Ecuasanitas | 2 - Estandar (copago 30%) |
    """)

# ── ESTADO DE SESION ─────────────────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []

if "mensajes_ui" not in st.session_state:
    st.session_state.mensajes_ui = []

# Mensaje de bienvenida
if not st.session_state.mensajes_ui:
    st.session_state.mensajes_ui.append({
        "role": "assistant",
        "content": "👋 Hola, soy tu asistente de salud. Describeme tu sintoma y te ayudo a conocer tu copago y los hospitales disponibles en tu red."
    })

# ── CHAT ─────────────────────────────────────────────────────────────────────
for msg in st.session_state.mensajes_ui:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu sintoma o responde al agente..."):

    # Mostrar mensaje del usuario
    st.session_state.mensajes_ui.append({
        "role": "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    # Llamar al agente
    
    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            respuesta, st.session_state.historial = run_agent(
                prompt,
                st.session_state.historial
            )
        # Limpiar backticks que Claude puede generar
        import re
        respuesta_limpia = respuesta.replace("`", "")

        # Reemplazar saltos de linea para HTML
        respuesta_html = respuesta_limpia.replace("\n", "<br>")

        # Colorear todos los numeros decimales como dolares
        respuesta_html = re.sub(
            r'\$?(\d+\.\d{2})',
            r'<span style="color:#27ae60;font-weight:bold;">$\1</span>',
            respuesta_html
        )

        st.html(f"<div style='font-size:15px;line-height:1.8;'>{respuesta_html}</div>")

        st.session_state.mensajes_ui.append({
            "role": "assistant",
            "content": respuesta
        })

# ── BOTON LIMPIAR ─────────────────────────────────────────────────────────────
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Nueva consulta", use_container_width=True):
        st.session_state.historial = []
        st.session_state.mensajes_ui = []
        st.rerun()
