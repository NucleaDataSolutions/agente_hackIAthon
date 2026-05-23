import streamlit as st
import re
from agent import run_agent
from database import init_db

init_db()

st.set_page_config(
    page_title="Estimador de Copago",
    page_icon="🏥",
    layout="centered"
)

# ── ESTILOS ───────────────────────────────────────────────
st.markdown("""
<style>

.main {
    background-color: #f7f9fc;
}

.header {
    background: linear-gradient(90deg, #1a6fa8, #2c97de);
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    color: white;
    margin-bottom: 20px;
}

.card {
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 12px;
    color: #1a1a1a;
}

.best {
    background-color: #e8f8f0;
    border-left: 6px solid #27ae60;
}

.mid {
    background-color: #fff8e6;
    border-left: 6px solid #f1c40f;
}

.worst {
    background-color: #fdecea;
    border-left: 6px solid #e74c3c;
}

.money {
    color: #27ae60;
    font-weight: bold;
}

.badge {
    background-color: #27ae60;
    color: white;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────
st.markdown("""
<div class="header">
    <h1>🏥 Estimador Inteligente de Copago</h1>
    <p>Elige la mejor opción médica según tu seguro</p>
</div>
""", unsafe_allow_html=True)

st.info("💡 Describe tu síntoma y te diremos cuánto pagarás y dónde te conviene atenderte.")

# ── SESSION ──────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if not st.session_state.mensajes:
    st.session_state.mensajes.append({
        "role": "assistant",
        "content": "👋 Hola, soy tu asistente de salud. Cuéntame tu síntoma."
    })

# ── FUNCION PRINCIPAL ────────────────────────────────────
def render_respuesta(respuesta):

    lines = respuesta.split("\n")

    especialidad = ""
    seguro = ""
    hospitales = []

    for line in lines:
        if "Especialidad sugerida" in line:
            especialidad = line
        elif "Tu seguro" in line:
            seguro = line
        elif "-" in line and "Copago" in line:
            hospitales.append(line)

    st.markdown(f"### 🧠 {especialidad}")
    st.markdown(f"### 🛡️ {seguro}")
    st.markdown("### 🏥 Opciones disponibles")

    # Extraer copagos numéricos
    copagos = []
    for h in hospitales:
        match = re.search(r'\\$(\\d+\\.\\d{2})', h)
        if match:
            copagos.append(float(match.group(1)))

    if not copagos:
        return

    max_copago = max(copagos)
    min_copago = min(copagos)

    for i, h in enumerate(hospitales):

        copago_match = re.search(r'\\$(\\d+\\.\\d{2})', h)
        copago = float(copago_match.group(1)) if copago_match else 0

        ahorro = max_copago - copago
        ahorro_pct = (ahorro / max_copago) * 100 if max_copago > 0 else 0

        if i == 0:
            clase = "best"
            titulo = "🥇 Mejor opción"
            recomendacion = f"""
            <br><span class="badge">Ahorras {ahorro_pct:.0f}% (${ahorro:.2f}) vs la opción más cara</span>
            <br>✔ Te conviene porque es el menor copago disponible en la red.
            """
        elif i == 1:
            clase = "mid"
            titulo = "👍 Alternativa"
            recomendacion = f"""
            <br>Ahorras {ahorro_pct:.0f}% comparado con la más cara.
            """
        else:
            clase = "worst"
            titulo = "💸 Más costoso"
            recomendacion = "<br>❗ Es la opción con mayor copago."

        # Colorear dinero
        h_html = re.sub(
            r'\\$(\\d+\\.\\d{2})',
            r'<span class="money">$\1</span>',
            h
        )

        st.markdown(f"""
        <div class="card {clase}">
            <strong>{titulo}</strong><br>
            {h_html}
            {recomendacion}
        </div>
        """, unsafe_allow_html=True)


# ── CHAT ────────────────────────────────────────────────
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Escribe tu síntoma..."):

    st.session_state.mensajes.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Analizando síntoma..."):
            respuesta, st.session_state.historial = run_agent(
                prompt,
                st.session_state.historial
            )

        respuesta_limpia = respuesta.replace("`", "")
        render_respuesta(respuesta_limpia)

        st.session_state.mensajes.append({
            "role": "assistant",
            "content": respuesta_limpia
        })

# ── RESET ───────────────────────────────────────────────
st.divider()
if st.button("🔄 Nueva consulta"):
    st.session_state.historial = []
    st.session_state.mensajes = []
    st.rerun()
