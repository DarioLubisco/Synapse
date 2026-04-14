import os
import paramiko
from scp import SCPClient

HOST = "10.147.18.204"
USER = "root"
PASSWORD = "Twinc3pt.2"
REMOTE_DIR = "/opt/stacks/synapse-app/Synapse"
LOCAL_DIR = r"c:\source\Synapse"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("Conectando a SSH...")
    ssh.connect(HOST, username=USER, password=PASSWORD)
    
    print("Iniciando transferencia SCP...")
    scp = SCPClient(ssh.get_transport())
    
    # Upload everything needed
    dirs_to_sync = ['backend', 'frontend', 'nginx']
    files_to_sync = ['docker-compose.yml', 'web-service.yml']
    
    for d in dirs_to_sync:
        local_path = os.path.join(LOCAL_DIR, d)
        if os.path.exists(local_path):
            print(f"Subiendo {d}...")
            scp.put(local_path, recursive=True, remote_path=REMOTE_DIR)
            
    for f in files_to_sync:
        local_path = os.path.join(LOCAL_DIR, f)
        if os.path.exists(local_path):
            print(f"Subiendo {f}...")
            scp.put(local_path, remote_path=REMOTE_DIR)
            
    scp.close()
    
    print("Ejecutando reinicio de Docker...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_DIR} && docker compose -f web-service.yml up -d --build")
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:", out)
    if err:
        print("STDERR:", err)
        
    print("Despliegue completado con exito.")
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
