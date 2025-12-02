from supabase import create_client
from dotenv import load_dotenv
from typing import Generator
import pyodbc
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
