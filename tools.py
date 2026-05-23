import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "hospital.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── TOOL 1 ───────────────────────────────────────────────────────────────────
def lookup_seguro(cedula: str) -> dict:
    """Busca el seguro de un paciente por cedula."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id_cliente, c.nombre, c.correo,
               s.id_seguro, s.nombre_seguro, s.nivel_seguro
        FROM cliente c
        JOIN seguros s ON c.id_seguro = s.id_seguro
        WHERE c.cedula = ?
    """, (cedula,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"No se encontro paciente con cedula {cedula}"}

    return {
        "id_cliente":    row["id_cliente"],
        "nombre":        row["nombre"],
        "correo":        row["correo"],
        "id_seguro":     row["id_seguro"],
        "nombre_seguro": row["nombre_seguro"],
        "nivel_seguro":  row["nivel_seguro"],
    }

# ── TOOL 2 ───────────────────────────────────────────────────────────────────
def mapear_especialidad(sintoma: str) -> dict:
    """Detecta la especialidad medica a partir de un sintoma en texto libre."""
    conn = get_connection()
    cursor = conn.cursor()

    # Normalizar texto
    sintoma_norm = sintoma.lower()
    for char in "áéíóúàèìòùäëïöü":
        replacements = {"á":"a","é":"e","í":"i","ó":"o","ú":"u",
                        "à":"a","è":"e","ì":"i","ò":"o","ù":"u",
                        "ä":"a","ë":"e","ï":"i","ö":"o","ü":"u"}
        sintoma_norm = sintoma_norm.replace(char, replacements.get(char, char))

    cursor.execute("SELECT keyword_sintoma, id_especialidad, confianza FROM sintoma_especialidad")
    keywords = cursor.fetchall()

    # Calcular score por especialidad
    scores = {}
    hits = {}
    for kw in keywords:
        if kw["keyword_sintoma"] in sintoma_norm:
            esp_id = kw["id_especialidad"]
            scores[esp_id] = scores.get(esp_id, 0) + kw["confianza"]
            hits.setdefault(esp_id, []).append(kw["keyword_sintoma"])

    if not scores:
        conn.close()
        return {
            "error": "No pude identificar la especialidad con ese sintoma",
            "sugerencia": "Por favor describe mejor tu sintoma"
        }

    # Especialidad con mayor score
    best_id = max(scores, key=scores.get)
    total_keywords = sum(1 for kw in keywords if kw["id_especialidad"] == best_id)
    confianza_pct = min(99, round((scores[best_id] / total_keywords) * 100))

    # Obtener nombre de la especialidad (sin duplicados por hospital)
    cursor.execute("""
        SELECT DISTINCT especialidad FROM especialidades
        WHERE id_especialidad = ?
    """, (best_id,))
    nombre = cursor.fetchone()
    conn.close()

    return {
        "id_especialidad": best_id,
        "especialidad":    nombre["especialidad"] if nombre else "Desconocida",
        "confianza_pct":   confianza_pct,
        "keywords_encontradas": hits[best_id],
    }

# ── TOOL 3 ───────────────────────────────────────────────────────────────────
def buscar_hospitales(id_especialidad: int) -> list:
    """Retorna hospitales que ofrecen la especialidad con su precio base."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id_especialidad, e.especialidad, e.precio_base,
               h.id_hospital, h.hospital, h.direccion, h.ciudad, h.telefono
        FROM especialidades e
        JOIN hospitales h ON e.id_hospital = h.id_hospital
        WHERE e.especialidad = (
            SELECT especialidad FROM especialidades WHERE id_especialidad = ?
        )
        ORDER BY e.precio_base ASC
    """, (id_especialidad,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id_especialidad": r["id_especialidad"],
            "especialidad":    r["especialidad"],
            "precio_base":     r["precio_base"],
            "id_hospital":     r["id_hospital"],
            "hospital":        r["hospital"],
            "direccion":       r["direccion"],
            "ciudad":          r["ciudad"],
            "telefono":        r["telefono"],
        }
        for r in rows
    ]

# ── TOOL 4 ───────────────────────────────────────────────────────────────────
def calcular_copago(id_seguro: int, id_especialidad: int) -> dict:
    """Calcula el copago exacto para un seguro y especialidad dados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.porcentaje, e.precio_base, e.especialidad,
               s.nombre_seguro, s.nivel_seguro
        FROM copago c
        JOIN especialidades e ON c.id_especialidad = e.id_especialidad
        JOIN seguros s ON c.id_seguro = s.id_seguro
        WHERE c.id_seguro = ? AND c.id_especialidad = ?
    """, (id_seguro, id_especialidad))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "No se encontro copago para ese seguro y especialidad"}

    precio     = row["precio_base"]
    porcentaje = row["porcentaje"]
    copago     = round(precio * porcentaje / 100, 2)
    cubre      = round(precio - copago, 2)

    return {
        "nombre_seguro": row["nombre_seguro"],
        "nivel_seguro":  row["nivel_seguro"],
        "especialidad":  row["especialidad"],
        "precio_base":   precio,
        "porcentaje":    porcentaje,
        "copago_paciente": copago,
        "cubre_seguro":    cubre,
    }

# ── TOOL 5 ───────────────────────────────────────────────────────────────────
def rankear_opciones(id_seguro: int | None, id_especialidad: int) -> list:

    hospitales = buscar_hospitales(id_especialidad)

    resultado = []

    if id_seguro is None:
        # SIN SEGURO → paga todo
        for h in hospitales:
            resultado.append({
                **h,
                "porcentaje": 100,
                "copago_paciente": h["precio_base"],
                "cubre_seguro": 0,
            })
        return sorted(resultado, key=lambda x: x["copago_paciente"])

    # CON SEGURO (tu lógica actual)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT porcentaje FROM copago
        WHERE id_seguro = ? AND id_especialidad = ?
        LIMIT 1
    """, (id_seguro, id_especialidad))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return []

    porcentaje = row["porcentaje"]

    for h in hospitales:
        precio = h["precio_base"]
        copago = round(precio * porcentaje / 100, 2)
        cubre = round(precio - copago, 2)

        resultado.append({
            **h,
            "porcentaje": porcentaje,
            "copago_paciente": copago,
            "cubre_seguro": cubre,
        })

    return sorted(resultado, key=lambda x: x["copago_paciente"])
# ── TOOL 6 (utilidad) ────────────────────────────────────────────────────────
def guardar_log(id_cliente: int, id_especialidad: int,
                id_hospital: int, copago: float, sintoma: str):
    """Guarda la consulta en el log transaccional."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO consulta_log
            (id_cliente, id_especialidad, id_hospital, fecha, copago_estimado, sintoma_ingresado)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id_cliente, id_especialidad, id_hospital,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), copago, sintoma))
    conn.commit()
    conn.close()


# ── TEST RAPIDO ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== TEST TOOLS ===\n")

    print("1. lookup_seguro:")
    print(lookup_seguro("0932001001"))

    print("\n2. mapear_especialidad:")
    print(mapear_especialidad("me duele mucho el pecho y siento palpitaciones"))

    print("\n3. buscar_hospitales:")
    hospitales = buscar_hospitales(2)
    for h in hospitales:
        print(f"   {h['hospital']} - ${h['precio_base']}")

    print("\n4. calcular_copago:")
    print(calcular_copago(1, 2))

    print("\n5. rankear_opciones:")
    ranking = rankear_opciones(1, 2)
    for i, r in enumerate(ranking, 1):
        print(f"   {i}. {r['hospital']} - Copago: ${r['copago_paciente']}")
