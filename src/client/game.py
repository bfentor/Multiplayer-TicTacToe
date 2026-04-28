import sys
from time import sleep
import os
import client

def main():
    # generate matrix before game
    matrix = [[" ", " ", " ",], [" ", " ", " ",], [" ", " ", " ",]]

    menu()

def menu():
    title = r'''
        ,----,                           ,----,                            ,----,                   
      ,/   .`|                         ,/   .`|                          ,/   .`|                   
    ,`   .'  :                       ,`   .'  :                        ,`   .'  :                   
  ;    ;     / ,--,                ;    ;     /                      ;    ;     /                   
.'___,/    ,',--.'|              .'___,/    ,'                     .'___,/    ,'  ,---.             
|    :     | |  |,               |    :     |                      |    :     |  '   ,'\            
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
        except:
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
    print("temp")

def createRoom():
    print("temp")

def printBoard(matrix):
    os.system('cls' if os.name == 'nt' else 'clear')

    m  = f'''
 {matrix[0][0]} | {matrix[1][0]} | {matrix[2][0]} 
---+---+---
 {matrix[0][1]} | {matrix[1][1]} | {matrix[2][1]} 
---+---+---
 {matrix[0][2]} | {matrix[1][2]} | {matrix[2][2]} 
'''
    print(m)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program exit")
        sys.exit()