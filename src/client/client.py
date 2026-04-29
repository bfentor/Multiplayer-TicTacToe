import socket
import pickle

port = 8000
s = None


def send_request(message: str):
    if s is None:
        raise RuntimeError("Socket is not connected")
    payload = message.encode("utf-8")
    s.sendall(len(payload).to_bytes(4, "big") + payload)


def receive_response():
    if s is None:
        raise RuntimeError("Socket is not connected")
    header = s.recv(4)
    if not header:
        raise ConnectionError("Server closed the connection")
    length = int.from_bytes(header, "big")
    data = b""
    while len(data) < length:
        packet = s.recv(length - len(data))
        if not packet:
            raise ConnectionError("Server closed the connection")
        data += packet
    return pickle.loads(data)


def connect(ip):
    global s
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
    except Exception:
        s = None
        return 1
    return 0


def queryServer():
    if s is None:
        raise RuntimeError("Socket is not connected")
    send_request("QUERY_ROOMS")
    return receive_response()


def join(room: int):
    if s is None:
        raise RuntimeError("Socket is not connected")
    send_request(f"JOIN:{room}")
    return receive_response()


def send_move(room: int, row: int, col: int):
    if s is None:
        raise RuntimeError("Socket is not connected")
    send_request(f"MOVE:{row},{col}")
    return receive_response()


def get_state(room: int):
    if s is None:
        raise RuntimeError("Socket is not connected")
    send_request(f"GET_STATE:{room}")
    return receive_response()


def set_name(name: str):
    if s is None:
        raise RuntimeError("Socket is not connected")
    send_request(f"SET_NAME:{name}")


def receive_update():
    if s is None:
        raise RuntimeError("Socket is not connected")
    return receive_response()


def close():
    global s
    if s is not None:
        try:
            send_request("QUIT")
        except Exception:
            pass
        finally:
            s.close()
            s = None
