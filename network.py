import socket
import threading
import time
import os
from PyQt5.QtCore import QObject, pyqtSignal

UDP_PORT = 5000
TCP_PORT = 5001
BROADCAST_INTERVAL = 2  # seconds
PEER_TIMEOUT = 10  # seconds
CHUNK_SIZE = 8192

class NetworkManager(QObject):
    peer_discovered = pyqtSignal(str)
    peer_lost = pyqtSignal(str)
    transfer_progress = pyqtSignal(str, int)  # filename, percentage
    transfer_complete = pyqtSignal(str) # filename
    receive_progress = pyqtSignal(str, int)
    receive_complete = pyqtSignal(str)
    
    def __init__(self, download_dir):
        super().__init__()
        self.download_dir = download_dir
        self.peers = {}  # ip: last_seen_time
        
        self.running = True
        
        # Start UDP Discovery threads
        self.udp_thread = threading.Thread(target=self.udp_discovery_loop, daemon=True)
        self.udp_thread.start()
        
        self.udp_broadcast_thread = threading.Thread(target=self.udp_broadcast_loop, daemon=True)
        self.udp_broadcast_thread.start()
        
        # Start TCP Receiver thread
        self.tcp_receiver_thread = threading.Thread(target=self.tcp_receive_loop, daemon=True)
        self.tcp_receiver_thread.start()
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def udp_broadcast_loop(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.running:
            try:
                s.sendto(b"DROPZONE_HELLO", ("<broadcast>", UDP_PORT))
            except Exception:
                pass
            time.sleep(BROADCAST_INTERVAL)
        s.close()
        
    def udp_discovery_loop(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow multiple local instances to bind to the same port for testing
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass
            
        s.bind(("", UDP_PORT))
        
        local_ip = self.get_local_ip()
        
        while self.running:
            try:
                s.settimeout(1.0)
                data, addr = s.recvfrom(1024)
                if data == b"DROPZONE_HELLO" and addr[0] != local_ip:
                    ip = addr[0]
                    if ip not in self.peers:
                        self.peers[ip] = time.time()
                        self.peer_discovered.emit(ip)
                    else:
                        self.peers[ip] = time.time()
            except socket.timeout:
                pass
            except Exception:
                pass
            
            # Clean up stale peers
            current_time = time.time()
            stale_peers = [ip for ip, last_seen in self.peers.items() if current_time - last_seen > PEER_TIMEOUT]
            for ip in stale_peers:
                del self.peers[ip]
                self.peer_lost.emit(ip)
                
        s.close()

    def tcp_receive_loop(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass
            
        s.bind(("0.0.0.0", TCP_PORT))
        s.listen(5)
        
        while self.running:
            try:
                s.settimeout(1.0)
                client_sock, addr = s.accept()
                threading.Thread(target=self.handle_incoming_file, args=(client_sock,), daemon=True).start()
            except socket.timeout:
                pass
            except Exception:
                pass
        s.close()

    def handle_incoming_file(self, client_sock):
        try:
            name_len_data = client_sock.recv(4)
            if not name_len_data: return
            name_len = int.from_bytes(name_len_data, 'big')
            
            filename_data = client_sock.recv(name_len)
            filename = filename_data.decode('utf-8')
            
            size_data = client_sock.recv(8)
            file_size = int.from_bytes(size_data, 'big')
            
            save_path = os.path.join(self.download_dir, filename)
            
            # Handle duplicate filename
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(self.download_dir, f"{base}_{counter}{ext}")
                counter += 1
                
            received = 0
            with open(save_path, 'wb') as f:
                while received < file_size:
                    chunk = client_sock.recv(min(CHUNK_SIZE, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    
                    if file_size > 0:
                        progress = int((received / file_size) * 100)
                        self.receive_progress.emit(filename, progress)
                        
            self.receive_complete.emit(filename)
        except Exception as e:
            print(f"Error receiving file: {e}")
        finally:
            client_sock.close()

    def send_file(self, file_path, target_ip):
        def _send():
            try:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target_ip, TCP_PORT))
                
                name_bytes = filename.encode('utf-8')
                s.sendall(len(name_bytes).to_bytes(4, 'big'))
                s.sendall(name_bytes)
                s.sendall(file_size.to_bytes(8, 'big'))
                
                sent = 0
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        s.sendall(chunk)
                        sent += len(chunk)
                        if file_size > 0:
                            progress = int((sent / file_size) * 100)
                            self.transfer_progress.emit(filename, progress)
                
                self.transfer_complete.emit(filename)
                s.close()
            except Exception as e:
                print(f"Error sending file {os.path.basename(file_path)} to {target_ip}: {e}")
                
        threading.Thread(target=_send, daemon=True).start()

    def get_active_peers(self):
        return list(self.peers.keys())

    def stop(self):
        self.running = False
