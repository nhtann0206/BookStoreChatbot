from app.db.database import get_all_books, add_order
from app.llm.llm_client import llm_generate
from app.logic.utils import extract_order_entities

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

    # Khởi tạo order_info nếu chưa có
    if "order_info" not in session:
        session["order_info"] = {}

    # Cập nhật thông tin người dùng vừa nhập
    entities = extract_order_entities(user_input)
    session["order_info"].update({k: v for k, v in entities.items() if v})
    print("Extracted entities:", entities)

    required_fields = ["customer_name", "book_title", "quantity", "address", "phone"]
    missing = [f for f in required_fields if not session["order_info"].get(f)]

    if missing:
        # Chỉ hỏi lại những thông tin còn thiếu
        friendly_fields = {
            "customer_name": "tên của bạn",
            "book_title": "tên sách muốn mua",
            "quantity": "số lượng",
            "address": "địa chỉ giao hàng",
            "phone": "số điện thoại liên lạc",
        }
        missing_names = [friendly_fields[f] for f in missing]
        prompt = f"Người dùng còn thiếu {', '.join(missing_names)}. Hãy hỏi người dùng cung cấp những thông tin này, với giọng thân thiện, tự nhiên."
        response = llm_generate(prompt)
        print(" Prompt gửi LLM:", prompt)
        reply = f"🧩 {response}\n\n👉 (Nhấn '0' để quay lại menu chính)"
        return reply, False

    # Tìm sách trong kho
    book = next(
        (b for b in get_all_books() if b["title"].lower() == session["order_info"]["book_title"].lower()),
        None
    )
    if not book:
        reply = (
            "❌ Xin lỗi, sách bạn chọn không có trong kho.\n"
            "Vui lòng chọn sách khác.\n\n👉 (Nhấn '0' để quay lại menu chính)"
        )
        return reply, False

    # Lưu đơn hàng
    order = add_order(
        name=session["order_info"]["customer_name"],
        phone=session["order_info"]["phone"],
        address=session["order_info"]["address"],
        book_id=book["book_id"],
        quantity=session["order_info"]["quantity"],
    )

    session.clear()
    reply = (
        f"✅ Đơn hàng của bạn đã được xác nhận!\n\n"
        f"🧾 Mã đơn hàng: {order['order_id']}\n"
        f"📗 Sách: {book['title']}\n"
        f"📦 Số lượng: {order['quantity']}\n"
        f"🏠 Giao đến: {order['address']}\n"
        f"📞 Liên hệ: {order['phone']}\n\n"
        "🎉 Cảm ơn bạn đã đặt hàng tại Bookstore!\n\n"
        "🏠 Quay lại menu chính:\n"
        "- Bấm '1' để Đặt sách\n"
        "- Bấm '2' để Xem sách khả dụng\n"
        "- Bấm '3' để Tra cứu đơn hàng"
    )
    session["state"] = "menu"
    return reply, True
