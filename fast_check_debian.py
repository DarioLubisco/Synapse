import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    stdin, stdout, stderr = ssh.exec_command('ls -l /root/ && cat /root/Agent-Lab/.env || cat /root/Synapse/.env')
    print("STDOUT env:", stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('docker ps')
    print("Docker PS:", stdout.read().decode())
    
    # Check what the actual DB_SERVER config inside the synapse container is
    stdin, stdout, stderr = ssh.exec_command('docker exec synapse-api cat .env || docker exec synapse-api env | grep DB_SERVER')
    print("Container Env DB_SERVER:", stdout.read().decode())

except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
