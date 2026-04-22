import paramiko

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"
REMOTE_DIR = "/opt/stacks/synapse-app/Synapse"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"DEBUG: Intentando conectar a {HOST} con usuario {USER}...")
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    print("DEBUG: Conexión SSH establecida con éxito.")

    commands = [
        f"cd {REMOTE_DIR} && git pull origin main",
        f"cd {REMOTE_DIR} && docker compose -f web-service.yml up -d --build",
    ]

    for cmd in commands:
        print(f"DEBUG: Ejecutando comando remoto: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
        
        print("DEBUG: Esperando salida del comando...")
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        
        if out: print(f"OUT: {out}")
        if err: print(f"ERR: {err}")
        print("DEBUG: Comando finalizado.")

    print("Despliegue finalizado.")

except Exception as e:
    print(f"ERROR: {e}")
finally:
    ssh.close()
