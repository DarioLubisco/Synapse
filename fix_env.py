import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    # Replace DB_SERVER IP in .env
    commands = [
        "sed -i 's/DB_SERVER=10.147.18.192\\\\efficacis3/DB_SERVER=10.200.8.5\\\\efficacis3/g' /opt/stacks/synapse-app/Synapse/.env",
        "cd /opt/stacks/synapse-app/Synapse && docker restart synapse-api"
    ]
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.read()
        stderr.read()
    print("Done")
finally:
    ssh.close()
