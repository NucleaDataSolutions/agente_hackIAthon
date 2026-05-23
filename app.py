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

# ── ESTILOS ──────────────────────────────────────────────────
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

📌 Ejemplo: "Mi cédula es 0932001001"

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

# ── FUNCIÓN RENDER ───────────────────────────────────────────
def render_respuesta(respuesta):

    if "Hospitales disponibles" not in respuesta:
        st.markdown(respuesta)
        return

    lines = respuesta.split("\n")

    especialidad = ""
    seguro = ""
    hospitales = []
    recomendacion = ""

    for line in lines:
        if "Especialidad sugerida" in line:
            especialidad = line.split(":")[-1].strip()
        elif "Saludsa" in line or ("Salud" in line and "Seguro" not in line):
            seguro = line.strip().lstrip("- ").strip()
        elif line.strip().startswith(("1.", "2.", "3.")):
            hospitales.append(line.strip())
        elif "Recomendación" in line:
            recomendacion = line.split(":", 1)[-1].strip()

    if not hospitales:
        st.markdown(respuesta)
        return

    # Extraer copagos
    copagos = []
    for h in hospitales:
        match = re.search(r'\$(\d+[\.,]\d{2})', h)
        copagos.append(float(match.group(1).replace(",", ".")) if match else 0)

    max_copago = max(copagos) if copagos else 0

    # Header especialidad
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a6fa8,#2c97de);padding:20px 24px;border-radius:14px;margin-bottom:20px;color:white;">
        <div style="font-size:13px;opacity:0.8;margin-bottom:4px;">Especialidad sugerida</div>
        <div style="font-size:24px;font-weight:700;">🧠 {especialidad}</div>
        <div style="margin-top:8px;font-size:13px;opacity:0.85;">🛡️ Seguro activo: {seguro}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🏥 Hospitales disponibles")

    configs = [
        ("🥇 Mejor opción", "#f0fdf4", "#16a34a", "#dcfce7"),
        ("👍 Alternativa",  "#fffbeb", "#d97706", "#fef3c7"),
        ("💸 Más costoso",  "#fff1f2", "#e11d48", "#ffe4e6"),
    ]

    for i, h in enumerate(hospitales):
        if i >= len(configs):
            break

        titulo, bg, color_acento, badge_bg = configs[i]

        nombre_match = re.match(r'\d+\.\s*([^-]+)', h)
        nombre = nombre_match.group(1).strip() if nombre_match else f"Hospital {i+1}"

        copago = copagos[i] if i < len(copagos) else 0
        ahorro = max_copago - copago
        ahorro_pct = (ahorro / max_copago * 100) if max_copago else 0

        dir_match = re.search(r'(?:Seguro cubre:?\s*[\d.]+\s*)(.+)', h)
        detalle = dir_match.group(1).strip() if dir_match else ""
        detalle_html = f"<div style='font-size:12px;color:#64748b;margin-bottom:8px;'>📍 {detalle}</div>" if detalle else ""

        ahorro_texto = f"💡 Ahorras ${ahorro:.2f} ({ahorro_pct:.0f}%) vs la opción más cara"

        card_html = f"""
        <div style="background:{bg};border:1px solid {badge_bg};border-left:5px solid {color_acento};padding:16px 20px;border-radius:12px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <span style="background:{badge_bg};color:{color_acento};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;">{titulo}</span>
                <span style="font-size:22px;font-weight:800;color:{color_acento};">${copago:.2f}</span>
            </div>
            <div style="font-size:16px;font-weight:700;color:#1e293b;margin-bottom:6px;">🏥 {nombre}</div>
            {detalle_html}
            <div style="background:white;border-radius:8px;padding:6px 10px;margin-top:6px;font-size:13px;color:#475569;">{ahorro_texto}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # Recomendación final
    if recomendacion:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;border-left:5px solid #0284c7;border-radius:12px;padding:16px 20px;margin-top:16px;">
            <div style="font-size:14px;font-weight:700;color:#0284c7;margin-bottom:6px;">🧾 Recomendación del agente</div>
            <div style="font-size:14px;color:#1e3a5f;line-height:1.6;">{recomendacion}</div>
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
