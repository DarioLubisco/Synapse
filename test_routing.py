import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    print("Testing backend port 8000 directly...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/cuentas-por-pagar")
    print(stdout.read().decode().strip())
    
    print("Testing proxy port 8085 directly...")
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8085/api/cuentas-por-pagar")
    print(stdout.read().decode().strip())
    
finally:
    ssh.close()
