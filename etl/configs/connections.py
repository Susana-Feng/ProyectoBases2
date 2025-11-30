"""
Configuración de conexiones a bases de datos.
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine
from neo4j import GraphDatabase
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv(".env.local")

# Configuración MSSQL Data Warehouse
MSSQL_DW_HOST = os.getenv("MSSQL_DW_HOST", "your-server-host")
MSSQL_DW_PORT = os.getenv("MSSQL_DW_PORT", "1433")
MSSQL_DW_USER = os.getenv("MSSQL_DW_USER", "your-username")
MSSQL_DW_PASS = os.getenv("MSSQL_DW_PASS", "your-password")
MSSQL_DW_DB = os.getenv("MSSQL_DW_DB", "your-database-name")

# Configuración MSSQL DB_SALES (fuente transaccional)
MSSQL_SALES_HOST = os.getenv("MSSQL_SALES_HOST", "your-server-host")
MSSQL_SALES_PORT = os.getenv("MSSQL_SALES_PORT", "1433")
MSSQL_SALES_USER = os.getenv("MSSQL_SALES_USER", "your-username")
MSSQL_SALES_PASS = os.getenv("MSSQL_SALES_PASS", "your-password")
MSSQL_SALES_DB = os.getenv("MSSQL_SALES_DB", "DB_SALES")

# Configuración MySQL DB_SALES (fuente transaccional)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "password")
MYSQL_DB = os.getenv("MYSQL_DB", "DB_SALES")

# Configuración BCCR WebService
BCCR_TOKEN = os.getenv("BCCR_TOKEN", "your-bccr-token")
BCCR_EMAIL = os.getenv("BCCR_EMAIL", "your-email@example.com")
BCCR_NOMBRE = os.getenv("BCCR_NOMBRE", "Your Name")
BCCR_ENDPOINT = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos"

# Indicadores de BCCR
BCCR_INDICADOR_COMPRA = "317"  # Compra USD/CRC
BCCR_INDICADOR_VENTA = "318"  # Venta USD/CRC

# Variables de conexión MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

# Variables de conexión Supabase
SUPABASE_URI = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Variables de conexión Neo4j
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def get_dw_engine():
    """
    Crea y retorna un engine de SQLAlchemy para la BD del Data Warehouse (MSSQL).
    """
    connection_string = (
        f"mssql+pyodbc://{MSSQL_DW_USER}:{MSSQL_DW_PASS}@"
        f"{MSSQL_DW_HOST}:{MSSQL_DW_PORT}/{MSSQL_DW_DB}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    return create_engine(connection_string, echo=False)


def get_mssql_sales_engine():
    """
    Crea y retorna un engine de SQLAlchemy para la BD transaccional DB_SALES (MSSQL).
    """
    connection_string = (
        f"mssql+pyodbc://{MSSQL_SALES_USER}:{MSSQL_SALES_PASS}@"
        f"{MSSQL_SALES_HOST}:{MSSQL_SALES_PORT}/{MSSQL_SALES_DB}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    return create_engine(connection_string, echo=False)


def get_mysql_engine():
    """
    Crea y retorna un engine de SQLAlchemy para la BD transaccional DB_SALES (MySQL).
    """
    connection_string = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        f"?charset=utf8mb4"
    )
    return create_engine(connection_string, echo=False)


def get_mongo_client():
    return MongoClient(MONGO_URI)


def get_mongo_database():
    client = get_mongo_client()
    return client[MONGO_DB]

def get_supabase_client():
    client = create_client(SUPABASE_URI, SUPABASE_KEY)
    return client

def get_neo4j_driver():
    uri = NEO4J_URI
    user = NEO4J_USERNAME
    password = NEO4J_PASSWORD

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


if __name__ == "__main__":
    print("Configuraciones cargadas exitosamente.")
    print(f"MSSQL DW: {MSSQL_DW_HOST}:{MSSQL_DW_PORT}/{MSSQL_DW_DB}")
    print(f"MSSQL Sales: {MSSQL_SALES_HOST}:{MSSQL_SALES_PORT}/{MSSQL_SALES_DB}")
    print(f"BCCR Endpoint: {BCCR_ENDPOINT}")
    print(f"MongoDB URI: {MONGO_URI} - - - - Database: {MONGO_DB}")
