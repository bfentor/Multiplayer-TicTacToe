import socket
import threading
import pickle

port = 8000

global s
s = None

def connect(ip):
    global s
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
    except:
        return 1
    return 0

def queryServer():
    if s is None:
        raise RuntimeError("Socket is not connected")
    s.send("QUERY_ROOMS".encode("utf-8"))
    return pickle.loads(s.recv(1024))

def join(room: int):
    if s is None:
        raise RuntimeError("Socket is not connected")
    s.send(f"JOIN:{room}")
    data = pickle.loads(s.recv(1024))