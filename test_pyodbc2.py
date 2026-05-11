import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    script = """
import os
import pyodbc

server = os.environ.get('DB_SERVER', r'10.200.8.5,49751')
database = os.environ.get('DB_DATABASE', 'EnterpriseAdmin_AMC')
username = os.environ.get('DB_USERNAME', 'sa')
password = os.environ.get('DB_PASSWORD', 'Twinc3pt.')
driver = os.environ.get('DRIVER', 'ODBC Driver 18 for SQL Server')

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "LoginTimeout=5;"
)
print('Conn str:', conn_str)
try:
    conn = pyodbc.connect(conn_str)
    print('Connected successfully!')
    conn.close()
except Exception as e:
    print('Error:', e)
"""
    
    # create script.py inside container
    ssh.exec_command(f"docker exec -i synapse-api sh -c 'cat > /tmp/test.py' << 'EOF'\n{script}\nEOF\n")
    
    stdin, stdout, stderr = ssh.exec_command("docker exec synapse-api python /tmp/test.py")
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="", file=sys.stderr)
finally:
    ssh.close()
