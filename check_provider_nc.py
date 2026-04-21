import database

conn = database.get_db_connection()
c = conn.cursor()
c.execute("""
    SELECT cn.Id, p.CodProv, p.Descrip, p.ID3 
    FROM EnterpriseAdmin_AMC.Procurement.CreditNotesTracking cn 
    LEFT JOIN EnterpriseAdmin_AMC.dbo.SAPROV p ON cn.CodProv=p.CodProv 
    WHERE cn.Id=17
""")
print(c.fetchone())
