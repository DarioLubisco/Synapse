import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("cat /opt/stacks/synapse-app/Synapse/web-service.yml")
    out = stdout.read()
    with open("web_service_local.yml", "wb") as f:
        f.write(out)
finally:
    ssh.close()
