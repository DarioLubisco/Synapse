import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    script = """
import socket
def check_port(ip, port, is_udp=False):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM if is_udp else socket.SOCK_STREAM)
        s.settimeout(2.0)
        if is_udp:
            s.sendto(b'\\x02', (ip, port))
            data, _ = s.recvfrom(1024)
            return True
        else:
            s.connect((ip, port))
            return True
    except Exception as e:
        return False
    finally:
        s.close()

print('TCP 49751:', check_port('10.200.8.5', 49751))
print('TCP 1433:', check_port('10.200.8.5', 1433))
print('UDP 1434:', check_port('10.200.8.5', 1434, True))
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="", file=sys.stderr)
finally:
    ssh.close()
