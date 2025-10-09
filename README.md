# 🤖 Bookstore Chatbot

Một chatbot hỗ trợ đặt sách, tra cứu đơn hàng và xem danh sách sách khả dụng — built with FastAPI, Streamlit và LLM.

---

## Mục lục
- Giới thiệu
- Tính năng chính
- Kiến trúc hệ thống
- Cấu trúc thư mục
- Cài đặt & Chạy thử
- Luồng hoạt động chính (pseudocode)
- Công nghệ sử dụng
- Hướng phát triển
- Tác giả

---

## Giới thiệu

**Bookstore Chatbot** là dự án demo hệ thống bán sách qua hội thoại. Người dùng tương tác bằng menu hoặc nhập câu tự nhiên (tiếng Việt). Hệ thống xử lý logic đặt hàng, trích xuất entity bằng regex/NLU thủ công, và dùng LLM để sinh phản hồi tự nhiên (không để LLM quyết định luồng).

---

## Tính năng chính

1. **Đặt sách**
   - Nhận tên sách, số lượng, tên khách, địa chỉ, số điện thoại.
   - Nếu thiếu thông tin → hỏi lại (LLM sinh câu hỏi), nếu đủ → lưu đơn hàng.
   - Hỗ trợ bấm `0` để quay lại menu chính.
2. **Xem sách khả dụng**
   - Liệt kê toàn bộ bản ghi trong bảng `Books` (title, author, price, stock, category).
3. **Tra cứu đơn hàng**
   - Nhập tên người đặt (case-insensitive) → trả về danh sách đơn tương ứng (order_id, book_title, quantity, status).
4. **Menu điều hướng**
   - Khi hoàn tất một luồng, tự động quay lại menu chính.

---

## Kiến trúc hệ thống

```
User ↔ Streamlit UI ↔ FastAPI Backend ↔ SQLite DB (app/db/bookstore.db)
                                      ↕
                                     LLM (Google GenAI / gemini)
```

- Streamlit: giao diện chat demo
- FastAPI: API, session state, xử lý luồng logic
- SQLite: lưu Books, Orders
- LLM: chỉ sinh các phản hồi tự nhiên (prompt từ backend, không để LLM quyết định logic)

---

## Cấu trúc thư mục (đề xuất)

```
bookstore_chatbot_final/
├── app/
│   ├── api/
│   │   ├── chat_router.py
│   │   └── schemas.py
│   ├── db/
│   │   ├── database.py
│   │   └── seed_data.py
│   ├── logic/
│   │   ├── order_flow.py
│   │   ├── view_books_flow.py
│   │   ├── track_order_flow.py
│   │   └── utils.py
│   ├── llm/
│   │   └── llm_client.py
│   ├── main.py
│   └── cache/
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## Cài đặt & Chạy thử

1. Tạo virtualenv và cài dependencies:
```bash
python -m venv venv
source venv/bin/activate   # mac/linux
pip install -r requirements.txt
```

2. Khởi tạo database và seed dữ liệu:
```bash
python -c "from app.db.database import init_db; init_db()"
python app/db/seed_data.py
```

3. Chạy backend FastAPI:
```bash
uvicorn app.main:app --reload
```

4. Chạy frontend demo Streamlit:
```bash
streamlit run streamlit_app.py
```

---

## Database schema

- **Books**: `(book_id INTEGER PK, title TEXT, author TEXT, price INTEGER, stock INTEGER, category TEXT)`
- **Orders**: `(order_id INTEGER PK, customer_name TEXT, phone TEXT, address TEXT, book_id INTEGER FK, quantity INTEGER, status TEXT)`

---

## Công nghệ sử dụng

- Python 3.13
- FastAPI (backend)
- Streamlit (frontend demo)
- SQLite (db)
- google-genai (gemini-2.5-flash-lite) hoặc tương tự (LLM)
- requests, python-dotenv, pydantic, uvicorn

---

## Hướng phát triển

- Nâng cấp NLU: hybrid regex + light LLM-assisted parsing (only for disambiguation)
- Thêm authentication & user profiles
- Hỗ trợ giỏ hàng nhiều sản phẩm
- Xử lý tiền tệ, mã giảm giá
- Triển khai production: Docker, CI/CD, hosted DB

---

## Tác giả

Nguyễn Hữu Tấn
