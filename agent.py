import psutil
import socket
import os

INTERVAL=1

def main():
    host = os.getenv("HOST")
    if host is None:
        print("$HOST not specified")
        exit(1)
    port = os.getenv("PORT")
    if port is None:
        print("$PORT not specified")
        exit(1)
    token = os.getenv("TOKEN")
    if token is None:
        print("$TOKEN not specified")
        exit(1)
        
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    print(f"connected to %s:%s. sending machine token" % (host, port))
    s.send(f"{token}\r\n".encode("ascii"))
    print("token accepted by server. sending metrics...")
    while True:
        cpu = psutil.cpu_percent(interval=INTERVAL) / 100
        ram_struct = psutil.virtual_memory()
        ram = ram_struct.used / ram_struct.total
        s.send(f"{cpu:.2f}:{ram:.2f}\r\n".encode("ascii"))
        print(f"cpu={cpu}, ram={ram}")
    s.close()
    
main()
