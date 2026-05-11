import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    stdin, stdout, stderr = ssh.exec_command('cd /opt/stacks/synapse-app/Synapse && docker compose -f web-service.yml ps')
    print("STDOUT web-service.yml:")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('cd /opt/stacks/synapse-app/Synapse && docker compose -f docker-compose.yml ps')
    print("STDOUT docker-compose.yml:")
    print(stdout.read().decode())
    
    # Also grab the backend logs assuming it's named synapse-backend or similar
    stdin, stdout, stderr = ssh.exec_command('cd /opt/stacks/synapse-app/Synapse && docker compose -f web-service.yml logs --tail 20')
    print("LOGS web-service.yml:")
    print(stdout.read().decode())
except Exception as e:
    print(e)
finally:
    ssh.close()
