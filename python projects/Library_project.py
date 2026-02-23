# Online Library Borrow system with book delivery or pickup points

users_db = {}
current_user_email = None
loans = []



def show_UI():
    print("\nLoading...")
    print("Online Library system")
    print("1. Sign-up")
    print("2. Login")
    print("3. Exit")

    print("Enter '1' to create an account, '2' to log in, '3' to exit")

    try:
        user_pick = int(input("Choose: "))
    except ValueError:
        print("Enter a number.")
        return show_UI()

    if user_pick == 1:
        created = create_account()
        if created:
            lib_menu()
    elif user_pick == 2:
        logged = login()
        if logged:
            lib_menu()
    elif user_pick == 3:
        ex()


def create_account():
    global users_db, current_user_email

    print("\nSign up to access library")
    email = input("Email: ").strip().lower()

    if email in users_db:
        print("This email is already linked to an account.")
        return False

    while True:
        pwd = input("Password: ")
        conf_pwd = input("Confirm password: ")
        if conf_pwd == pwd:
            break
        print("Passwords do not match. Try again!")

    user = {
        "first name": input("First name: ").strip(),
        "last name": input("Last name: ").strip(),
        "email": email,
        "password": pwd,
        "fav_genre": input("What is your favourite genre: ").strip(),
    }

    users_db[email] = user
    current_user_email = email
    print("Account created successfully ✅")
    return True


def login():
    global users_db, current_user_email

    while True:
        user_email = input("Email: ").strip().lower()

        if user_email not in users_db:
            print("Email not found! Try again.")
            continue

        user_pwd = input("Password: ")

        if user_pwd == users_db[user_email]["password"]:
            current_user_email = user_email
            print("Login successful ✅")
            return True
        else:
            print("Incorrect password. Try again.")


def ex():
    print("Exiting... Goodbye 👋")


def logout():
    global current_user_email
    current_user_email = None
    print("Logged out ✅")
    show_UI()




class Book:
    def __init__(self, name, total_qty):
        self.name = name
        self.total_qty = total_qty
        self.available_qty = total_qty
        self.genre = None 

    def borrow_book(self, qty):
        if qty <= 0:
            return False, "Quantity must be at least 1"
        if qty > self.available_qty:
            return False, "Not enough copies available"
        self.available_qty -= qty
        return True, f"Borrowed {qty} copy/copies of {self.name}"

    def return_book(self, qty):
        if qty <= 0:
            return False, "Quantity must be at least 1"
        if self.available_qty + qty > self.total_qty:
            return False, "Return amount has exceeded original stock"
        self.available_qty += qty
        return True, f"Returned {qty} copy/copies of {self.name}"


class Loan:
    def __init__(self, user_name, book_name, qty_borrowed, days_borrowed):
        self.user_name = user_name
        self.book_name = book_name
        self.qty_borrowed = qty_borrowed
        self.days_borrowed = days_borrowed
        self.status = "BORROWED"

    def mark_returned(self):
        self.status = "RETURNED"




Finance_books = {
    "book_1": {"name": "1. Rich Dad Poor Dad", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. The psychology of money", "Quantiy": 10, "is_available": True},  # typo handled
    "book_3": {"name": "3. The Intelligent Investor", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. A random walk down wall street", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. The Simple Path To wealth", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. The Millonaire Next Door", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. Think And Grow Rich", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. The Riches Man in Babylon", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. Common Stocks and Uncommon Profits", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. The Little Book of Common Sense Investing", "Quantity": 10, "is_available": True},
}

Literary_books = {
    "book_1": {"name": "1. 1984", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. To Kill a Mockingbird", "Quantity": 10, "is_available": True},
    "book_3": {"name": "3. The Great Gatsby", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. Pride and Prejudice", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. The Catcher in The Rye", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. Of Mice and Men", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. Crime and Punishment", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. The Brothers Karasmov", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. The Old Man and The Sea", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. Brave New World", "Quantity": 10, "is_available": True},
}

Science_books = {
    "book_1": {"name": "1. Dune", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. Foundation", "Quantity": 10, "is_available": True},
    "book_3": {"name": "3. Neuromancer", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. Ender's Game", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. The Hobbit", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. The Lord of The Rings", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. The Name of The Wind", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. Mistborn", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. Snow Crash", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. The Martian", "Quantity": 10, "is_available": True},
}

Psychology_books = {
    "book_1": {"name": "1. Thinking Fast and Slow", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. Man's Search for Meaning", "Quantity": 10, "is_available": True},
    "book_3": {"name": "3. Influence", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. Behave", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. The Psychology of Money", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. Emotional Intelligence", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. Predictability Irrational", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. Games people play", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. Flow", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. Thinking in Bets", "Quantity": 10, "is_available": True},
}

Selfhelp_books = {
    "book_1": {"name": "1. Atomic Habits", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. The 7 Habits of Highly Effective People", "Quantity": 10, "is_available": True},
    "book_3": {"name": "3. How to Win Friends and Inluence People", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. Deep Work", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. The Power of Now", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. Can't Hurt Me", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. The Subtle Art of not giving A Fuck", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. Make Your Bed", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. Think and Grow Rich", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. Ikigai", "Quantity": 10, "is_available": True},
}

Horror_books = {
    "book_1": {"name": "1. Dracula", "Quantity": 10, "is_available": True},
    "book_2": {"name": "2. Frankenstein", "Quantity": 10, "is_available": True},
    "book_3": {"name": "3. The Shining", "Quantity": 10, "is_available": True},
    "book_4": {"name": "4. It", "Quantity": 10, "is_available": True},
    "book_5": {"name": "5. Pet Semetary", "Quantity": 10, "is_available": True},
    "book_6": {"name": "6. The Exorctist", "Quantity": 10, "is_available": True},
    "book_7": {"name": "7. The Hauntng of Hill House", "Quantity": 10, "is_available": True},
    "book_8": {"name": "8. The Turn of The Screw", "Quantity": 10, "is_available": True},
    "book_9": {"name": "9. Bird Box", "Quantity": 10, "is_available": True},
    "book_10": {"name": "10. World War Z", "Quantity": 10, "is_available": True},
}




def clean_title(name: str) -> str:
    name = name.strip()
    if ". " in name:
        left, right = name.split(". ", 1)
        if left.isdigit():
            return right.strip()
    return name


def build_inventory():
    inv = {}
    genre_map = {
        "Finance": Finance_books,
        "Literary": Literary_books,
        "Science": Science_books,
        "Psychology": Psychology_books,
        "Self Help": Selfhelp_books,
        "Horror": Horror_books,
    }

    for genre, books_dict in genre_map.items():
        for b in books_dict.values():
            title = clean_title(b.get("name", "Unknown"))
            qty = b.get("Quantity", b.get("Quantiy", 0))  

            book_obj = Book(title, qty)
            book_obj.genre = genre
            inv[title] = book_obj

    return inv


inventory = build_inventory()



def choose_genre():
    genres = ["Finance", "Literary", "Science", "Psychology", "Self Help", "Horror"]

    print("\nChoose a genre:")
    for i, g in enumerate(genres, start=1):
        print(f"{i}) {g}")

    try:
        choice = int(input("Pick genre number: "))
        if choice < 1 or choice > len(genres):
            print("Invalid choice.")
            return None
    except ValueError:
        print("Enter a number.")
        return None

    return genres[choice - 1]


def show_books_by_genre(genre):
    books_in_genre = [b for b in inventory.values() if b.genre == genre]

    if not books_in_genre:
        print("No books found in this genre.")
        return None

    print(f"\nBooks in {genre}:")
    for i, b in enumerate(books_in_genre, start=1):
        print(f"{i}) {b.name} ({b.available_qty}/{b.total_qty})")

    return books_in_genre




def lib_menu():
    print("\n=== Library Menu ===")
    print("1. Library search (show genre books)")
    print("2. Borrow from library")
    print("3. Return books")
    print("0. Log out")

    try:
        user_pick = int(input("Choose: "))
    except ValueError:
        print("Enter a number.")
        return

    if user_pick == 1:
        lib_search()
    elif user_pick == 2:
        borrow_flow()
    elif user_pick == 3:
        return_flow()
    elif user_pick == 0:
        logout()


def lib_search():
    genre = choose_genre()
    if not genre:
        return
    show_books_by_genre(genre)



def borrow_flow():
    if not current_user_email:
        print("You must login first.")
        return

    user_name = users_db[current_user_email]["first name"]

    genre = choose_genre()
    if not genre:
        return

    books = show_books_by_genre(genre)
    if not books:
        return

    try:
        choice = int(input("Pick book number: "))
        qty = int(input("Quantity: "))
        days = int(input("Days: "))
    except ValueError:
        print("Enter numbers only.")
        return

    if choice < 1 or choice > len(books):
        print("Invalid selection.")
        return

    book = books[choice - 1]

    ok, msg = book.borrow_book(qty)
    print(msg)

    if ok:
        loans.append(Loan(user_name, book.name, qty, days))
        print("Loan recorded ✅")




def return_flow():
    if not current_user_email:
        print("You must login first.")
        return

    user_name = users_db[current_user_email]["first name"]

    active = [l for l in loans if l.user_name == user_name and l.status == "BORROWED"]
    if not active:
        print("You have no active borrowed books.")
        return

    print("\nYour borrowed books:")
    for i, l in enumerate(active, start=1):
        print(f"{i}) {l.book_name} (qty: {l.qty_borrowed}, days: {l.days_borrowed})")

    try:
        choice = int(input("Choose which loan to return: "))
        qty = int(input("Quantity to return: "))
    except ValueError:
        print("Enter numbers only.")
        return

    if choice < 1 or choice > len(active):
        print("Invalid selection.")
        return

    loan = active[choice - 1]

    if qty <= 0:
        print("Quantity must be at least 1.")
        return

    if qty > loan.qty_borrowed:
        print("You cannot return more than you borrowed.")
        return

    book_obj = inventory.get(loan.book_name)
    if not book_obj:
        print("System error: book not found in inventory.")
        return

    ok, msg = book_obj.return_book(qty)
    print(msg)

    if ok:
        loan.qty_borrowed -= qty
        if loan.qty_borrowed == 0:
            loan.mark_returned()
            print("Loan marked RETURNED ✅")
        else:
            print(f"Partial return recorded ✅ Remaining qty: {loan.qty_borrowed}")




show_UI()
