import paramiko
import os

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

files_to_deploy = [
    (r"c:\source\Synapse\backend\routers\caja.py", "/opt/stacks/synapse-app/Synapse/backend/routers/caja.py"),
    (r"c:\source\Synapse\frontend\modulo_caja.html", "/opt/stacks/synapse-app/Synapse/frontend/modulo_caja.html"),
]

try:
    print("Connecting to Debian via SSH...")
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    sftp = ssh.open_sftp()
    
    for local_path, remote_path in files_to_deploy:
        print(f"Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
    
    sftp.close()
    
    print("Restarting synapse-frontend and synapse-api service to load frontend/backend changes...")
    stdin, stdout, stderr = ssh.exec_command("docker restart synapse-frontend synapse-api")
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:", out.strip())
    print("STDERR:", err.strip())
    
    print("Deployment completed successfully.")
    
except Exception as e:
    print(f"Deployment Error: {e}")
finally:
    ssh.close()
