"""
Configuración de conexiones a bases de datos.
"""

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(".env.local")

# Configuración MSSQL Data Warehouse
MSSQL_DW_HOST = os.getenv("MSSQL_DW_HOST", "your-server-host")
MSSQL_DW_PORT = os.getenv("MSSQL_DW_PORT", "1433")
MSSQL_DW_USER = os.getenv("MSSQL_DW_USER", "your-username")
MSSQL_DW_PASS = os.getenv("MSSQL_DW_PASS", "your-password")
MSSQL_DW_DB = os.getenv("MSSQL_DW_DB", "your-database-name")

# Configuración BCCR WebService
BCCR_TOKEN = os.getenv("BCCR_TOKEN", "your-bccr-token")
BCCR_EMAIL = os.getenv("BCCR_EMAIL", "your-email@example.com")
BCCR_NOMBRE = os.getenv("BCCR_NOMBRE", "Your Name")
BCCR_ENDPOINT = "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos"

# Indicadores de BCCR
BCCR_INDICADOR_COMPRA = "317"  # Compra USD/CRC
BCCR_INDICADOR_VENTA = "318"  # Venta USD/CRC


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


if __name__ == "__main__":
    print("Configuraciones cargadas exitosamente.")
    print(f"MSSQL DW: {MSSQL_DW_HOST}:{MSSQL_DW_PORT}/{MSSQL_DW_DB}")
    print(f"BCCR Endpoint: {BCCR_ENDPOINT}")
