import paramiko

HOST = '10.147.18.204'
REMOTE_DIR = '/opt/stacks/synapse-app/Synapse'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password='Twinc3pt.2', timeout=10)

# Ver qué CSS tiene el archivo en produccion
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && grep -n "action-bar" frontend/css/style.css')
print('[action-bar en style.css]')
print(out.read().decode())

# Ver el hash del archivo de css en produccion vs el commit
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git hash-object frontend/css/style.css')
prod_hash = out.read().decode().strip()
print(f'\n[Hash del style.css en disco]: {prod_hash}')

# Hash esperado segun el commit actual (main)
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git show HEAD:frontend/css/style.css | git hash-object --stdin')
expected_hash = out.read().decode().strip()
print(f'[Hash segun git HEAD (main)]: {expected_hash}')

if prod_hash == expected_hash:
    print('\nOK: Los archivos son identicos')
else:
    print('\nDIFERENCIA: el archivo en disco no coincide con el commit HEAD!')

# Diferencia entre dev y main en css
_, out, _ = ssh.exec_command(f'cd {REMOTE_DIR} && git diff main dev -- frontend/css/style.css --stat')
print('\n[Diff main vs dev (css)]')
print(out.read().decode())

ssh.close()
