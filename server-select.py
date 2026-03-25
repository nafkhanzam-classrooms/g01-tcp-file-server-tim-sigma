import socket
import select
import os

HOST = "0.0.0.0"
PORT = 8080
BUFFER_SIZE = 1024
STORAGE_DIR = "storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

# Dictionary to hold states per connection
clients = {}

def broadcast(message, sender_sock):
    """
    Broadcast a message to all connected clients except the sender.
    Also sends an acknowledgment to the sender so it doesn't block.
    """
    for sock in list(clients.keys()):
        if sock != sender_sock and sock.fileno() != -1:
            try:
                sock.sendall(message.encode())
            except Exception:
                pass
    
    # Send acknowledgment to the sender
    try:
        sender_sock.sendall(b"Message broadcasted to other clients")
    except Exception:
        pass

def handle_message(sock, data):
    try:
        message = data.decode().strip()
    except UnicodeDecodeError:
        return
    
    if message:
        print(f"Received from {sock.getpeername()}: {message}")
    
    if message.startswith("/list"):
        files = os.listdir(STORAGE_DIR)
        if not files:
            sock.sendall(b"empty")
        else:
            sock.sendall("\n".join(files).encode())

    elif message.startswith("/upload"):
        parts = message.split()
        if len(parts) < 2:
            sock.sendall(b"error: filename required")
            return

        filename = parts[1]

        clients[sock]["mode"] = "upload_size"
        clients[sock]["filename"] = filename

    elif message.startswith("/download"):
        parts = message.split()
        if len(parts) < 2:
            sock.sendall(b"error: filename required")
            return

        filename = parts[1]
        filepath = os.path.join(STORAGE_DIR, filename)

        if not os.path.exists(filepath):
            sock.sendall(b"File not found")
            return

        filesize = os.path.getsize(filepath)
        sock.sendall(str(filesize).encode())

        clients[sock]["mode"] = "download_wait_ack"
        clients[sock]["filepath"] = filepath

    else:
        # Broadcast standard message
        addr = sock.getpeername()
        broadcast(f"[{addr[0]}:{addr[1]}] {message}", sock)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server running on {HOST}:{PORT}")

    inputs = [server]

    try:
        while inputs:
            readable, _, exceptional = select.select(inputs, [], inputs)

            for sock in readable:
                if sock is server:
                    # Handle new connection
                    conn, addr = server.accept()
                    print(f"Connected client from {addr}")
                    
                    # Instead of fully non-blocking, we keep default blocking socket
                    # to simplify file transfer buffering in file uploads/downloads
                    # like we do in thread, ensuring large files don't hit BlockingIOError
                    inputs.append(conn)
                    clients[conn] = {"mode": "normal"}
                else:
                    try:
                        data = sock.recv(BUFFER_SIZE)

                        if not data:
                            raise ConnectionError("Client disconnected")

                        state = clients[sock]["mode"]

                        if state == "normal":
                            handle_message(sock, data)

                        elif state == "upload_size":
                            try:
                                filesize = int(data.decode().strip())
                            except ValueError:
                                sock.sendall(b"error: invalid file size")
                                clients[sock]["mode"] = "normal"
                                continue
                                
                            clients[sock]["mode"] = "upload_data"
                            clients[sock]["filesize"] = filesize
                            clients[sock]["received"] = 0
                            
                            filepath = os.path.join(STORAGE_DIR, clients[sock]["filename"])
                            clients[sock]["file"] = open(filepath, "wb")
                            
                            # ack command from client
                            sock.sendall(b"ok\n")

                        elif state == "upload_data":
                            f = clients[sock]["file"]
                            f.write(data)
                            clients[sock]["received"] += len(data)

                            if clients[sock]["received"] >= clients[sock]["filesize"]:
                                f.close()
                                print(f"Uploaded {clients[sock]['filename']} successfully")
                                sock.sendall(b"Uploaded successfully")
                                clients[sock]["mode"] = "normal"

                        elif state == "download_wait_ack":
                            if data.decode().strip() != "ok":
                                continue

                            filepath = clients[sock]["filepath"]
                            with open(filepath, "rb") as f:
                                while True:
                                    chunk = f.read(BUFFER_SIZE)
                                    if not chunk:
                                        break
                                    sock.sendall(chunk)

                            print(f"Downloaded {filepath} successfully")
                            sock.sendall(b"Downloaded successfully")
                            clients[sock]["mode"] = "normal"

                    except Exception as err:
                        if hasattr(sock, "getpeername"):
                            print(f"Error handling {sock.getpeername()}: {err}")
                        else:
                            print(f"Error handling disconnected client: {err}")
                            
                        if sock in inputs:
                            inputs.remove(sock)
                        if sock in clients:
                            if "file" in clients[sock] and not clients[sock]["file"].closed:
                                clients[sock]["file"].close()
                            del clients[sock]
                        sock.close()

            for sock in exceptional:
                if sock in inputs:
                    inputs.remove(sock)
                if sock in clients:
                    if "file" in clients[sock] and not clients[sock]["file"].closed:
                        clients[sock]["file"].close()
                    del clients[sock]
                sock.close()
                
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
