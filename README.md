[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)

# Network Programming - Assignment G01

## Anggota Kelompok

| Nama                   | NRP        | Kelas |
| ---------------------- | ---------- | ----- |
| Farras Nazhif Pratikno | 5025241260 | D     |
|                        |            |       |

## Link Youtube (Unlisted)

Link ditaruh di bawah ini

```

```

## Penjelasan Program

### Broadcast Messages

1. `/list`: menampilkan semua file yang ada di folder storage (dari server).
2. `/upload`: meng-upload file yang berada di luar folder storage (namun masih di dalam project) ke folder storage (dari server).
3. `/download`: men-download file yang berada di folder storage (dari server) ke dalam project.

### Client Code

1. Inisialisasi koneksi

```python
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
```

2. Fungsi `receive_full`

- Menerima data dari socket sampai jumlah byte tertentu (size) terpenuhi

```python
def receive_full(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
    return data
```

3. List command

- Mengirim command ke server, lalu menerima data dari server

```python
if command.startswith("/list"):
  client.sendall(command.encode())
  data = client.recv(BUFFER_SIZE)
  print("Files on server: ")
  print(data.decode())
```

4. Upload command

```python
elif command.startswith("/upload"):
  # split & check command format
  parts = command.split()
  if len(parts) < 2:
    print("Format usage: /upload <filename>")
    continue

  # parse filename
  filename = parts[1]

  # send command and wait till got ack from server
  client.sendall(command.encode())

  # get file size
  filesize = os.path.getsize(filename)
  # send filesize into server
  client.sendall(str(filesize).encode())

  # receive data from server (response)
  client.recv(BUFFER_SIZE)

  # read file and send it to server
  with open(filename, "rb") as f:
    while True:
        chunk = f.read(BUFFER_SIZE)
        if not chunk:
          break
        client.sendall(chunk)

  # receive & print result message from server
  result = client.recv(BUFFER_SIZE)
  print(result.decode())
```

5. Download command

```python
elif command.startswith("/download"):
  # split & check command format
  parts = command.split()
  if len(parts) < 2:
      print("Format usage: /download <filename>")
      continue

  # parse filename
  filename = parts[1]

  # send command to server
  client.sendall(command.encode())

  # receive server message & check the search result
  server_msg = client.recv(BUFFER_SIZE)
  server_search_msg = str(server_msg.decode())

  if server_search_msg == "File not found":
    print("File not found on server storage")
    continue

  # parse filesize from server
  filesize = int(server_search_msg)

  # send ack
  client.sendall(b"ok\n")

  # receive data from server (response)
  data = receive_full(client, filesize)

  # write the file into client
  with open(filename, "wb") as f:
    f.write(data)

  # receive & print result message from server
  result = client.recv(BUFFER_SIZE)
  print(result.decode())
```

### Synchronous Server Code

1. Inisialisasi koneksi

```python
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# allow port to be reused immediately after restart
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)
```

2. List command

- Menggunakan `os.listdir` untuk melihat file yang berada di dalam folder tertentu.
- Kirim file-file tersebut ke client dengan ` conn.sendall("\n".join(files).encode())`.

```python
if message.startswith("/list"):
  files = os.listdir(STORAGE_DIR)
  if not files:
    conn.sendall(b"empty")
  else:
    conn.sendall("\n".join(files).encode())
```

3. Upload command

```python
elif message.startswith("/upload"):
  # split & check command format
  parts = message.split()
  if len(parts) < 2:
    conn.sendall(b"error: filename required")
    continue

  # parse filename
  filename = parts[1]

  # ack command from client
  conn.sendall(b"ok\n")

  # receive data size from client & parse it into filesize
  data_size = conn.recv(BUFFER_SIZE)
  filesize = int(data_size.decode())

  # get filepath
  filepath = os.path.join(STORAGE_DIR, filename)

  # write the uploaded file from client
  with open(filepath, "wb") as f:
    received = 0
    while received < filesize:
      chunk = conn.recv(BUFFER_SIZE)
      if not chunk:
        break
      f.write(chunk)
      received += len(chunk)

  # print log for server and send message to client
  print(f"Uploaded {filename} from {addr} successfully")
  conn.sendall(b"Uploaded successfully")
```

4. Download command

```python
elif message.startswith("/download"):
  # split & check command format
  parts = message.split()
  if len(parts) < 2:
    conn.sendall(b"error: filename required")
    continue

  # parse filename & get filepath
  filename = parts[1]
  filepath = os.path.join(STORAGE_DIR, filename)

  # send "not found" message to client if filepath not exists
  if not os.path.exists(filepath):
    conn.sendall(b"File not found")
    continue

  # get filesize & send it to client
  filesize = os.path.getsize(filepath)
  conn.sendall(str(filesize).encode())

  # wait for client ack
  ack = conn.recv(BUFFER_SIZE)

  # read file and send it to client
  with open(filepath, "rb") as f:
    while True:
      chunk = f.read(BUFFER_SIZE)
      if not chunk:
        break
      conn.sendall(chunk)

  # print log for server and send message to client
  print(f"Downloaded {filename} to {addr}  successfully")
  conn.sendall(b"Downloaded successfully")
```

### Cara Menjalankan program

- Pilih salah satu server yang ingin dijalankan

```bash
python server-sync.py
python server-select.py
python server-poll.py
python server-thread.py
```

- Jalankan client

```bash
python client.py
```

## Screenshot Hasil

### Synchronous Server

- Server

![Synchronous Server Result](docs/server-sync.png)

- Client 1

![Synchronous Client Result](docs/client-sync.png)

### Server with Poll

- Server

![Server with Poll Result](docs/server-poll-1.png)

- Client 1

![Client with Poll Result](docs/client-1-poll.png)

- Client 2

![Client with Poll Result](docs/client-2-poll.png)
