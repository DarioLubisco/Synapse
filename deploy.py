"""
@ship - Synapse Deploy Script
==============================
Uso desde PowerShell:   python deploy.py
Uso con alias global:   ship

Que hace:
  1. Merge de dev -> main (opcional, si estas en dev)
  2. Push a GitHub
  3. SSH al servidor -> git pull -> docker restart
"""
import os
import sys
import subprocess
import paramiko

# ── Configuracion del servidor ──────────────────────────────
HOST       = "10.147.18.204"
USER       = "root"
PASSWORD   = "Twinc3pt.2"
REMOTE_DIR = "/opt/stacks/synapse-app/Synapse"
LOCAL_DIR  = r"c:\source\Synapse"

# ── Colores para la consola ─────────────────────────────────
OK   = "\033[92m[OK]\033[0m"
ERR  = "\033[91m[ERROR]\033[0m"
INFO = "\033[94m[>>]\033[0m"
WARN = "\033[93m[!]\033[0m"

def run_local(cmd, cwd=LOCAL_DIR):
    """Ejecuta un comando local y muestra output en tiempo real."""
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode == 0

def run_git(args, cwd=LOCAL_DIR):
    """Ejecuta git con lista de argumentos (sin problemas de quoting en Windows)."""
    result = subprocess.run(["git"] + args, cwd=cwd)
    return result.returncode == 0

def git_push():
    """Merge dev->main y push a GitHub."""
    print(f"\n{INFO} Paso 1: Subiendo codigo a GitHub...")

    # Detectar rama actual
    result = subprocess.run(["git", "branch", "--show-current"], cwd=LOCAL_DIR, capture_output=True, text=True)
    current_branch = result.stdout.strip()
    print(f"   Rama actual: {current_branch}")

    if current_branch == "dev":
        print(f"   Mergeando dev -> main...")
        if not run_git(["checkout", "main"]):
            print(f"{ERR} Error al cambiar a main"); return False
        if not run_git(["merge", "dev", "--no-ff", "-m", "deploy: merge dev into main"]):
            print(f"{ERR} Error en merge"); run_git(["checkout", "dev"]); return False

    if not run_git(["push", "origin", "main"]):
        print(f"{ERR} Error en git push"); return False

    # Volver a dev si veniamos de ahi, y push dev tambien. Si estabamos en main, sincronizar dev con main.
    if current_branch == "dev":
        run_git(["checkout", "dev"])
        run_git(["push", "origin", "dev"])  # mantener dev actualizado en GitHub
    elif current_branch == "main":
        print(f"   Sincronizando la rama dev con los cambios hechos en main...")
        run_git(["checkout", "dev"])
        run_git(["merge", "main", "-m", "deploy: sync main into dev"])
        run_git(["push", "origin", "dev"])
        run_git(["checkout", "main"])

    print(f"{OK} Codigo subido a GitHub (Ambas ramas alineadas)")
    return True

def deploy_server():
    """SSH al servidor: git pull + docker restart."""
    print(f"\n{INFO} Paso 2: Conectando al servidor {HOST}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        print(f"{OK} Conectado via SSH")

        # Comandos a ejecutar en el servidor
        commands = [
            f"cd {REMOTE_DIR} && git pull origin main",
            f"cd {REMOTE_DIR} && docker compose -f web-service.yml up -d --build",
        ]

        labels = [
            "Bajando codigo nuevo del servidor...",
            "Reiniciando Docker (puede tardar 1-2 min)...",
        ]

        for label, cmd in zip(labels, commands):
            print(f"\n   {label}")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
            out = stdout.read().decode('utf-8', errors='ignore').strip()
            err = stderr.read().decode('utf-8', errors='ignore').strip()
            if out: print(f"   {out}")
            if err and "error" in err.lower(): print(f"{WARN} {err}")

        print(f"\n{OK} Servidor actualizado. Abre http://amc.synapse/ para verificar.")

    except Exception as e:
        print(f"{ERR} Error SSH: {e}")
        return False
    finally:
        ssh.close()

    return True

if __name__ == "__main__":
    print("=" * 50)
    print("  >> @ship  Synapse Deploy")
    print("=" * 50)

    if not git_push():
        sys.exit(1)

    if not deploy_server():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  [OK]  Deploy completado exitosamente!")
    print("=" * 50)
