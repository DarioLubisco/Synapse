import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno (.env tiene precedencia)
DB_SERVER = os.getenv("DB_SERVER", "amc.sql\\efficacis3")
DB_DATABASE = os.getenv("DB_DATABASE", "EnterpriseAdmin_AMC")
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Twinc3pt.")

def get_db_connection():
    # Detectar drivers disponibles para evitar errores de "Driver not found"
    available = pyodbc.drivers()
    driver_name = os.getenv("DRIVER", "ODBC Driver 18 for SQL Server").strip("{}")
    
    # Si el driver configurado no existe en el sistema, buscar uno que sí exista
    if driver_name not in available:
        if "ODBC Driver 18 for SQL Server" in available:
            driver_name = "ODBC Driver 18 for SQL Server"
        elif "ODBC Driver 17 for SQL Server" in available:
            driver_name = "ODBC Driver 17 for SQL Server"
        elif "SQL Server" in available:
            driver_name = "SQL Server"

    conn_str = (
        f"DRIVER={{{driver_name}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str)
    conn.timeout = 30
    return conn
