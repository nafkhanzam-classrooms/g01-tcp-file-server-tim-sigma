import socket
import os

HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 1024

def receive_full(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
    return data

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    try:
        while True:
            command = input("Command: ").strip()

            if not command:
                continue
            
            if command.startswith("/list"):
              client.sendall(command.encode())
              data = client.recv(BUFFER_SIZE)
              print("Files on server: ")
              print(data.decode())

            elif command.startswith("/upload"):
              parts = command.split()
              if len(parts) < 2:
                print("Format usage: /upload <filename>")
                continue
              
              filename = parts[1]

              # send command and wait till got ack from server
              client.sendall(command.encode())

              filesize = os.path.getsize(filename)
              client.sendall(str(filesize).encode())

              client.recv(BUFFER_SIZE)

              with open(filename, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                      break
                    client.sendall(chunk)

              result = client.recv(BUFFER_SIZE)
              print(result.decode())

            elif command.startswith("/download"):
              parts = command.split()
              if len(parts) < 2:
                  print("Format usage: /download <filename>")
                  continue
              
              filename = parts[1]

              client.sendall(command.encode())

              server_msg = client.recv(BUFFER_SIZE)
              server_search_msg = str(server_msg.decode())

              if server_search_msg == "File not found":
                print("File not found on server storage")
                continue

              # send ack
              client.sendall(b"ok\n")

              data = receive_full(client, filesize)

              with open(filename, "wb") as f:
                f.write(data)

              result = client.recv(BUFFER_SIZE)
              print(result.decode())

            else:
              client.sendall(command.encode())
              data = client.recv(BUFFER_SIZE)
              print(data.decode())

    except KeyboardInterrupt:
      print("\nConnection closed")

    finally:
       client.close()

if __name__ == "__main__":
    main()
