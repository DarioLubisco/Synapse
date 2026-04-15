import sys
sys.path.append('c:\\source\\Synapse\\backend')
import database

try:
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, COLUMNPROPERTY(object_id(TABLE_SCHEMA+'.'+TABLE_NAME), COLUMN_NAME, 'IsIdentity') as IsIdentity
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ProveedorDescuentosProntoPago'
    """)
    for row in cursor.fetchall():
        print(row)
except Exception as e:
    print(e)
