import socket

def check_port(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        result = s.connect_ex((ip, port))
        if result == 0:
            print(f"Port {port} on {ip} is OPEN")
        else:
            print(f"Port {port} on {ip} is CLOSED (errno: {result})")
    except Exception as e:
        print(f"Error checking {ip}:{port} - {str(e)}")
    finally:
        s.close()

if __name__ == "__main__":
    print("--- Tailscale ---")
    check_port("100.125.8.80", 1433)
    print("--- ZeroTier ---")
    check_port("10.147.18.192", 1433)
    print("--- Subnet ---")
    check_port("10.200.8.5", 1433)
