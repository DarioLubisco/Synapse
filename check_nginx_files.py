import paramiko

HOST = '10.147.18.204'
REMOTE_DIR = '/opt/stacks/synapse-app/Synapse'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password='Twinc3pt.2', timeout=10)

# Verificar hash del HTML actual en disco vs HEAD
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git hash-object frontend/modulo_cxp.html')
prod_hash = out.read().decode().strip()
print(f'[Hash modulo_cxp.html en disco]: {prod_hash}')

_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git show HEAD:frontend/modulo_cxp.html | git hash-object --stdin')
expected_hash = out.read().decode().strip()
print(f'[Hash segun git HEAD (main)]: {expected_hash}')

if prod_hash == expected_hash:
    print('OK: HTML identico al commit')
else:
    print('DIFERENCIA detectada!')

# Diferencia de HTML entre main y dev
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git diff main dev -- frontend/modulo_cxp.html --stat')
print('\n[Diff main vs dev (html)]')
print(out.read().decode())

# Ver el container nginx y que archivos sirve
_, out, _ = ssh.exec_command('docker inspect synapse-frontend --format "{{range .Mounts}}{{.Source}} -> {{.Destination}}\\n{{end}}"')
print('\n[Volumenes de synapse-frontend]')
print(out.read().decode())

ssh.close()
