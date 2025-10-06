import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any

DB_PATH = Path(__file__).resolve().parent.parent / "bookstore.db"

def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(seed: bool = True):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Books(
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            category TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Orders(
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT,
            FOREIGN KEY(book_id) REFERENCES Books(book_id)
        );
    """)
    conn.commit()
    if seed:
        seed_data(conn)
    conn.close()

def seed_data(conn: Optional[sqlite3.Connection] = None):
    close_after = False
    if conn is None:
        conn = _connect()
        close_after = True
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Books'")
    if cur.fetchone() is None:
        if close_after:
            conn.close()
        return
    cur.execute("SELECT COUNT(1) FROM Books")
    if cur.fetchone()[0] > 0:
        if close_after:
            conn.close()
        return
    books = [
        ("Truyện Kiều", "Nguyễn Du", 100000.0, 5, "Văn học"),
        ("Lập trình Python cơ bản", "Nguyễn Văn A", 180000.0, 7, "Programming"),
        ("Chiến tranh và Hòa bình", "Lev Tolstoy", 250000.0, 2, "Classic"),
        ("Dế Mèn phiêu lưu ký", "Tô Hoài", 90000.0, 10, "Children"),
    ]
    cur.executemany("INSERT INTO Books (title, author, price, stock, category) VALUES (?, ?, ?, ?, ?)", books)
    conn.commit()
    if close_after:
        conn.close()

def find_books(title: str = "", author: str = "", category: str = "") -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    q = "SELECT * FROM Books WHERE 1=1"
    params = []
    if title:
        q += " AND title LIKE ?"
        params.append(f"%{title}%")
    if author:
        q += " AND author LIKE ?"
        params.append(f"%{author}%")
    if category:
        q += " AND category LIKE ?"
        params.append(f"%{category}%")
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_book_by_id(book_id: int) -> Optional[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Books WHERE book_id = ?", (book_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def create_order(customer_name: str, phone: str, address: str, book_id: int, quantity: int) -> Dict[str, Any]:
    conn = _connect()
    try:
        cur = conn.cursor()
        conn.execute("BEGIN")
        cur.execute("SELECT stock FROM Books WHERE book_id = ?", (book_id,))
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            return {"error": "Book not found"}
        stock = row["stock"] if isinstance(row, sqlite3.Row) else row[0]
        if stock < quantity:
            conn.rollback()
            return {"error": "Insufficient stock"}
        cur.execute("INSERT INTO Orders (customer_name, phone, address, book_id, quantity, status) VALUES (?, ?, ?, ?, ?, ?)", (customer_name, phone, address, book_id, quantity, "Pending"))
        order_id = cur.lastrowid
        cur.execute("UPDATE Books SET stock = stock - ? WHERE book_id = ?", (quantity, book_id))
        conn.commit()
        cur.execute("""
            SELECT o.order_id, o.customer_name, o.phone, o.address, o.book_id, o.quantity, o.status,
                   b.title AS book_title, b.author AS book_author, b.price AS book_price
            FROM Orders o
            JOIN Books b ON o.book_id = b.book_id
            WHERE o.order_id = ?
        """, (order_id,))
        order_row = cur.fetchone()
        return dict(order_row) if order_row else {"error": "Unknown error"}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_orders() -> List[Dict[str, Any]]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.order_id, o.customer_name, o.phone, o.address, o.quantity, o.status,
               b.book_id, b.title AS book_title, b.author AS book_author, b.price AS book_price
        FROM Orders o JOIN Books b ON o.book_id = b.book_id
        ORDER BY o.order_id DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
