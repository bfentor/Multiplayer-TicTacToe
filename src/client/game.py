import sys
from time import sleep
import os
import client


def main():
    menu()


def menu():
    title = r'''
        ,----,                           ,----,                            ,----,                   
      ,/   .`|                         ,/   .`|                          ,/   .`|                   
    ,`   .'  :                       ,`   .'  :                        ,`   .'  :                   
  ;    ;     / ,--,                ;    ;     /                      ;    ;     /                   
.'___,/    ,',--.'|              .'___,/    ,'                     .'___,/    ,'  ,---.             
|    :     | |  |,               |    :     |                      |    :     |  '   ,"\            
;    |.';  ; `--'_       ,---.   ;    |.';  ;  ,--.--.     ,---.   ;    |.';  ; /   /   |   ,---.   
`----'  |  | ,' ,'|     /     \  `----'  |  | /       \   /     \  `----'  |  |.   ; ,. :  /     \  
    '   :  ; '  | |    /    / '      '   :  ;.--.  .-. | /    / '      '   :  ;'   | |: : /    /  | 
    |   |  ' |  | :   .    ' /       |   |  ' \__\/: . ..    ' /       |   |  ''   | .; :.    ' / | 
    '   :  | '  : |__ '   ; :__      '   :  | ," .--.; |'   ; :__      '   :  ||   :    |'   ;   /| 
    ;   |.'  |  | '.'|'   | '.'|     ;   |.' /  /  ,.  |'   | '.'|     ;   |.'  \   \  / '   |  / | 
    '---'    ;  :    ;|   :    :     '---'  ;  :   .'   \   :    :     '---'     `----'  |   :    | 
             |  ,   /  \   \  /             |  ,     .-./\   \  /                         \   \  /  
              ---`-'    `----'               `--`---'     `----'                           `----'   
'''

    print(title)
    print("1. Join Room")
    print("2. Create Room")
    print("3. View Credits")
    print("4. Quit")

    while True:
        try:
            choice = int(input("\nChoice: "))
        except KeyboardInterrupt:
            print("Program exit")
            sys.exit()
        except Exception:
            print("Bad input. Try again")
            continue

        if choice == 1:
            joinRoom()
        elif choice == 2:
            createRoom()
        elif choice == 3:
            print("Game by: Naadiya Saikia, Balazs Fentor")
        elif choice == 4:
            print("Quitting...")
            sys.exit()
        else:
            print("Choice not found. Pick again")


def joinRoom():
    if client.s is None:
        ip = input("Server IP: ")
        ret = client.connect(ip)
        if ret == 1:
            print("Couldn't connect to server")
            sys.exit()

    rooms = client.queryServer()

    if not rooms:
        print("No rooms found. Try creating one")
        return

    for room in rooms:
        print(room)

    try:
        choice = int(input("Choose room: "))
    except KeyboardInterrupt:
        print("Program exit")
        sys.exit()
    except Exception:
        print("Bad input. Try again")
        return

    state = client.join(choice)
    if state.get("type") == "ERROR":
        print(state.get("message", "Could not join room."))
        return

    name = input("Enter your name (press enter for default): ").strip()
    if name:
        client.set_name(name)

    play_game(state)


def createRoom():
    print("Creating a room by joining room 1.")
    if client.s is None:
        ip = input("Server IP: ")
        ret = client.connect(ip)
        if ret == 1:
            print("Couldn't connect to server")
            sys.exit()
    state = client.join(1)
    if state.get("type") == "ERROR":
        print(state.get("message", "Could not create room."))
        return

    name = input("Enter your name (press enter for default): ").strip()
    if name:
        client.set_name(name)

    play_game(state)


def play_game(state):
    room_id = state["room"]
    player_symbol = state["your_symbol"]
    matrix = state["matrix"]
    next_symbol = state["next"]
    winner = state["winner"]

    while True:
        printBoard(matrix, state.get("player_names", {}), state.get("wins", {}), player_symbol)
        if winner:
            if winner == "DRAW":
                print("Game over: Draw.")
            elif winner == player_symbol:
                print("Game over: You win!")
            else:
                winner_name = state.get("player_names", {}).get(winner, f"Player {winner}")
                print(f"Game over: {winner_name} wins!")
            client.close()
            sys.exit()
            return

        print(state.get("message", ""))
        if state.get("player_count", 0) < 2:
            print("Waiting for opponent to join...")
            state = client.receive_update()
            matrix = state.get("matrix", matrix)
            next_symbol = state.get("next", next_symbol)
            winner = state.get("winner", winner)
            continue

        if next_symbol == player_symbol:
            print(f"Your turn ({player_symbol}). Enter a move as row,col.")
            try:
                choice = input("Move (1-3,1-3) or Q to quit: ")
                if choice.strip().lower() in {"q", "quit", "exit"}:
                    client.close()
                    sys.exit()
                row, col = [int(val.strip()) - 1 for val in choice.split(",")]
                state = client.send_move(room_id, row, col)
            except KeyboardInterrupt:
                print("Program exit")
                client.close()
                sys.exit()
            except Exception:
                print("Bad input. Please use row,col with values 1 to 3.")
                continue
        else:
            print(f"Waiting for opponent ({next_symbol})...")
            state = client.receive_update()

        if state.get("type") == "ERROR":
            print(state.get("message", "An error occurred."))
            if state.get("winner") or state.get("message") == "Game is already over.":
                matrix = state.get("matrix", matrix)
                winner = state.get("winner")
                break
            continue

        matrix = state["matrix"]
        next_symbol = state["next"]
        winner = state["winner"]


def printBoard(matrix, player_names, wins, player_symbol):
    os.system('cls' if os.name == 'nt' else 'clear')
    your_name = player_names.get(player_symbol, f"Player {player_symbol}")
    opp_symbol = "O" if player_symbol == "X" else "X"
    opp_name = player_names.get(opp_symbol, f"Player {opp_symbol}")
    your_wins = wins.get(player_symbol, 0)
    opp_wins = wins.get(opp_symbol, 0)
    board = f'''
 {matrix[0][0]} | {matrix[0][1]} | {matrix[0][2]}
---+---+---
 {matrix[1][0]} | {matrix[1][1]} | {matrix[1][2]}
---+---+---
 {matrix[2][0]} | {matrix[2][1]} | {matrix[2][2]}

You: {your_name} ({player_symbol}) - Wins: {your_wins}
Opponent: {opp_name} ({opp_symbol}) - Wins: {opp_wins}
'''
    print(board)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program exit")
        sys.exit()
