import paramiko
import os

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

files_to_deploy = [
    (r"c:\source\Synapse\.env.chatwoot", "/opt/stacks/synapse-app/Synapse/.env.chatwoot"),
]

try:
    print("Connecting to Debian via SSH...")
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    sftp = ssh.open_sftp()
    
    for local_path, remote_path in files_to_deploy:
        print(f"Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
    
    sftp.close()
    
    print("Restarting Chatwoot containers to apply FRONTEND_URL and SSL changes...")
    # Using docker restart to force reload of env_file
    stdin, stdout, stderr = ssh.exec_command("docker restart chatwoot-rails chatwoot-sidekiq")
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT:", out.strip())
    print("STDERR:", err.strip())
    
    print("Chatwoot services updated and restarted successfully.")
    
except Exception as e:
    print(f"Deployment Error: {e}")
finally:
    ssh.close()
