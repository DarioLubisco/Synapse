import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "amc.sql\\efficacis3")
DB_DATABASE = os.getenv("DB_DATABASE", "EnterpriseAdmin_AMC")
DB_USERNAME = os.getenv("DB_USERNAME", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Twinc3pt.")

def get_db_connection():
    available = pyodbc.drivers()
    driver_name = os.getenv("DRIVER", "ODBC Driver 18 for SQL Server").strip("{}")
    if driver_name not in available:
        if "ODBC Driver 18 for SQL Server" in available: driver_name = "ODBC Driver 18 for SQL Server"
        elif "ODBC Driver 17 for SQL Server" in available: driver_name = "ODBC Driver 17 for SQL Server"
        elif "SQL Server" in available: driver_name = "SQL Server"
    
    conn_str = f"DRIVER={{{driver_name}}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD};Encrypt=yes;TrustServerCertificate=yes;"
    return pyodbc.connect(conn_str)

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT NumeroD, CodProv, FechaE, FechaI, Descrip FROM SACOMP WHERE NumeroD = '0076085'")
row = cursor.fetchone()
if row:
    print(f"NumeroD: {row[0]}")
    print(f"CodProv: {row[1]}")
    print(f"FechaE: {row[2]} (Type: {type(row[2])})")
    print(f"FechaI: {row[3]} (Type: {type(row[3])})")
    print(f"Descrip: {row[4]}")
else:
    print("No found")
conn.close()
