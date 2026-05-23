import streamlit as st
import re
from agent import run_agent
from database import init_db

# ── INIT ─────────────────────────────────────────────────────
init_db()

st.set_page_config(
    page_title="Estimador Inteligente de Copago",
    page_icon="🏥",
    layout="centered"
)

# ── ESTILOS PRO ──────────────────────────────────────────────
st.markdown("""
<style>
.header {
    background: linear-gradient(90deg, #1a6fa8, #2c97de);
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    color: white;
    margin-bottom: 20px;
}

.card {
    padding: 16px;
    border-radius: 10px;
    margin-bottom: 12px;
}

.best { background-color: #e8f8f0; border-left: 6px solid #27ae60; }
.mid { background-color: #fff8e6; border-left: 6px solid #f1c40f; }
.worst { background-color: #fdecea; border-left: 6px solid #e74c3c; }

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

# ── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div class="header">
    <h1>🏥 Estimador Inteligente de Copago</h1>
    <p>Descubre cuánto pagarás antes de atenderte</p>
</div>
""", unsafe_allow_html=True)

# ── MENSAJE INICIAL ──────────────────────────────────────────
st.info("""
👋 Primero necesito tu cédula para verificar tu seguro.

📌 Ejemplo:
"Mi cédula es 0932001001"

Luego podrás indicarme tu síntoma y te diré:
- Especialidad médica
- Copago exacto
- Mejor hospital 💰
""")

# ── SESSION STATE ────────────────────────────────────────────
if "historial" not in st.session_state:
    st.session_state.historial = []

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if not st.session_state.mensajes:
    st.session_state.mensajes.append({
        "role": "assistant",
        "content": "👋 Hola, por favor indícame tu número de cédula para comenzar."
    })

# ── FUNCION VISUAL PRO ───────────────────────────────────────
def render_respuesta(respuesta):

    lines = respuesta.split("\n")

    especialidad = ""
    seguro = ""
    hospitales = []

    for line in lines:
        if "Especialidad sugerida" in line:
            especialidad = line
        elif "seguro" in line.lower():
            seguro = line
        elif "-" in line and "Copago" in line:
            hospitales.append(line)

    if especialidad:
        st.markdown(f"### 🧠 {especialidad}")
    if seguro:
        st.markdown(f"### 🛡️ {seguro}")

    st.markdown("### 🏥 Opciones disponibles")

    copagos = []
    for h in hospitales:
        match = re.search(r'\\$(\\d+\\.\\d{2})', h)
        if match:
            copagos.append(float(match.group(1)))

    if not copagos:
        st.warning("No se pudieron procesar los resultados.")
        return

    max_copago = max(copagos)

    for i, h in enumerate(hospitales):

        match = re.search(r'\\$(\\d+\\.\\d{2})', h)
        copago = float(match.group(1)) if match else 0

        ahorro = max_copago - copago
        ahorro_pct = (ahorro / max_copago) * 100 if max_copago else 0

        if i == 0:
            clase = "best"
            titulo = "🥇 Mejor opción"
            extra = f"""
            <br><span class="badge">Ahorras {ahorro_pct:.0f}% (${ahorro:.2f})</span>
            <br>✔ Es la opción más económica disponible.
            """
        elif i == 1:
            clase = "mid"
            titulo = "👍 Alternativa"
            extra = f"<br>Ahorro: {ahorro_pct:.0f}% vs la más cara."
        else:
            clase = "worst"
            titulo = "💸 Más costoso"
            extra = "<br>❗ Mayor costo en la red."

        h_html = re.sub(
            r'\\$(\\d+\\.\\d{2})',
            r'<span class="money">$\1</span>',
            h
        )

        st.markdown(f"""
        <div class="card {clase}">
            <strong>{titulo}</strong><br>
            {h_html}
            {extra}
        </div>
        """, unsafe_allow_html=True)

# ── CHAT ─────────────────────────────────────────────────────
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── INPUT ────────────────────────────────────────────────────
if prompt := st.chat_input("Escribe aquí..."):

    st.session_state.mensajes.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Procesando..."):
            try:
                respuesta, st.session_state.historial = run_agent(
                    prompt,
                    st.session_state.historial
                )
                respuesta = respuesta.replace("`", "")

                render_respuesta(respuesta)

                st.session_state.mensajes.append({
                    "role": "assistant",
                    "content": respuesta
                })

            except Exception as e:
                st.error("❌ Ocurrió un error. Intenta nuevamente.")
                print(e)

# ── RESET ────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Nueva consulta"):
    st.session_state.historial = []
    st.session_state.mensajes = []
    st.rerun()
