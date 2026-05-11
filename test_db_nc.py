import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    stdin, stdout, stderr = ssh.exec_command("nc -vz 10.200.8.5 49751 && nc -vz 10.200.8.5 1433 && nc -vzu 10.200.8.5 1434")
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="", file=sys.stderr)
finally:
    ssh.close()
