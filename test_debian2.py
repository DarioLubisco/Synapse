import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    stdin, stdout, stderr = ssh.exec_command('cd /opt/stacks/synapse-app/Synapse && docker compose -f web-service.yml logs --tail 50 backend')
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
except Exception as e:
    print(e)
finally:
    ssh.close()
