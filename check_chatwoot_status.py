import paramiko

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    print("Checking Chatwoot logs...")
    stdin, stdout, stderr = ssh.exec_command("docker logs --tail 20 chatwoot-rails")
    print("STDOUT:", stdout.read().decode('utf-8'))
    print("STDERR:", stderr.read().decode('utf-8'))
    
    print("\nChecking if port 3000 is listening...")
    stdin, stdout, stderr = ssh.exec_command("netstat -tulpn | grep :3000")
    print("Netstat:", stdout.read().decode('utf-8'))
    
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
