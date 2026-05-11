import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Try fetching one of the endpoints
    stdin, stdout, stderr = ssh.exec_command('curl -v http://localhost:8000/caja/vendedores')
    print("/caja/vendedores Response:\n", stdout.read().decode())
    print("ERR:\n", stderr.read().decode())
    
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
