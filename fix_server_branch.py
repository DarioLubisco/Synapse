import paramiko

HOST = '10.147.18.204'
REMOTE_DIR = '/opt/stacks/synapse-app/Synapse'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password='Twinc3pt.2', timeout=15)

print("=== Haciendo checkout a main y reset duro ===")

# Paso 1: switch a main y resetear al origin/main
_, out, err = ssh.exec_command(
    f'cd {REMOTE_DIR} && git fetch origin && git checkout main && git reset --hard origin/main'
)
print(out.read().decode())
e = err.read().decode()
if e: print('ERR:', e)

# Verificacion
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git branch && git log --oneline -2')
print('\n=== Estado post-reset ===')
print(out.read().decode())

# Verificar el HTML
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && grep "style.css" frontend/modulo_cxp.html')
print('\n=== CSS version en HTML ===')
print(out.read().decode())

# Verificar action-bar count
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && grep -c "action-bar" frontend/modulo_cxp.html')
print('\n=== action-bar count en HTML (debe ser 0 idealmente) ===')
print(out.read().decode())

# Reiniciar solo nginx (frontend) para que tome los archivos nuevos
print('\n=== Reiniciando synapse-frontend ===')
_, out, err = ssh.exec_command(
    f'cd {REMOTE_DIR} && docker compose -f web-service.yml restart synapse-frontend'
)
print(out.read().decode())
e = err.read().decode()
if e: print('ERR:', e)

print('\nDone.')
ssh.close()
