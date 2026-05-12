import paramiko

HOST = '10.147.18.204'
REMOTE_DIR = '/opt/stacks/synapse-app/Synapse'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username='root', password='Twinc3pt.2', timeout=10)

cmds = {
    'Rama actual': f'cd {REMOTE_DIR} && git branch',
    'Ultimo commit': f'cd {REMOTE_DIR} && git log --oneline -3',
    'CSS version en HTML': f'cd {REMOTE_DIR} && grep "style.css" frontend/modulo_cxp.html',
    'action-bar en CSS': f'cd {REMOTE_DIR} && grep -c "action-bar" frontend/css/style.css',
    'action-bar en HTML': f'cd {REMOTE_DIR} && grep -c "action-bar" frontend/modulo_cxp.html',
    'Remote branches': f'cd {REMOTE_DIR} && git branch -a',
}

for label, cmd in cmds.items():
    _, out, err = ssh.exec_command(cmd)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    print(f'\n[{label}]')
    if o: print(f'  {o}')
    if e: print(f'  ERR: {e}')

ssh.close()
