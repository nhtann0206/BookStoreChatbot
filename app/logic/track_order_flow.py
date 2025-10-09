from app.db.database import get_orders_by_customer

def handle(user_input: str, session: dict):
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

    if "awaiting_name" not in session:
        session["awaiting_name"] = True
        reply = (
            "🔎 Vui lòng nhập **tên người đặt hàng** để tra cứu đơn.\n"
            "👉 (Nhấn '0' để quay lại menu chính)"
        )
        return reply, False

    customer_name = user_input.strip()
    orders = get_orders_by_customer(customer_name)

    if not orders:
        session.clear()
        reply = (
            f"❌ Không tìm thấy đơn hàng nào của '{customer_name}'.\n"
            "👉 Thử lại hoặc nhấn '0' để quay lại menu chính."
        )
        session["state"] = "menu"
        return reply, False

    orders_text = "\n\n".join([
        f"🧾 Mã đơn: {o['order_id']}\n"
        f"📗 Sách: {o['book_title']}\n"
        f"📦 Số lượng: {o['quantity']}\n"
        f"🚚 Trạng thái: {o['status']}"
        for o in orders
    ])

    session.clear()
    reply = (
        f"📋 Kết quả tra cứu đơn hàng cho '{customer_name}':\n\n{orders_text}\n\n"
        "🏠 Quay lại menu chính:\n"
        "- Bấm '1' để Đặt sách\n"
        "- Bấm '2' để Xem sách khả dụng\n"
        "- Bấm '3' để Tra cứu đơn hàng\n"
        "- Bấm '0' để Quay lại menu chính"
    )
    session["state"] = "menu"
    return reply, True
