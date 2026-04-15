import sys
sys.path.append('c:\\source\\Synapse\\backend')
import database

try:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 CodProv FROM EnterpriseAdmin_AMC.dbo.SAPROV WHERE CodProv LIKE '%/%'")
    rows = cursor.fetchall()
    print("Slashes:", rows)

    cursor.execute("SELECT TOP 5 CodProv FROM EnterpriseAdmin_AMC.dbo.SAPROV WHERE CodProv LIKE '% %'")
    rows_spaces = cursor.fetchall()
    print("Spaces:", rows_spaces)
except Exception as e:
    print(e)
