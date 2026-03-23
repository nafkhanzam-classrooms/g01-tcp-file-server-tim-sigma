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
