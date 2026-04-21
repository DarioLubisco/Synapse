import sys
sys.path.append('c:\\source\\Synapse\\backend')
import database

try:
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.CodProv, p.Descrip, p.ID3, c.Email 
        FROM EnterpriseAdmin_AMC.dbo.SAPROV p 
        LEFT JOIN EnterpriseAdmin_AMC.Procurement.ProveedorCondiciones c ON p.CodProv = c.CodProv 
        WHERE p.CodProv = ?
    """, ('J-411993918-8',))
    prov_row = c.fetchone()
    print("Type:", type(prov_row))
    print("Value:", prov_row)
    print("prov_row.CodProv:", prov_row.CodProv)
    print("prov_row.Descrip:", prov_row.Descrip)
    print("prov_row.ID3:", prov_row.ID3)
    dict_val = {"CodProv": prov_row.CodProv, "Descrip": prov_row.Descrip, "ID3": prov_row.ID3, "Email": getattr(prov_row, 'Email', 'None')}
    print(dict_val)
except Exception as e:
    import traceback
    traceback.print_exc()
