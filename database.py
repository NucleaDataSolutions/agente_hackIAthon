import sqlite3
import os

DB_PATH = os.path.join("data", "hospital.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seguros (
            id_seguro INTEGER PRIMARY KEY,
            nombre_seguro TEXT NOT NULL,
            nivel_seguro INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cliente (
            id_cliente INTEGER PRIMARY KEY,
            cedula TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            correo TEXT,
            id_seguro INTEGER,
            FOREIGN KEY (id_seguro) REFERENCES seguros(id_seguro)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitales (
            id_hospital INTEGER PRIMARY KEY,
            hospital TEXT NOT NULL,
            direccion TEXT,
            ciudad TEXT,
            telefono TEXT,
            correo TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS especialidades (
            id_especialidad INTEGER PRIMARY KEY,
            especialidad TEXT NOT NULL,
            precio_base REAL NOT NULL,
            id_hospital INTEGER,
            FOREIGN KEY (id_hospital) REFERENCES hospitales(id_hospital)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS copago (
            id_copago INTEGER PRIMARY KEY,
            id_seguro INTEGER,
            id_especialidad INTEGER,
            porcentaje REAL NOT NULL,
            FOREIGN KEY (id_seguro) REFERENCES seguros(id_seguro),
            FOREIGN KEY (id_especialidad) REFERENCES especialidades(id_especialidad)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sintoma_especialidad (
            id_mapeo INTEGER PRIMARY KEY,
            keyword_sintoma TEXT NOT NULL,
            id_especialidad INTEGER,
            confianza REAL DEFAULT 1.0,
            FOREIGN KEY (id_especialidad) REFERENCES especialidades(id_especialidad)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consulta_log (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER,
            id_especialidad INTEGER,
            id_hospital INTEGER,
            fecha TEXT,
            copago_estimado REAL,
            sintoma_ingresado TEXT,
            canal TEXT DEFAULT 'streamlit'
        )
    """)

    conn.commit()

    if cursor.execute("SELECT COUNT(*) FROM seguros").fetchone()[0] == 0:

        # Seguros reales Ecuador
        cursor.executemany("INSERT INTO seguros VALUES (?,?,?)", [
            (1, "Saludsa",     3),  # Plan Plus   — copago 20%
            (2, "Saludsa",     4),  # Plan Premium — copago 10%
            (3, "Ecuasanitas", 2),  # Plan Estandar — copago 30%
            (4, "BMI Ecuador", 1),  # Plan Basico  — copago 40%
        ])

        # Clientes
        cursor.executemany("INSERT INTO cliente VALUES (?,?,?,?,?)", [
            (1, "0932001001", "Enrique Calle",      "enrique@email.com",    1),
            (2, "0932001002", "Cristhian Gallegos",  "cristhian@email.com",  2),
            (3, "0932001003", "Kenny Pizarro",        "kenny@email.com",      3),
        ])

        # Hospitales reales Guayaquil
        cursor.executemany("INSERT INTO hospitales VALUES (?,?,?,?,?,?)", [
            (1, "Clinica Kennedy",
                "Av. Rodolfo Baquerizo Nazur y Calle Crotos, Alborada",
                "Guayaquil", "04-268-0000", "info@kennedysalud.com"),
            (2, "Omni Hospital",
                "Av. Abel Castillo y Av. Juan Tanca Marengo",
                "Guayaquil", "04-268-7900", "info@omnihospital.com"),
            (3, "Clinica Alcivar",
                "Coronel 2301 y Azuay, Torre 1",
                "Guayaquil", "04-256-5000", "info@clinicaalcivar.com"),
        ])

        # Especialidades con precios reales de mercado Guayaquil
        # Cada hospital ofrece las mismas especialidades pero con precio propio
        cursor.executemany("INSERT INTO especialidades VALUES (?,?,?,?)", [
            # Kennedy
            (1,  "Medicina General",   30.00, 1),
            (2,  "Cardiologia",        75.00, 1),
            (3,  "Oftalmologia",       65.00, 1),
            (4,  "Traumatologia",      80.00, 1),
            (5,  "Gastroenterologia",  70.00, 1),
            # Omni Hospital
            (6,  "Medicina General",   28.00, 2),
            (7,  "Cardiologia",        70.00, 2),
            (8,  "Oftalmologia",       60.00, 2),
            (9,  "Traumatologia",      75.00, 2),
            (10, "Gastroenterologia",  65.00, 2),
            # Clinica Alcivar
            (11, "Medicina General",   25.00, 3),
            (12, "Cardiologia",        65.00, 3),
            (13, "Oftalmologia",       55.00, 3),
            (14, "Traumatologia",      70.00, 3),
            (15, "Gastroenterologia",  60.00, 3),
        ])

        # Copagos por seguro y especialidad
        # Logica: nivel 1=40%, nivel 2=30%, nivel 3=20%, nivel 4=10%
        copagos = []
        id_copago = 1
        porcentajes = {1: 20.0, 2: 10.0, 3: 30.0, 4: 40.0}  # id_seguro: %

        for id_seguro, porcentaje in porcentajes.items():
            for id_especialidad in range(1, 16):
                copagos.append((id_copago, id_seguro, id_especialidad, porcentaje))
                id_copago += 1

        cursor.executemany("INSERT INTO copago VALUES (?,?,?,?)", copagos)

        # Keywords de deteccion de especialidad
        cursor.executemany("INSERT INTO sintoma_especialidad VALUES (?,?,?,?)", [
            # Medicina General (id 1,6,11)
            (1,  "fiebre",        1, 0.85),
            (2,  "gripe",         1, 0.90),
            (3,  "garganta",      1, 0.85),
            (4,  "tos",           1, 0.80),
            (5,  "resfriado",     1, 0.90),
            (6,  "malestar",      1, 0.70),
            (7,  "cansancio",     1, 0.70),
            # Cardiologia (id 2,7,12)
            (8,  "pecho",         2, 0.90),
            (9,  "corazon",       2, 0.95),
            (10, "palpitaciones", 2, 0.95),
            (11, "taquicardia",   2, 0.95),
            (12, "opresion",      2, 0.85),
            (13, "aire",          2, 0.75),
            (14, "infarto",       2, 0.99),
            # Oftalmologia (id 3,8,13)
            (15, "vista",         3, 0.90),
            (16, "ojo",           3, 0.90),
            (17, "vision",        3, 0.90),
            (18, "borrosa",       3, 0.85),
            (19, "lagrimeo",      3, 0.85),
            (20, "pupila",        3, 0.80),
            (21, "retina",        3, 0.95),
            # Traumatologia (id 4,9,14)
            (22, "rodilla",       4, 0.90),
            (23, "fractura",      4, 0.95),
            (24, "esguince",      4, 0.95),
            (25, "hinchazon",     4, 0.75),
            (26, "columna",       4, 0.85),
            (27, "tobillo",       4, 0.90),
            (28, "hueso",         4, 0.85),
            # Gastroenterologia (id 5,10,15)
            (29, "estomago",      5, 0.85),
            (30, "gastritis",     5, 0.95),
            (31, "reflujo",       5, 0.90),
            (32, "nausea",        5, 0.80),
            (33, "diarrea",       5, 0.85),
            (34, "acidez",        5, 0.90),
            (35, "intestino",     5, 0.85),
        ])

        conn.commit()
        print("✅ Base de datos creada con datos reales de Guayaquil.")
    else:
        print("✅ Base de datos ya existe.")

    conn.close()

if __name__ == "__main__":
    init_db()