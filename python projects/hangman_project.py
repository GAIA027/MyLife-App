try:
    from wonderwords import RandomWord

    r = RandomWord()
    random_word = r.word(word_min_length=5, word_max_length=5)
except Exception:
    import random

    random_word = random.choice(["apple", "grape", "zebra", "music", "tiger"])

word = random_word.lower()
player_life_count = 5
guessed_letters = set()

print("\n===Hangman===")

while True:
    display = "".join([ch if ch in guessed_letters else "_" for ch in word])
    print("Word:", " ".join(display))
    print("Player life count:", player_life_count)

    if "_" not in display:
        print("You won! He was saved. The word is:", word)
        break

    if player_life_count <= 0:
        print("You lost! He was hanged. The word was:", word)
        break

    guess = input("Guess a letter: ").strip().lower()

    if len(guess) != 1 or not guess.isalpha():
        print("You have to enter a single letter.")
        continue

    if guess in guessed_letters:
        print("You already guessed that letter.")
        continue

    guessed_letters.add(guess)

    if guess not in word:
        player_life_count -= 1
        print("Incorrect letter.", player_life_count, "life/lives left.")




import random

words = ["Apple", "Hierarchy", "Typography", "Alignment", "Orange"]
random_word = random.choice(words)

single_letter = random.choice(random_word)
print("Word:", random_word)
print("Letter:", single_letter)