import socket
import os

HOST = "0.0.0.0"
PORT = 8080
BUFFER_SIZE = 1024
STORAGE_DIR = "storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

def handle_client(conn, addr):
  print(f"Connected client from {addr}")

  try:
    while True:
      data = conn.recv(BUFFER_SIZE)

      if not data:
        break

      message = data.decode().strip()
      print(f"Received from {addr}: {message}")

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
        
        # ack command from client
        conn.sendall(b"ok\n")

        data_size = conn.recv(BUFFER_SIZE)
        filesize = int(data_size.decode())

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

        # wait for client ack
        ack = conn.recv(BUFFER_SIZE)

        with open(filepath, "rb") as f:
          while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
              break
            conn.sendall(chunk)

        print(f"Downloaded {filename} to {addr}  successfully")
        conn.sendall(b"Downloaded successfully")

      else:
        response = f"{message}"
        conn.sendall(response.encode())

  except Exception as err:
    print(f"Error on {addr}: {err}")

  finally:
    conn.close()
    print(f"{addr} connection disconnected")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow port to be reused immediately after restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)  

    print(f"Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        handle_client(conn, addr) 

if __name__ == "__main__":
    main()