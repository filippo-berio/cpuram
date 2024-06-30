import socket
import sqlite3
import time
import os

MAX_CONNS=10

db_conn = sqlite3.connect("cpuram.db")
db = db_conn.cursor()

def handle_conn(c):
    mach_token_b = c.recv(34)
    if not mach_token_b:
        print(f"closing connection")
        return
        
    mach_token = mach_token_b.decode("ascii")
    mach_token = mach_token[:len(mach_token)-2] # \r\n
    res = db.execute("select name from machines where token = ?", (mach_token,))
    row = res.fetchone()
    if row == None:
        print(f"machine {mach_token} not found")
        c.close()
        return
    mach_name = row[0]
    print(f"{mach_name}: connected. gathering info...")
    while True:
        metrics_b = c.recv(34)
        if not metrics_b:
            print(f"{mach_name}: closing connection")
            break
        metrics = metrics_b.decode("ascii")
        metrics = metrics[:len(metrics)-2]
        parts = metrics.split(":")
        if len(parts) != 2:
            print(f"{mach_name}: invalid metrics {metrics}")
            c.close()
            break
        (cpu, ram) = parts
        print(f"{mach_name}: cpu percent is {cpu}, RAM percent is {ram}")
        db.execute("insert into metrics (machine, cpu, ram, ts) values (?, ?, ?, ?)", (mach_token, cpu, ram, int(time.time())))
        db_conn.commit()
        
        
    
def main():
      
    host = os.getenv("HOST")
    if host is None:
        print("$HOST not specified")
        exit(1)
    port = os.getenv("PORT")
    if port is None:
        print("$PORT not specified")
        exit(1)
        
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1);
    s.bind((host, int(port)))
    s.listen(MAX_CONNS)
    print(f"Listening tcp connections at {host}:{port}")
    while True:
        c, addr = s.accept()
        print("Connection from %s:%s" % addr)
        with c:
            handle_conn(c)

main()
