from app.db.database import get_all_books

def handle(user_input: str, session: dict):
    """
    Xử lý luồng xem danh sách sách khả dụng.
    Trả về tuple (reply, done) để đồng bộ với các flow khác.
    """

    # Cho phép quay lại menu chính
    if user_input.strip() == "0":
        session.clear()
        reply = (
            "🔙 Đã quay lại menu chính.\n\n"
            "📚 Vui lòng chọn tính năng:\n"
            "- Bấm '1' để Đặt sách\n"
            "- Bấm '2' để Xem các loại sách khả dụng\n"
            "- Bấm '3' để Tra cứu đơn hàng\n"
            "- Bấm '0' để Thoát / quay lại menu chính"
        )
        session["state"] = "menu"
        return reply, True

    # Nếu chưa có state hoặc user chọn xem danh sách
    books = get_all_books()
    if not books:
        reply = (
            "😔 Hiện chưa có sách nào trong kho.\n"
            "👉 Nhấn '0' để quay lại menu chính."
        )
        return reply, False

    # Hiển thị danh sách sách
    book_list = "\n".join([
        f"- {b['title']} (Tác giả: {b['author']}, Giá: {b['price']}₫, Còn: {b['stock']} quyển)"
        for b in books
    ])

    reply = (
        f"📚 Danh sách sách khả dụng:\n\n{book_list}\n\n"
        "🏠 Quay lại menu chính:\n"
        "- Bấm '0' để quay lại menu chính"
    )

    # Flow xem sách chỉ hiển thị 1 lần → có thể coi là kết thúc
    session.clear()
    session["state"] = "menu"
    return reply, True
