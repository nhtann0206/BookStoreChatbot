from app.db.database import get_conn, init_db

def seed_data():
    init_db()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Books")
    count = cur.fetchone()[0]
    if count > 0:
        print("✅ Database đã có dữ liệu, bỏ qua seed.")
        conn.close()
        return

    books = [
        ("Truyện Kiều", "Nguyễn Du", 45000, 20, "Văn học cổ điển"),
        ("Dế Mèn Phiêu Lưu Ký", "Tô Hoài", 38000, 15, "Thiếu nhi"),
        ("Harry Potter và Hòn đá Phù thủy", "J.K. Rowling", 95000, 10, "Fantasy"),
        ("Đắc Nhân Tâm", "Dale Carnegie", 80000, 25, "Kỹ năng sống"),
        ("Lập Trình Python Cơ Bản", "Nguyễn Văn A", 120000, 8, "Công nghệ thông tin"),
    ]

    cur.executemany(
        "INSERT INTO Books (title, author, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        books
    )

    conn.commit()
    conn.close()
    print("🌱 Seed dữ liệu thành công!")

if __name__ == "__main__":
    seed_data()
