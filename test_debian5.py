import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('10.147.18.204', username='root', password='Twinc3pt.2', timeout=5)
    
    # Check if Debian can ping the SQL server
    stdin, stdout, stderr = ssh.exec_command('ping -c 3 10.200.8.5')
    print("PING 10.200.8.5:")
    print(stdout.read().decode())
    
    # Check if port 1433 is open
    stdin, stdout, stderr = ssh.exec_command('nc -zv 10.200.8.5 1433')
    print("NC PORT 1433:")
    print(stdout.read().decode())
    print(stderr.read().decode())
except Exception as e:
    print(e)
finally:
    ssh.close()
