import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=10)

# Usamos comillas simples para el script de Python y dobles para el comando shell
script = "import sys; sys.path.append('/app/backend'); import database; conn = database.get_db_connection(); c = conn.cursor(); c.execute('SELECT cn.CodProv, p.CodProv, p.Descrip, p.ID3 FROM EnterpriseAdmin_AMC.Procurement.CreditNotesTracking cn LEFT JOIN EnterpriseAdmin_AMC.dbo.SAPROV p ON cn.CodProv=p.CodProv WHERE cn.Id=17'); row = c.fetchone(); print(f'Row: {row}')"

stdin, stdout, stderr = ssh.exec_command(f'docker exec synapse-api python3 -c "{script}"')
print('OUT:', stdout.read().decode('utf-8'))
print('ERR:', stderr.read().decode('utf-8'))
ssh.close()
