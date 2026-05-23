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

    # Si aún no hay resultado final → mostrar normal
    if "Hospitales disponibles" not in respuesta:
        st.markdown(respuesta)
        return

    import re

    lines = respuesta.split("\n")

    especialidad = ""
    seguro = ""
    hospitales = []
    recomendacion = ""

    # ── PARSEO ─────────────────────────────
    for line in lines:
        if "Especialidad sugerida" in line:
            especialidad = line.split(":")[-1].strip()

        elif "Seguro" in line:
            seguro = line.replace("Seguro:", "").strip()

        elif line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3."):
            hospitales.append(line)

        elif "Recomendación" in line:
            recomendacion = line.replace("Recomendación:", "").strip()

    # ── HEADER ─────────────────────────────
    st.markdown(f"## 🧠 {especialidad}")
    st.markdown(f"🛡️ {seguro}")

    st.markdown("---")

    # ── EXTRAER COPAGOS ────────────────────
    copagos = []
    for h in hospitales:
        match = re.search(r'\$(\d+\.\d{2})', h)
        if match:
            copagos.append(float(match.group(1)))

    if not copagos:
        st.markdown(respuesta)
        return

    max_copago = max(copagos)

    # ── CARDS ──────────────────────────────
    for i, h in enumerate(hospitales):

        nombre = h.split("-")[0].split(".")[-1].strip()

        match = re.search(r'\$(\d+\.\d{2})', h)
        copago = float(match.group(1)) if match else 0

        ahorro = max_copago - copago
        ahorro_pct = (ahorro / max_copago) * 100 if max_copago else 0

        if i == 0:
            titulo = "🥇 Mejor opción"
            color = "#e8f8f0"
        elif i == 1:
            titulo = "👍 Alternativa"
            color = "#fff8e6"
        else:
            titulo = "💸 Más costoso"
            color = "#fdecea"

        st.markdown(f"""
        <div style="
            background:{color};
            padding:15px;
            border-radius:10px;
            margin-bottom:12px;
        ">
            <strong>{titulo}</strong><br><br>

            🏥 <strong>{nombre}</strong><br>

            💰 Pagas: <span style="color:#27ae60;font-weight:bold;">${copago:.2f}</span><br>

            💡 Ahorras: {ahorro_pct:.0f}% (${ahorro:.2f})<br>
        </div>
        """, unsafe_allow_html=True)

    # ── RECOMENDACIÓN FINAL ─────────────────
    if recomendacion:
        st.markdown("### 🧾 Recomendación")
        st.markdown(f"""
<div style="
    background: linear-gradient(90deg, #e8f8f0, #f4f6f7);
    padding:18px;
    border-radius:12px;
    border:1px solid #d5f5e3;
">
    <div style="font-size:16px;font-weight:bold;color:#1e8449;">
        💡 Recomendación inteligente
    </div>
    <div style="margin-top:8px;">
        {recomendacion}
    </div>
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
                # Limpieza agresiva de formato feo de Claude
                respuesta = (
                    respuesta
                    .replace("`", "")
                    .replace("**", "")
                    .replace("*", "")
                )

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
