import socket
import select
import os

HOST = "0.0.0.0"
PORT = 8080
BUFFER_SIZE = 1024
STORAGE_DIR = "storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

# store client state: normal, upload_size, upload_data, download_wait_ack
clients = {}

def handle_message(sock, data):
  message = data.decode().strip()
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
      sock.sendall(message.encode())

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # allow port to be reused immediately after restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server running on {HOST}:{PORT}")  

    poller = select.poll()
    poller.register(server, select.POLLIN)

    fd_to_socket = {server.fileno(): server}

    while True:
      events = poller.poll()

      for fd, flag in events:
        sock = fd_to_socket[fd]

        # new connection
        if sock is server:
          conn, addr = server.accept()
          print(f"Connected client from {addr}")

          conn.setblocking(False)

          poller.register(conn, select.POLLIN)
          fd_to_socket[conn.fileno()] = conn

          clients[conn] = {"mode": "normal"}

        # existing client
        else:
          try:
              data = sock.recv(BUFFER_SIZE)

              if not data: 
                raise ConnectionError()
              
              state = clients[sock]["mode"]

              if state == "normal":
                handle_message(sock, data)

              elif state == "upload_size":
                filesize = int(data.decode())

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
                # if ack is not "ok", continue looping (go back to outer loop)
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
            print(f"Error: {err}")

            poller.unregister(sock)
            sock.close()

            if sock in clients:
              del clients[sock]
            if fd in fd_to_socket:
              del fd_to_socket[fd]

if __name__ == "__main__":
  main()
              
              


