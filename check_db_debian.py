import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Check how database.py builds the connection string inside synapse-api
    stdin, stdout, stderr = ssh.exec_command('docker exec synapse-api cat /app/database.py')
    print("database.py on Debian:\n", stdout.read().decode())

except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
