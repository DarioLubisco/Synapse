import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=10)

def do_ping(ip):
    print(f"--- Pinging {ip} ---")
    stdin, stdout, stderr = ssh.exec_command(f'ping -c 3 {ip}')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))

# IPs requested: 10.147.18.43 (Local ZT), 10.147.18.192 (SQL ZT), 100.125.8.80 (SQL TS)
do_ping('10.147.18.43')
do_ping('10.147.18.192')
do_ping('100.125.8.80')

ssh.close()
