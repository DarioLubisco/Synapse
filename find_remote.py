import paramiko
import os

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    stdin, stdout, stderr = ssh.exec_command("find / -name synapse-app -type d 2>/dev/null")
    print("Found 'synapse-app' in:", stdout.read().decode().strip())
    ssh.close()
except Exception as e:
    print(f"Error SSH: {e}")
