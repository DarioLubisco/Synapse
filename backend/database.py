import os
import pyodbc

# Variables from Docker/Environment
DB_SERVER = os.getenv("DB_SERVER", "amc.sql\\efficacis3")
DB_DATABASE = os.getenv("DB_DATABASE", "EnterpriseAdmin_AMC")
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Twinc3pt.")
# En Linux con Docker usaremos ODBC Driver 18
DRIVER = os.getenv("DRIVER", "{ODBC Driver 18 for SQL Server}")

def get_db_connection():
    # String diseñado para soportar ODBC 18 que requiere encriptación explícita
    conn_str = (
        f"DRIVER={DRIVER};"
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
