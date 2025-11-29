# operations.py
import sqlite3
from datetime import date, timedelta
from database import create_connection

def search_books(query: str):
    """
    Returns ALL books where the query appears in ISBN, Title, or ANY Author name
    Case-insensitive substring search (exactly as required)
    """
    conn = create_connection()
    c = conn.cursor()

    pattern = f"%{query.strip()}%"

    sql = """
    SELECT 
        b.Isbn,
        b.Title,
        GROUP_CONCAT(DISTINCT a.Name) AS authors,
        CASE 
            WHEN EXISTS(SELECT 1 FROM BOOK_LOANS bl 
                        WHERE bl.Isbn = b.Isbn AND bl.Date_in IS NULL)
            THEN 'OUT'
            ELSE 'IN'
        END AS availability
    FROM BOOK b
    LEFT JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn
    LEFT JOIN AUTHORS a ON ba.Author_id = a.Author_id
    WHERE LOWER(b.Isbn) LIKE LOWER(?)
       OR LOWER(b.Title) LIKE LOWER(?)
       OR LOWER(a.Name) LIKE LOWER(?)
    GROUP BY b.Isbn, b.Title
    ORDER BY b.Isbn
    """

    c.execute(sql, (pattern, pattern, pattern))
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        authors = row[2] if row[2] else "Unknown"
        results.append({
            "isbn": row[0],
            "title": row[1],
            "authors": authors,
            "availability": row[3]
        })
    return results

# Teammates will implement these
def checkout_book(isbn, card_id): 
    conn = create_connection()
    c = conn.cursor()
#cannot check out if borrower has unpaid files
    c.execute("""
              SELECT SUM(Fine_amt)
              FROM FINES f
              JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
              WHERE bl.Card_id = ? AND Paid = 0
              """, (card_id,))
    row = c.fetchone()
    if row[0] is not None:
        conn.close()
        return "Checkout failed: borrower has unpaid fines."
#borrower can have max 3 active loans 
    c.execute("""
        SELECT COUNT(*) FROM BOOK_LOANS
        WHERE Card_id = ? AND Date_in IS NULL
    """, (card_id,))
    count = c.fetchone()[0]
    if count >= 3:
        conn.close()
        return "Checkout failed: borrower already has 3 books."
#cant check out the book if it is not avaliable 
    c.execute("""
        SELECT 1 FROM BOOK_LOANS
        WHERE Isbn = ? AND Date_in IS NULL
    """, (isbn,))
    if c.fetchone():
        conn.close()
        return "Checkout failed: book is already checked out."
#checkout book
    today = date.today()
    due_date = today + timedelta(days=14)

    c.execute("""
        INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date)
        VALUES (?, ?, ?, ?)
    """, (isbn, card_id, today, due_date))
    conn.commit()
    conn.close()
    return "Checkout successful!"
    
def checkin_book(isbn, card_id): return "[Pending] Teammate"
def add_borrower(ssn, name, address, phone=None): return "[Pending] Teammate"
def pay_fines(card_id): return "[Pending] Teammate"
def refresh_fines(): pass
