import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Try fetching one of the endpoints
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/caja/vendedores')
    print("/caja/vendedores Response:\n", stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/caja/puntos_venta')
    print("/caja/puntos_venta Response:\n", stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command('curl -s "http://localhost:8000/api/procurement/cxp-status?cod_prov=J-412236709"')
    print("/api/procurement/cxp-status Response:\n", stdout.read().decode())
except Exception as e:
    print("Error:", e)
finally:
    ssh.close()
