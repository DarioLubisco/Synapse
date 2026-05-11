import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()
DB_SERVER = os.getenv("DB_SERVER", "amc.sql\\efficacis3")
print("Trying to connect to:", DB_SERVER)

try:
    available = pyodbc.drivers()
    driver_name = "ODBC Driver 17 for SQL Server"
    if "ODBC Driver 18 for SQL Server" in available:
        driver_name = "ODBC Driver 18 for SQL Server"
    conn_str = f"DRIVER={{{driver_name}}};SERVER={DB_SERVER};DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str, timeout=5)
    print("Success")
except Exception as e:
    print("Error:", e)
