import random
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from faker import Faker
import unicodedata


# Directorios base
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / 'clients'
SUPABASE_DIR = SAMPLES_DIR / 'supabase'
MONGO_DIR = SAMPLES_DIR / 'mongo'
NEO4J_DIR = SAMPLES_DIR / 'neo4j'
MSSQL_DIR = SAMPLES_DIR / 'mssql'
MYSQL_DIR = SAMPLES_DIR / 'mysql'

# Crear directorios si no existen
SUPABASE_DIR.mkdir(parents=True, exist_ok=True)
MONGO_DIR.mkdir(parents=True, exist_ok=True)
NEO4J_DIR.mkdir(parents=True, exist_ok=True)
MSSQL_DIR.mkdir(parents=True, exist_ok=True)
MYSQL_DIR.mkdir(parents=True, exist_ok=True)

nombres_usados = set()
correos_usados = set()

# Para generar correos
def limpiar_texto(texto: str) -> str:
    """Elimina acentos y caracteres no ASCII del texto."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def generar_email_desde_nombre(nombre: str) -> str:
    """Genera un email basado en el nombre."""
    nombre_limpio = limpiar_texto(nombre.lower().replace(" ", "."))
    return f"{nombre_limpio}@example.com"

# Para generar clientes
def generar_datos_clientes_supabase(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')  # Usar español para nombres y países
    clientes = []
    while len(clientes) < num_clientes:

        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Verificar unicidad
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'nombre': nombre,
            'email': email,
            'genero': random.choice(['M', 'F']),
            'pais': fake.country(),
            'fecha_registro': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes

def generar_datos_clientes_mongo(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios con preferencias y creado.$date."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []

    CANALES = ["WEB", "TIENDA"]

    while len(clientes) < num_clientes:

        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        # Seleccionar 1 o 2 canales distintos
        canales = random.sample(CANALES, random.randint(1, 2))

        cliente = {
            "nombre": nombre,
            "email": email,
            "genero": random.choice(["Masculino", "Femenino", "Otro"]),
            "pais": fake.country_code(),  # códigos tipo CR, MX, ES
            "preferencias": {
                "canal": canales
            },
            "creado": {
                "$date": fake.date_between(start_date='-2y', end_date='today').isoformat()
            }
        }

        clientes.append(cliente)

    return clientes

def generar_datos_clientes_neo4j(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes con id, nombre, género y país."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []

    generos_posibles = ['M', 'F', 'Otro', 'Masculino', 'Femenino']

    contador = 1  # Para generar ids tipo C00001, C00002, ...

    while len(clientes) < num_clientes:

        nombre = fake.name()

        # Verificar unicidad del nombre
        if nombre in nombres_usados:
            continue

        # Registrar como usado
        nombres_usados.add(nombre)

        # Crear ID autogenerado C00001, C00002, ...
        id_cliente = f"C{contador:05d}"

        cliente = {
            'id': id_cliente,
            'nombre': nombre,
            'genero': random.choice(generos_posibles),
            'pais': fake.country()
        }

        clientes.append(cliente)
        contador += 1

    return clientes

def generar_datos_clientes_mssql(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')  # Usar español para nombres y países
    clientes = []

    while len(clientes) < num_clientes:

        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'Nombre': nombre,
            'Email': email,
            'Genero': random.choice(['Masculino', 'Femenino']),
            'Pais': fake.country(),
            'FechaRegistro': fake.date_between(start_date='-2y', end_date='today').isoformat()
        }
        clientes.append(cliente)
    return clientes

def generar_datos_clientes_mysql(num_clientes: int = 600) -> List[Dict[str, Any]]:
    """Genera datos ficticios para clientes (MySQL - heterogeneidades)."""
    global nombres_usados, correos_usados

    fake = Faker('es_ES')
    clientes = []

    while len(clientes) < num_clientes:

        nombre = fake.name()
        email = generar_email_desde_nombre(nombre)

        # Evitar duplicados
        if nombre in nombres_usados:
            continue
        if email in correos_usados:
            continue

        # Registrar como usados
        nombres_usados.add(nombre)
        correos_usados.add(email)

        cliente = {
            'nombre': nombre,
            'correo': email,
            'genero': random.choice(['M', 'F', 'X']),  # Valores heterogéneos: M, F, X
            'pais': fake.country(),
            'created_at': fake.date_between(start_date='-2y', end_date='today').isoformat()  # VARCHAR: YYYY-MM-DD
        }
        clientes.append(cliente)
    return clientes

# Para generar csv
def guardar_csv(datos: List[Dict[str, Any]], filename: str) -> None:
    """Guarda una lista de diccionarios en un archivo CSV."""
    df = pd.DataFrame(datos)
    df.to_csv(filename, index=False)
    print(f"Guardado {filename} con {len(datos)} registros")

# Para correr
def main() -> None:
    """Función principal del script."""
    clientes_supabase = generar_datos_clientes_supabase(600)
    clientes_mongo = generar_datos_clientes_mongo(600)
    clientes_neo4j = generar_datos_clientes_neo4j(600)
    clientes_mssql = generar_datos_clientes_mssql(600)
    clientes_mysql = generar_datos_clientes_mysql(600)

    print("=== Generador de Datos de Clientes ===\n")
    guardar_csv(clientes_supabase, str(SUPABASE_DIR / 'clients_supabase.csv'))
    guardar_csv(clientes_mongo, str(MONGO_DIR / 'clients_mongo.csv'))
    guardar_csv(clientes_neo4j, str(NEO4J_DIR / 'clients_neo4j.csv'))
    guardar_csv(clientes_mssql, str(MSSQL_DIR / 'clients_mssql.csv'))
    guardar_csv(clientes_mysql, str(MYSQL_DIR / 'clients_mysql.csv'))
    print()
    print("\n=== Generación completada ===")


if __name__ == "__main__":
    main()