import socket
from dotenv import load_dotenv
import os
import logging
import threading
import pickle

port = 8000
rooms = {}
socket_room = {}
lock = threading.Lock()


def create_room(room_id=1):
    return {
        "matrix": [[" ", " ", " "] for _ in range(3)],
        "players": [],
        "symbols": {},
        "next": "X",
        "winner": None,
        "moves": 0,
    }


def send_response(sock, data):
    payload = pickle.dumps(data)
    sock.sendall(len(payload).to_bytes(4, "big") + payload)


def recv_request(sock):
    header = sock.recv(4)
    if not header:
        return None
    length = int.from_bytes(header, "big")
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return data.decode("utf-8")


def available_rooms():
    with lock:
        if not rooms:
            rooms[1] = create_room(1)
        results = []
        for room_id, room in rooms.items():
            count = len(room["players"])
            status = "waiting" if count < 2 else "in progress"
            results.append(f"{room_id}. Room {room_id} ({count}/2) - {status}")
        return results


def room_for_socket(sock):
    return socket_room.get(sock)


def player_symbol(room, sock):
    return room["symbols"].get(sock)


def current_state(room_id, message=""):
    room = rooms[room_id]
    return {
        "type": "STATE",
        "room": room_id,
        "matrix": room["matrix"],
        "next": room["next"],
        "winner": room["winner"],
        "player_count": len(room["players"]),
        "message": message,
    }


def join_room(room_id, sock):
    with lock:
        room = rooms.setdefault(room_id, create_room(room_id))

        if len(room["players"]) >= 2 and sock not in room["players"]:
            return {"type": "ERROR", "message": "Room is full."}

        if sock not in room["players"]:
            symbol = "X" if len(room["players"]) == 0 else "O"
            room["players"].append(sock)
            room["symbols"][sock] = symbol
            socket_room[sock] = room_id
        else:
            symbol = room["symbols"][sock]

        message = "Joined room. "
        if len(room["players"]) < 2:
            message += "Waiting for opponent to join."
        else:
            message += "Opponent connected. Game ready."

        state = current_state(room_id, message)
        state["type"] = "JOIN_ACK"
        state["your_symbol"] = symbol
        return state


def valid_move(room, row, col):
    if row not in range(3) or col not in range(3):
        return False
    return room["matrix"][row][col] == " "


def check_winner(matrix):
    lines = []
    lines.extend(matrix)
    lines.extend([[matrix[r][c] for r in range(3)] for c in range(3)])
    lines.append([matrix[i][i] for i in range(3)])
    lines.append([matrix[i][2 - i] for i in range(3)])
    for line in lines:
        if line[0] != " " and line.count(line[0]) == 3:
            return line[0]
    return None


def process_move(room_id, sock, row, col):
    with lock:
        if room_id not in rooms:
            return {"type": "ERROR", "message": "Room does not exist."}
        room = rooms[room_id]
        symbol = player_symbol(room, sock)
        if symbol is None:
            return {"type": "ERROR", "message": "You are not in that room."}
        if len(room["players"]) < 2:
            state = current_state(room_id, "Waiting for opponent to join before the game begins.")
            state["type"] = "ERROR"
            return state
        if room["winner"] is not None:
            state = current_state(room_id, "Game is already over.")
            state["type"] = "ERROR"
            return state
        if symbol != room["next"]:
            state = current_state(room_id, "It is not your turn.")
            state["type"] = "ERROR"
            return state
        if not valid_move(room, row, col):
            state = current_state(room_id, "Invalid move. Try again.")
            state["type"] = "ERROR"
            return state

        room["matrix"][row][col] = symbol
        room["moves"] += 1
        winner = check_winner(room["matrix"])
        if winner:
            room["winner"] = winner
            message = f"{winner} wins!"
        elif room["moves"] >= 9:
            room["winner"] = "DRAW"
            message = "The game is a draw."
        else:
            room["next"] = "O" if room["next"] == "X" else "X"
            message = f"Move accepted: {symbol} at {row + 1},{col + 1}."

        return current_state(room_id, message)


def handle_client(c_socket, c_addr):
    try:
        while True:
            request = recv_request(c_socket)
            if request is None:
                break
            logging.info(f"Received: {request}")

            if request == "QUERY_ROOMS":
                send_response(c_socket, available_rooms())
                continue

            if request.startswith("JOIN:"):
                _, room_id_text = request.split(":", 1)
                room_id = int(room_id_text)
                response = join_room(room_id, c_socket)
                send_response(c_socket, response)
                continue

            if request.startswith("MOVE:"):
                _, payload = request.split(":", 1)
                row, col = map(int, payload.split(","))
                room_id = room_for_socket(c_socket)
                if room_id is None:
                    send_response(c_socket, {"type": "ERROR", "message": "Not joined in any room."})
                else:
                    response = process_move(room_id, c_socket, row, col)
                    send_response(c_socket, response)
                continue

            if request.startswith("GET_STATE:"):
                _, room_id_text = request.split(":", 1)
                room_id = int(room_id_text)
                response = current_state(room_id, "Current board state")
                send_response(c_socket, response)
                continue

            if request.startswith("QUIT"):
                break
    except Exception as e:
        logging.critical(f"Error when handling client: {e}")
    finally:
        with lock:
            room_id = socket_room.pop(c_socket, None)
            if room_id and room_id in rooms:
                room = rooms[room_id]
                if c_socket in room["players"]:
                    room["players"].remove(c_socket)
                    room["symbols"].pop(c_socket, None)
                if not room["players"]:
                    rooms.pop(room_id, None)
        c_socket.close()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        level=logging.DEBUG,
    )
    ip = os.getenv("SERVER_IP")
    port = int(os.getenv("PORT"))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((ip, port))
            server.listen(5)
            logging.info(f"Listening at {ip}:{port}")
            while True:
                c_socket, c_addr = server.accept()
                logging.info(f"Accepted connection from {c_addr[0]}:{c_addr[1]}")
                thread = threading.Thread(target=handle_client, args=(c_socket, c_addr), daemon=True)
                thread.start()
    except Exception as e:
        logging.critical(f"Exception occurred: {e}")
