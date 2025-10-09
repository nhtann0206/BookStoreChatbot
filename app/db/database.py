import sqlite3
from pathlib import Path

DB_PATH = Path("app/db/bookstore.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            price INTEGER,
            stock INTEGER,
            category TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            address TEXT,
            book_id INTEGER,
            quantity INTEGER,
            status TEXT,
            FOREIGN KEY(book_id) REFERENCES Books(book_id)
        )
    """)

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


def get_all_books():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Books")
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "book_id": r[0],
            "title": r[1],
            "author": r[2],
            "price": r[3],
            "stock": r[4],
            "category": r[5],
        }
        for r in rows
    ]


def find_book_by_title(title: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Books WHERE lower(title)=lower(?)", (title,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "book_id": row[0],
        "title": row[1],
        "author": row[2],
        "price": row[3],
        "stock": row[4],
        "category": row[5],
    }


def add_order(name, phone, address, book_id, quantity):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Orders (customer_name, phone, address, book_id, quantity, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, phone, address, book_id, quantity, "Đang xử lý"),
    )
    conn.commit()

    # Lấy order_id vừa thêm
    order_id = cur.lastrowid

    # Lấy lại thông tin đơn hàng đầy đủ (để trả về cho order_flow)
    cur.execute(
        "SELECT order_id, customer_name, phone, address, book_id, quantity, status FROM Orders WHERE order_id = ?",
        (order_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "order_id": row[0],
        "customer_name": row[1],
        "phone": row[2],
        "address": row[3],
        "book_id": row[4],
        "quantity": row[5],
        "status": row[6],
    }


def get_orders_by_customer(name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT o.order_id, o.quantity, o.status, b.title
        FROM Orders o
        JOIN Books b ON o.book_id = b.book_id
        WHERE lower(o.customer_name)=lower(?)
        """,
        (name,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "order_id": r[0],
            "quantity": r[1],
            "status": r[2],
            "book_title": r[3],
        }
        for r in rows
    ]
