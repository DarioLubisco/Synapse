import sys
sys.path.append('c:\\source\\Synapse\\backend')
import database

try:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ProveedorCondiciones'")
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print(e)
