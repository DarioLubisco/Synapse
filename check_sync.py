import paramiko
import hashlib
import os

HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"

# Genera diccionarios path: md5
def hash_local_directory(path):
    hashes = {}
    for root, _, files in os.walk(path):
        if '__pycache__' in root or '.git' in root or '.venv' in root or 'node_modules' in root:
            continue
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, r"c:\source\Synapse").replace('\\', '/')
            with open(file_path, "rb") as f:
                hashes[rel_path] = hashlib.md5(f.read()).hexdigest()
    return hashes

def get_remote_hashes():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    hashes = {}
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        command = "cd /opt/stacks/synapse-app/Synapse && find . -type f -not -path '*/\.*' -not -path '*/__pycache__*' -not -path '*/node_modules*' -not -path '*/.venv*' -exec md5sum {} +"
        stdin, stdout, stderr = ssh.exec_command(command)
        lines = stdout.read().decode('utf-8').splitlines()
        for line in lines:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                md5_hash, file_path_raw = parts
                rel_path = file_path_raw.lstrip('./').replace('\\', '/')
                hashes[rel_path] = md5_hash
    except Exception as e:
        print(f"Error connect SSH: {e}")
    finally:
        ssh.close()
    return hashes

print("Calculando hashes locales...")
local_hashes = hash_local_directory(r"c:\source\Synapse")
print("Calculando hashes remotos...")
remote_hashes = get_remote_hashes()

print("Comparando...")
differences = []
only_local = []
only_remote = []

for rel_path, l_hash in local_hashes.items():
    if rel_path not in remote_hashes:
        only_local.append(rel_path)
    elif remote_hashes[rel_path] != l_hash:
        differences.append(rel_path)

for rel_path in remote_hashes.keys():
    if rel_path not in local_hashes:
        only_remote.append(rel_path)

if not differences and not only_local and not only_remote:
    print("\n[OK] Todos los codigos son IDENTICOS entre local y produccion!")
else:
    print("\n[FAIL] Se encontraron diferencias:")
    if differences:
        print(" Archivos modificados (distintos):")
        for f in differences: print(f"   - {f}")
    if only_local:
        print("\n Archivos solo en LOCAL (no en PROD):")
        for f in only_local: print(f"   - {f}")
    if only_remote:
        print("\n Archivos solo en PROD (no en LOCAL):")
        for f in only_remote: print(f"   - {f}")
