import paramiko
import sys

DEBIAN_HOST = "10.147.18.204"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(hostname=DEBIAN_HOST, username="root", password="Twinc3pt.2", timeout=10)
    
    script = """
import socket
import struct

def get_sql_port(ip, instance):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2.0)
        s.sendto(b'\\x02', (ip, 1434))
        data, addr = s.recvfrom(2048)
        s.close()
        
        info = data[3:].decode('ascii', errors='ignore')
        servers = info.split(';;')
        for server in servers:
            if not server: continue
            parts = server.split(';')
            props = {}
            for i in range(0, len(parts)-1, 2):
                props[parts[i].upper()] = parts[i+1]
            if props.get('INSTANCENAME', '').upper() == instance.upper():
                return props.get('TCP', '')
    except Exception as e:
        return str(e)
    return 'Not found'

print('Port:', get_sql_port('10.200.8.5', 'efficacis3'))
"""
    
    stdin, stdout, stderr = ssh.exec_command(f"python3 -c \"{script}\"")
    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(line, end="", file=sys.stderr)
finally:
    ssh.close()
