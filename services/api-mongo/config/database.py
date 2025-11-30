from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Generator
import pyodbc
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_database():
    client = get_mongo_client()
    return client[MONGO_DB]

db = get_database()

def get_mssql_connection() -> Generator:
    connection = None
    try:
        server = os.getenv('MSSQL_DW_HOST', 'localhost')
        database = os.getenv('MSSQL_DW_DB', 'your_database')
        username = os.getenv('MSSQL_DW_USER', 'your_username')
        password = os.getenv('MSSQL_DW_PASS', 'your_password')
        port = os.getenv('MSSQL_DW_PORT', '1433')
        driver = os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

        # TrustServerCertificate=yes is required for self-signed certificates
        connection_string = f'DRIVER={driver};SERVER={server},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes'

        # Crear conexión
        connection = pyodbc.connect(connection_string)
        yield connection
        
    finally:
        if connection:
            connection.close()