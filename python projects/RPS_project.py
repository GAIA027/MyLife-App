rock = "Rock"
paper = "Paper"
scissors = "Scissors"

decisions = [rock, paper, scissors]

import random
while True:
    user_choice= input("What do you choose? Type 0 for rock, 1 for paper or 2 for scissors.")
    if user_choice >= 0 and user_choice <= 2:
        print(decisions[user_choice])
    computer_choice = random.randint(0, 2)
    print(f"computer chose:")
    print(decisions[computer_choice])
    if user_choice >= 3 or user_choice < 0:
        print("You typed an invalid number. You lose")
    elif user_choice == 0 and computer_choice == 2:
        print("You win")
    elif computer_choice > user_choice:
        print("You lose")
    elif computer_choice == user_choice:
        print("It's a draw")
    elif user_choice == 2 and computer_choice == 0:
        print("You lose")
    elif user_choice > computer_choice:
        print("You win")
    elif user_choice >= 3 or user_choice < 0:
        print("You typed an invalid number. You lose")
    else:
        print("You typed an invalid number. You lose")

