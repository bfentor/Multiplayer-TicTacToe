import socket
from dotenv import load_dotenv
import os
import logging
import threading
import pickle
import sys

ip = "127.0.0.1"
port = 34985
rooms = {}
socket_room = {}
wins = {}
lock = threading.Lock()

def main():
    # load_dotenv()
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        level=logging.DEBUG,
    )
    # ip = os.getenv("SERVER_IP")
    # port = int(os.getenv("PORT"))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((ip, port))
            server.listen(5)
            logging.info(f"Listening at {ip}:{port}")
            while True:
                c_socket, c_addr = server.accept()
                logging.info(f"Accepted connection from {c_addr[0]}:{c_addr[1]}")
                thread = threading.Thread(target=handleClient, args=(c_socket, c_addr), daemon=True)
                thread.start()
    except Exception as e:
        logging.critical(f"Exception occurred: {e}")

def createRoom(room_id=1):
    return {
        "matrix": [[" ", " ", " "] for _ in range(3)],
        "players": [],
        "symbols": {},
        "names": {},
        "next": "X",
        "winner": None,
        "moves": 0,
    }

def sendResponse(sock, data):
    payload = pickle.dumps(data)
    sock.sendall(len(payload).to_bytes(4, "big") + payload)


def recvRequest(sock):
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


def availableRooms():
    with lock:
        if not rooms:
            rooms[1] = createRoom(1)
        results = []
        for room_id, room in rooms.items():
            count = len(room["players"])
            status = "waiting" if count < 2 else "in progress"
            results.append(f"{room_id}. Room {room_id} ({count}/2) - {status}")
        return results


def roomForSocket(sock):
    return socket_room.get(sock)


def playerSymbol(room, sock):
    return room["symbols"].get(sock)


def currentState(room_id, message=""):
    room = rooms[room_id]
    return {
        "type": "STATE",
        "room": room_id,
        "matrix": room["matrix"],
        "next": room["next"],
        "winner": room["winner"],
        "player_count": len(room["players"]),
        "message": message,
        "player_names": {room["symbols"][sock]: room["names"][sock] for sock in room["players"]},
        "wins": {room["symbols"][sock]: wins.get(sock, 0) for sock in room["players"]},
    }


def broadcastState(room_id, exclude_sock=None, message=""):
    room = rooms[room_id]
    state = currentState(room_id, message)
    for player_sock in room["players"]:
        if player_sock is exclude_sock:
            continue
        try:
            sendResponse(player_sock, state)
        except Exception as e:
            logging.warning(f"Could not send update to opponent: {e}")


def joinRoom(room_id, sock):
    with lock:
        room = rooms.setdefault(room_id, createRoom(room_id))

        if len(room["players"]) >= 2 and sock not in room["players"]:
            return {"type": "ERROR", "message": "Room is full."}

        if sock not in room["players"]:
            symbol = "X" if len(room["players"]) == 0 else "O"
            room["players"].append(sock)
            room["symbols"][sock] = symbol
            room["names"][sock] = f"Player {len(room['players'])}"
            socket_room[sock] = room_id
        else:
            symbol = room["symbols"][sock]

        message = "Joined room. "
        if len(room["players"]) < 2:
            message += "Waiting for opponent to join."
        else:
            message += "Opponent connected. Game ready."

        state = currentState(room_id, message)
        state["type"] = "JOIN_ACK"
        state["your_symbol"] = symbol
        if len(room["players"]) == 2:
            other_sock = next(player for player in room["players"] if player is not sock)
            try:
                sendResponse(other_sock, currentState(room_id, "Opponent connected. Game ready."))
            except Exception as e:
                logging.warning(f"Could not notify waiting player: {e}")
        return state


def validMove(room, row, col):
    if row not in range(3) or col not in range(3):
        return False
    return room["matrix"][row][col] == " "


def checkWinner(matrix):
    lines = []
    lines.extend(matrix)
    lines.extend([[matrix[r][c] for r in range(3)] for c in range(3)])
    lines.append([matrix[i][i] for i in range(3)])
    lines.append([matrix[i][2 - i] for i in range(3)])
    for line in lines:
        if line[0] != " " and line.count(line[0]) == 3:
            return line[0]
    return None


def processMove(room_id, sock, row, col):
    with lock:
        if room_id not in rooms:
            return {"type": "ERROR", "message": "Room does not exist."}
        room = rooms[room_id]
        symbol = playerSymbol(room, sock)
        if symbol is None:
            return {"type": "ERROR", "message": "You are not in that room."}
        if len(room["players"]) < 2:
            state = currentState(room_id, "Waiting for opponent to join before the game begins.")
            state["type"] = "ERROR"
            return state
        if room["winner"] is not None:
            state = currentState(room_id, "Game is already over.")
            state["type"] = "ERROR"
            return state
        if symbol != room["next"]:
            state = currentState(room_id, "It is not your turn.")
            state["type"] = "ERROR"
            return state
        if not validMove(room, row, col):
            state = currentState(room_id, "Invalid move. Try again.")
            state["type"] = "ERROR"
            return state

        room["matrix"][row][col] = symbol
        room["moves"] += 1
        winner = checkWinner(room["matrix"])
        if winner:
            room["winner"] = winner
            if winner != "DRAW":
                winner_sock = next(sock for sock in room["players"] if room["symbols"][sock] == winner)
                wins[winner_sock] = wins.get(winner_sock, 0) + 1
            message = f"{winner} wins!"
        elif room["moves"] >= 9:
            room["winner"] = "DRAW"
            message = "The game is a draw."
        else:
            room["next"] = "O" if room["next"] == "X" else "X"
            message = f"Move accepted: {symbol} at {row + 1},{col + 1}."

        state = currentState(room_id, message)
        broadcastState(room_id, exclude_sock=sock, message=message)
        return state


def handleClient(c_socket, c_addr):
    try:
        while True:
            request = recvRequest(c_socket)
            if request is None:
                break
            logging.info(f"Received: {request}")

            if request == "QUERY_ROOMS":
                sendResponse(c_socket, availableRooms())
                continue

            if request.startswith("JOIN:"):
                _, room_id_text = request.split(":", 1)
                room_id = int(room_id_text)
                response = joinRoom(room_id, c_socket)
                sendResponse(c_socket, response)
                continue

            if request.startswith("MOVE:"):
                _, payload = request.split(":", 1)
                row, col = map(int, payload.split(","))
                room_id = roomForSocket(c_socket)
                if room_id is None:
                    sendResponse(c_socket, {"type": "ERROR", "message": "Not joined in any room."})
                else:
                    response = processMove(room_id, c_socket, row, col)
                    sendResponse(c_socket, response)
                continue

            if request.startswith("GET_STATE:"):
                _, room_id_text = request.split(":", 1)
                room_id = int(room_id_text)
                response = currentState(room_id, "Current board state")
                sendResponse(c_socket, response)
                continue

            if request.startswith("SET_NAME:"):
                _, name = request.split(":", 1)
                room_id = roomForSocket(c_socket)
                if room_id:
                    room = rooms[room_id]
                    room["names"][c_socket] = name
                    # broadcastState(room_id, message=f"Player {room['symbols'][c_socket]} changed name to {name}")
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
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        sys.exit()