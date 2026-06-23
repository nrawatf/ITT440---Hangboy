import socket

def send_msg(sock, message):
    """Safely encodes and transmits string packets across raw network sockets."""
    try:
        encoded_data = message.encode('utf-8')
        sock.sendall(encoded_data)
        return True
    except Exception:
        return False

def recv_msg(sock):
    """Receives and decodes incoming string streaming data packets cleanly."""
    try:
        raw_data = sock.recv(4096)
        if not raw_data:
            return None
        return raw_data.decode('utf-8').strip()
    except Exception:
        return None