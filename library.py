# library.py
from database import init_db
from operations import (
    search_books,
    checkout_book,
    checkin_book,
    add_borrower,
    pay_fines,
    refresh_fines
)


def print_results(results):
    if not results:
        print("\nNo results found.\n")
        return

    print(f"\n{'ISBN':<13} {'TITLE':<55} {'AUTHORS':<40} {'STATUS'}")
    print("-" * 140)

    for r in results:
        title = r["title"]
        if len(title) > 55:
            title = title[:52] + "..."

        authors = r["authors"] or "Unknown"
        if len(authors) > 40:
            authors = authors[:37] + "..."

        print(f"{r['isbn']:<13} {title:<55} {authors:<40} {r['availability']}")

    print(f"\n{len(results)} result(s) found.\n")


def input_or_cancel(prompt):
    value = input(prompt).strip()
    if value.lower() == "cancel":
        print("\nOperation cancelled.\n")
        return None
    return value


if __name__ == "__main__":
    init_db()

    while True:
        print("\n" + "="*55)
        print("     LIBRARY SYSTEM - MILESTONE 2")
        print("="*55)
        print("1. Search Books")
        print("2. Checkout Book")
        print("3. Checkin Book")
        print("4. Add Borrower")
        print("5. Pay Fines")
        print("6. Refresh Fines")
        print("7. Exit")

        choice = input("\nChoice: ").strip()

        
        #search
     
        if choice == "1":
            q = input("Search: ").strip()
            if q:
                results = search_books(q)
                print_results(results)
            else:
                print("Enter a search term.")

    
        #checkout
       
        elif choice == "2":
            isbn = input_or_cancel("Enter ISBN: ")
            if not isbn: continue

            card = input_or_cancel("Enter Card ID: ")
            if not card: continue

            print(checkout_book(isbn, card))

       
        #checkin
      
        elif choice == "3":
            isbn = input_or_cancel("Enter ISBN: ")
            if not isbn: continue

            card = input_or_cancel("Enter Card ID: ")
            if not card: continue

            print(checkin_book(isbn, card))

     
        #add borrower
      
        elif choice == "4":
            ssn = input_or_cancel("SSN: ")
            if not ssn: continue

            name = input_or_cancel("Name: ")
            if not name: continue

            addr = input_or_cancel("Address: ")
            if not addr: continue

            phone = input("Phone (optional): ").strip() or None

            print(add_borrower(ssn, name, addr, phone))

       
        #pay fines
    
        elif choice == "5":
            card = input_or_cancel("Enter Card ID: ")
            if not card: continue

            print(pay_fines(card))

        
        #refresh fines
    
        elif choice == "6":
            print(refresh_fines())

      
        #exit
       
        elif choice == "7":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")

