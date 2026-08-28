import socket

HOST = "192.168.86.160"   # replace with your printer IP
PORT = 9100

payload = (
    b"\x1b\x40"                 # ESC @ initialize
    b"\n"
    b"HELLO\n"
    b"WORLD\n"
    b"\n"
    b"\x1d\x56\x00"
)

with socket.create_connection((HOST, PORT), timeout=5) as sock:
    sock.sendall(payload)

print("sent")