import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=10)
    stdin, stdout, stderr = ssh.exec_command('cat /root/synapse/.env || cat /app/.env || cat /opt/synapse/.env || cat /root/Agent-Lab/synapse/.env || find / -name ".env" | grep synapse')
    out = stdout.read().decode()
    print("STDOUT:", out)
    err = stderr.read().decode()
    print("STDERR:", err)
    
    # Check docker containers
    stdin, stdout, stderr = ssh.exec_command('docker ps')
    print("Docker PS:", stdout.read().decode())
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
