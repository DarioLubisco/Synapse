import paramiko

HOST = '10.147.18.204'
REMOTE_DIR = '/opt/stacks/synapse-app/Synapse'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password='Twinc3pt.2', timeout=15)

print("=== Haciendo fetch y reset duro a origin/main ===")

# Paso 1: switch a main y resetear al origin/main
_, out, err = ssh.exec_command(
    f'cd {REMOTE_DIR} && git fetch origin && git checkout main && git reset --hard origin/main'
)
print(out.read().decode())
e = err.read().decode()
if e: print('ERR:', e)

# Reiniciar contenedores
print('\n=== Reiniciando synapse-api y synapse-frontend ===')
_, out, err = ssh.exec_command(
    f'cd {REMOTE_DIR} && docker compose -f web-service.yml up -d --build synapse-api synapse-frontend'
)
print(out.read().decode())
e = err.read().decode()
if e: print('ERR:', e)

print('\nDone.')
ssh.close()
