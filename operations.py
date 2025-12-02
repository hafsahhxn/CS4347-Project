# operations.py
import sqlite3
from datetime import date, timedelta, datetime
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

def checkout_book(isbn, card_id): #hafsah navaid
    conn = create_connection()
    c = conn.cursor()

    #borrower cannot checkout if unpaid fines
    c.execute("""
        SELECT SUM(Fine_amt)
        FROM FINES f
        JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
        WHERE bl.Card_id = ? AND Paid = 0
    """, (card_id,))
    row = c.fetchone()
    if row[0] and row[0] > 0:
        conn.close()
        return "Checkout failed: borrower has unpaid fines."

    #borrower cannot exceed 3 loans
    c.execute("""
        SELECT COUNT(*) FROM BOOK_LOANS
        WHERE Card_id = ? AND Date_in IS NULL
    """, (card_id,))
    count = c.fetchone()[0]
    if count >= 3:
        conn.close()
        return "Checkout failed: borrower already has 3 books."

    #if book is sold out then error
    c.execute("""
        SELECT 1 FROM BOOK_LOANS
        WHERE Isbn = ? AND Date_in IS NULL
    """, (isbn,))
    if c.fetchone():
        conn.close()
        return "Checkout failed: book is already checked out."

    #checkout
    today = date.today()
    due_date = today + timedelta(days=14)

    c.execute("""
        INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date)
        VALUES (?, ?, ?, ?)
    """, (isbn, card_id, today, due_date))
    conn.commit()
    conn.close()
    return "Checkout successful!"

def checkin_book(isbn, card_id):    # Teammate : Kimberly (Grace) Niemiec
    conn = create_connection()
    c = conn.cursor()

    c.execute("""
        SELECT Loan_id
        FROM BOOK_LOANS
        WHERE Isbn = ? AND Card_id = ? AND Date_in IS NULL
    """, (isbn, card_id))

    row = c.fetchone()
    if not row:
        conn.close()
        return "Checkin failed: no active loan found."

    loan_id = row[0]
    today = date.today()

    c.execute("""
        UPDATE BOOK_LOANS
        SET Date_in = ?
        WHERE Loan_id = ?
    """, (today, loan_id))

    conn.commit()
    conn.close()
    return "Checkin successful!"


def add_borrower(ssn, name, address, phone=None): #hafsah navaid
    conn = create_connection()
    c = conn.cursor()

    # cannot duplicate SSN
    c.execute("SELECT 1 FROM BORROWER WHERE Ssn = ?", (ssn,))
    if c.fetchone():
        conn.close()
        return "Borrower rejected: SSN already exists."

    # generate a new Card_id
    c.execute("SELECT Card_id FROM BORROWER ORDER BY Card_id DESC LIMIT 1")
    last = c.fetchone()
    if last:
        num = int(last[0][2:]) + 1
    else:
        num = 1

    new_id = f"ID{num:03d}"

    c.execute("""
        INSERT INTO BORROWER (Card_id, Ssn, Bname, Address, Phone)
        VALUES (?, ?, ?, ?, ?)
    """, (new_id, ssn, name, address, phone))

    conn.commit()
    conn.close()
    return f"Borrower created successfully. New Card ID = {new_id}"

def pay_fines(card_id):
    conn = create_connection()
    c = conn.cursor()

    # cannot pay if book is still out
    c.execute("""
        SELECT 1
        FROM BOOK_LOANS bl
        JOIN FINES f ON bl.Loan_id = f.Loan_id
        WHERE bl.Card_id = ? AND bl.Date_in IS NULL
    """, (card_id,))
    if c.fetchone():
        conn.close()
        return "Cannot pay: borrower still has a checked-out book."

    # mark all fines paid
    c.execute("""
        UPDATE FINES
        SET Paid = 1
        WHERE Loan_id IN (
            SELECT Loan_id FROM BOOK_LOANS WHERE Card_id = ?
        )
    """, (card_id,))
    conn.commit()
    conn.close()
    return "All fines successfully paid."

def refresh_fines():
    conn = create_connection()
    c = conn.cursor()

    c.execute("""
        SELECT Loan_id, Due_date, Date_in
        FROM BOOK_LOANS
    """)
    rows = c.fetchall()

    for loan_id, due, date_in in rows:
        due = datetime.strptime(due, "%Y-%m-%d").date()

        if date_in:
            date_in = datetime.strptime(date_in, "%Y-%m-%d").date()
            days_late = (date_in - due).days
        else:
            days_late = (date.today() - due).days

        if days_late <= 0:
            continue

        fine_amt = round(days_late * 0.25, 2)

        c.execute("""
            INSERT INTO FINES (Loan_id, Fine_amt)
            VALUES (?, ?)
            ON CONFLICT(Loan_id)
            DO UPDATE SET Fine_amt=excluded.Fine_amt
            WHERE Paid = 0
        """, (loan_id, fine_amt))

    conn.commit()
    conn.close()
    return "Fines refreshed."
