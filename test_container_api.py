import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Try fetching one of the endpoints from INSIDE the container
    stdin, stdout, stderr = ssh.exec_command('docker exec synapse-api curl -s http://localhost:8000/caja/tasa_del_dia')
    print("/caja/tasa_del_dia Response:\n", stdout.read().decode())

except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
