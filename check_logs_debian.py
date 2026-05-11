import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    stdin, stdout, stderr = ssh.exec_command('docker logs --tail 100 synapse-api')
    print("synapse-api logs:\n", stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command('docker exec synapse-api python -c "import pyodbc; available = pyodbc.drivers(); print(available)"')
    print("Available drivers in container:\n", stdout.read().decode())
    
    # Also test the actual DB connection from inside the container
    test_script = """import pyodbc
import os
driver_name = "ODBC Driver 18 for SQL Server"
conn_str = f"DRIVER={{{driver_name}}};SERVER=10.200.8.5\\\\efficacis3;DATABASE=EnterpriseAdmin_AMC;UID=sa;PWD=Twinc3pt.;Encrypt=yes;TrustServerCertificate=yes;"
try:
    conn = pyodbc.connect(conn_str, timeout=5)
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", str(e))
"""
    stdin, stdout, stderr = ssh.exec_command(f'docker exec synapse-api python -c \'{test_script}\'')
    print("DB connection test from container:\n", stdout.read().decode())
    print("STDERR:\n", stderr.read().decode())

except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
