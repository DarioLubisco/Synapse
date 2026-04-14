import paramiko

HOST = "10.147.18.204"
USER = "root"
PASSWORD = "Twinc3pt.2"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD)
    stdin, stdout, stderr = ssh.exec_command("docker logs --tail 50 synapse-api")
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("LOGS STDOUT:\n", out)
    if err:
        print("LOGS STDERR:\n", err)
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
