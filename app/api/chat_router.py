from fastapi import APIRouter
from app.api.schemas import ChatRequest, ChatResponse
from app.logic import order_flow, view_books_flow, track_order_flow

router = APIRouter()
user_sessions = {}

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_input = request.user_input.strip()
    session = user_sessions.get("default", {"state": "menu"})

    if "state" not in session:
        session["state"] = "menu"
        
    # Quay lại menu chính
    if user_input == "0":
        session["state"] = "menu"
        session["order_info"] = {}
        reply = (
            "↩️ Đã quay lại menu chính.\n\n"
            "📚 Cảm ơn quý khách đã sử dụng Bookstore Chatbot!\n"
            "Vui lòng chọn tính năng:\n"
            "- Bấm '1' để Đặt sách\n"
            "- Bấm '2' để Xem các loại sách khả dụng\n"
            "- Bấm '3' để Tra cứu đơn hàng"
        )
        user_sessions["default"] = session
        return ChatResponse(reply=reply)

    # Menu chính
    if session["state"] == "menu":
        if user_input == "1":
            session["state"] = "order"
            session["order_info"] = {}
            reply = (
                "🛒 Bạn đã chọn đặt sách.\n"
                "Vui lòng nhập thông tin đặt hàng, ví dụ:\n"
                "'Tôi muốn mua 2 cuốn Truyện Kiều giao cho Nam tại Hà Nội, SĐT 0123456789'.\n\n"
                "(Hoặc bấm '0' để quay lại menu chính.)"
            )
        elif user_input == "2":
            reply, done = view_books_flow.handle(user_input, session)
            session["state"] = "menu"
        elif user_input == "3":
            session["state"] = "track"
            reply = (
                "🔎 Vui lòng nhập tên người đặt hàng để tra cứu đơn hàng.\n"
                "(Hoặc bấm '0' để quay lại menu chính.)"
            )
        else:
            reply = (
                "📚 Cảm ơn quý khách đã sử dụng Bookstore Chatbot!\n"
                "Vui lòng chọn tính năng:\n"
                "- Bấm '1' để Đặt sách\n"
                "- Bấm '2' để Xem các loại sách khả dụng\n"
                "- Bấm '3' để Tra cứu đơn hàng"
            )

    # Đặt sách
    elif session["state"] == "order":
        reply, done = order_flow.handle(user_input, session)
        if done:
            session["state"] = "menu"

    # Tra cứu đơn hàng
    elif session["state"] == "track":
        reply, done = track_order_flow.handle(user_input, session)
        if done:
            session["state"] = "menu"
            reply += "\n\n↩️ Quay lại menu chính."

    user_sessions["default"] = session
    return ChatResponse(reply=reply)
