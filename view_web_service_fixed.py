import paramiko
import sys
import base64

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("cat /opt/stacks/synapse-app/Synapse/web-service.yml")
    out = stdout.read()
    print(out.decode('utf-8', 'ignore'))
finally:
    ssh.close()
