import socket
import os
import threading

HOST = "0.0.0.0"
PORT = 8080
BUFFER_SIZE = 1024
STORAGE_DIR = "storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

# List to keep track of all connected client sockets
clients = []
clients_lock = threading.Lock()

def broadcast(message, sender_conn):
    """
    Broadcast a message to all connected clients except the sender.
    Also sends an acknowledgment to the sender so it doesn't block.
    """
    with clients_lock:
        for client in clients:
            if client != sender_conn:
                try:
                    client.sendall(message.encode())
                except Exception:
                    # Ignore disconnected clients; they will be removed in their thread
                    pass
    
    # Send acknowledgment to the sender
    try:
        sender_conn.sendall(b"Message broadcasted to other clients")
    except Exception:
        pass

def handle_client(conn, addr):
    """
    Handle a single client connection within a thread.
    """
    print(f"Connected client from {addr}")
    
    with clients_lock:
        clients.append(conn)

    try:
        while True:
            data = conn.recv(BUFFER_SIZE)

            if not data:
                break

            # Try to decode the initial command
            try:
                message = data.decode().strip()
                if message:
                    print(f"Received from {addr}: {message}")
            except UnicodeDecodeError:
                continue

            if message.startswith("/list"):
                files = os.listdir(STORAGE_DIR)
                if not files:
                    conn.sendall(b"empty")
                else:
                    conn.sendall("\n".join(files).encode())

            elif message.startswith("/upload"):
                parts = message.split()
                if len(parts) < 2:
                    conn.sendall(b"error: filename required")
                    continue

                filename = parts[1]
                
                # ack command from client (required by client logic)
                conn.sendall(b"ok\n")

                # wait for filesize
                data_size = conn.recv(BUFFER_SIZE)
                try:
                    filesize = int(data_size.decode().strip())
                except ValueError:
                    conn.sendall(b"error: invalid file size")
                    continue

                filepath = os.path.join(STORAGE_DIR, filename)

                with open(filepath, "wb") as f:
                    received = 0
                    while received < filesize:
                        chunk = conn.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)

                print(f"Uploaded {filename} from {addr} successfully")
                conn.sendall(b"Uploaded successfully")

            elif message.startswith("/download"):
                parts = message.split()
                if len(parts) < 2:
                    conn.sendall(b"error: filename required")
                    continue

                filename = parts[1]
                filepath = os.path.join(STORAGE_DIR, filename)

                if not os.path.exists(filepath):
                    conn.sendall(b"File not found")
                    continue

                filesize = os.path.getsize(filepath)
                conn.sendall(str(filesize).encode())

                # wait for client ack ("ok\n")
                ack = conn.recv(BUFFER_SIZE)

                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        conn.sendall(chunk)

                print(f"Downloaded {filename} to {addr} successfully")
                conn.sendall(b"Downloaded successfully")

            else:
                # If not a command, it's a normal message to be broadcasted
                broadcast(f"[{addr[0]}:{addr[1]}] {message}", conn)

    except Exception as err:
        print(f"Error on {addr}: {err}")

    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"{addr} connection disconnected")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow port to be reused immediately after restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(5)  

    print(f"Server running on {HOST}:{PORT}")

    try:
        while True:
            # Main thread accepts connections
            conn, addr = server.accept()
            
            # Create and start a new thread for each client
            # Setting daemon=True ensures threads exit when main program closes
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
