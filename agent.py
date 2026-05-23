import os
from anthropic import Anthropic
from tools import (
    lookup_seguro,
    mapear_especialidad,
    buscar_hospitales,
    calcular_copago,
    rankear_opciones,
    guardar_log
)
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
SYSTEM_PROMPT = """
Eres un asistente de salud de una clínica privada en Guayaquil, Ecuador.

Tu función es ayudar al paciente a entender su costo antes de atenderse.

FLUJO OBLIGATORIO:

1. SIEMPRE primero solicita la cédula del paciente antes de cualquier otra cosa.
2. Usa lookup_seguro para validar si el paciente tiene seguro.
3. Si el paciente NO existe:
   - Indica que no tiene seguro registrado
   - Continúa el flujo como paciente particular (sin seguro, paga 100%)
4. Luego pide el síntoma
5. Usa mapear_especialidad
6. Si confianza < 50%, haz UNA pregunta de aclaración
7. Usa buscar_hospitales
8. Calcula costos:
   - Con seguro → usar copago
   - Sin seguro → paga precio completo
9. Ordena hospitales del más barato al más caro
10. Da recomendación final

FORMATO:

---
Especialidad sugerida: [nombre]

Seguro:
- Si tiene: [nombre] Nivel [nivel]
- Si no tiene: Paciente sin seguro (tarifa particular)

Hospitales:
1. [Hospital] - Pagas: $X - Seguro cubre: $Y
2. ...

Recomendación: [explicación clara]
---

REGLAS:
- Nunca inventes datos
- Siempre usa $
- Responde en español
- Máximo 1 pregunta de aclaración
- Nunca uses asteriscos ** para formato, formato limpio solo con el signo que debé ser del número
"""

TOOLS = [
    {
        "name": "lookup_seguro",
        "description": "Busca el seguro de un paciente por su numero de cedula. Retorna nombre, seguro y nivel del plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cedula": {
                    "type": "string",
                    "description": "Numero de cedula del paciente, ejemplo: 0932001001"
                }
            },
            "required": ["cedula"]
        }
    },
    {
        "name": "mapear_especialidad",
        "description": "Detecta la especialidad medica a partir del sintoma descrito por el paciente en texto libre.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sintoma": {
                    "type": "string",
                    "description": "Descripcion del sintoma en texto libre, ejemplo: me duele el pecho"
                }
            },
            "required": ["sintoma"]
        }
    },
    {
        "name": "buscar_hospitales",
        "description": "Retorna los hospitales de la red que ofrecen una especialidad especifica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_especialidad": {
                    "type": "integer",
                    "description": "ID de la especialidad medica"
                }
            },
            "required": ["id_especialidad"]
        }
    },
    {
        "name": "calcular_copago",
        "description": "Calcula el copago exacto para un seguro y especialidad dados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_seguro": {
                    "type": "integer",
                    "description": "ID del seguro del paciente"
                },
                "id_especialidad": {
                    "type": "integer",
                    "description": "ID de la especialidad medica"
                }
            },
            "required": ["id_seguro", "id_especialidad"]
        }
    },
    {
        "name": "rankear_opciones",
        "description": "Rankea todos los hospitales por copago final de menor a mayor para el paciente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_seguro": {
                    "type": "integer",
                    "description": "ID del seguro del paciente"
                },
                "id_especialidad": {
                    "type": "integer",
                    "description": "ID de la especialidad medica"
                }
            },
            "required": ["id_seguro", "id_especialidad"]
        }
    }
]

def procesar_tool(tool_name: str, tool_input: dict):
    """Ejecuta la tool correcta y retorna el resultado."""
    if tool_name == "lookup_seguro":
        return lookup_seguro(tool_input["cedula"])
    elif tool_name == "mapear_especialidad":
        return mapear_especialidad(tool_input["sintoma"])
    elif tool_name == "buscar_hospitales":
        return buscar_hospitales(tool_input["id_especialidad"])
    elif tool_name == "calcular_copago":
        return calcular_copago(tool_input["id_seguro"], tool_input["id_especialidad"])
    elif tool_name == "rankear_opciones":
        return rankear_opciones(tool_input["id_seguro"], tool_input["id_especialidad"])
    return {"error": f"Tool {tool_name} no encontrada"}

def run_agent(mensaje_usuario: str, historial: list) -> tuple[str, list]:
    """
    Corre el agente con el mensaje del usuario.
    Retorna (respuesta_texto, historial_actualizado)
    """
    # Agregar mensaje del usuario al historial
    historial.append({
        "role": "user",
        "content": mensaje_usuario
    })

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=historial
        )

        # Si Claude quiere usar una tool
        if response.stop_reason == "tool_use":
            # Agregar respuesta de Claude al historial
            historial.append({
                "role": "assistant",
                "content": response.content
            })

            # Procesar cada tool que pidio Claude
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    resultado = procesar_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(resultado)
                    })

            # Agregar resultados al historial
            historial.append({
                "role": "user",
                "content": tool_results
            })

        # Claude termino de responder
        elif response.stop_reason == "end_turn":
            respuesta = ""
            for block in response.content:
                if hasattr(block, "text"):
                    respuesta += block.text

            # Agregar respuesta final al historial
            historial.append({
                "role": "assistant",
                "content": respuesta
            })

            return respuesta, historial

# ── TEST RAPIDO ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== TEST AGENTE ===\n")
    historial = []

    mensajes = [
        "Hola, me duele el pecho y siento palpitaciones",
        "Mi cedula es 0932001001",
    ]

    for msg in mensajes:
        print(f"Paciente: {msg}")
        respuesta, historial = run_agent(msg, historial)
        print(f"Agente: {respuesta}\n")
        print("-" * 60 + "\n")
