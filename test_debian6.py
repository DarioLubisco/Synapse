import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Create .env file inside backend directory on Debian
    env_content = """
DB_SERVER=10.200.8.5\\efficacis3
DB_DATABASE=EnterpriseAdmin_AMC
DB_USERNAME=sa
DB_PASSWORD=Twinc3pt.
DRIVER={ODBC Driver 18 for SQL Server}
"""
    command = f"echo '{env_content}' > /opt/stacks/synapse-app/Synapse/backend/.env && cd /opt/stacks/synapse-app/Synapse && docker compose -f web-service.yml restart synapse-api"
    stdin, stdout, stderr = ssh.exec_command(command)
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
except Exception as e:
    print(e)
finally:
    ssh.close()
