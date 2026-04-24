import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=10)

# Script a ejecutar dentro del contenedor
script = """
import sys
import os
import pyodbc
sys.path.append('/app/backend')
try:
    # Probar con IP directa
    server = '10.200.8.5'
    database = 'EnterpriseAdmin_AMC'
    username = 'sa'
    password = 'Twinc3pt.'
    driver = '{ODBC Driver 18 for SQL Server}'
    
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
    print(f"Connecting to {server}...")
    conn = pyodbc.connect(conn_str, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 name FROM sys.databases")
    row = cursor.fetchone()
    print(f"SUCCESS: Connected to DB. Database name: {row[0]}")
    conn.close()
except Exception as e:
    print(f"FAILURE: {str(e)}")
"""

# Escapar comillas dobles para el comando shell
escaped_script = script.replace('"', '\\"')
command = f'docker exec synapse-api python3 -c "{escaped_script}"'

stdin, stdout, stderr = ssh.exec_command(command)
print('OUT:', stdout.read().decode('utf-8'))
print('ERR:', stderr.read().decode('utf-8'))

ssh.close()
