import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    script = """
import socket
def check_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((ip, port))
        return True
    except Exception as e:
        return str(e)
    finally:
        s.close()
print('TCP 49751:', check_port('10.200.8.5', 49751))
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"docker exec synapse-api python -c \"{script}\"")
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="", file=sys.stderr)
finally:
    ssh.close()
