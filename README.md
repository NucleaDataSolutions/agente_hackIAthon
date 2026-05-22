# 🏥 Estimador Agéntico de Copago y Cobertura

Agente conversacional que ayuda al paciente a entender su beneficio de seguro
antes de atenderse. Desarrollado para el **hackIAthon - Viamatica 2025**.

## ¿Qué hace?

El paciente describe su síntoma en lenguaje natural y el agente:

1. Identifica al paciente por cédula
2. Detecta la especialidad médica según el síntoma
3. Consulta su plan de seguro
4. Calcula el copago exacto en cada hospital de la red
5. Recomienda el hospital más económico

## Especialidades disponibles

| Especialidad | Síntomas de ejemplo |
|---|---|
| Cardiología | dolor de pecho, palpitaciones, taquicardia |
| Oftalmología | vista borrosa, dolor de ojos, lagrimeo |
| Traumatología | rodilla, fractura, esguince, columna |
| Medicina General | fiebre, gripe, tos, garganta |
| Gastroenterología | gastritis, reflujo, náusea, diarrea |

## Pacientes de prueba

| Paciente | Cédula | Seguro | Copago |
|---|---|---|---|
| Enrique Calle | 0932001001 | Saludsa Nivel 3 | 20% |
| Cristhian Gallegos | 0932001002 | Saludsa Nivel 4 | 10% |
| Kenny Pizarro | 0932001003 | Ecuasanitas Nivel 2 | 30% |

## Stack tecnológico

- **Agente IA:** Claude claude-sonnet-4-5 (Anthropic) + LangGraph
- **Frontend:** Streamlit
- **Base de datos:** SQLite + SQLAlchemy
- **Deploy:** Streamlit Cloud

## Estructura del proyecto

    agente_hackIAthon/
      app.py           # Interfaz Streamlit
      agent.py         # Agente Claude + orquestación de tools
      tools.py         # 5 herramientas de consulta a la BD
      database.py      # Tablas SQLite + datos reales Guayaquil
      data/
        hospital.db    # Base de datos SQLite
      requirements.txt
      .env.example

## Cómo correr localmente

```bash
git clone https://github.com/TU_USUARIO/hackiathon-reto3
cd hackiathon-reto3
pip install -r requirements.txt
cp .env.example .env
# Agrega tu ANTHROPIC_API_KEY en .env
streamlit run app.py
```

## Hospitales en la red

- Clínica Kennedy — Av. Rodolfo Baquerizo Nazur, Alborada
- Omni Hospital — Av. Abel Castillo y Juan Tanca Marengo  
- Clínica Alcívar — Coronel 2301 y Azuay, Torre 1

## Equipo

Desarrollado por **Enrique Calle** y **Cristhian Gallegos** — Nuclea Data Solutions