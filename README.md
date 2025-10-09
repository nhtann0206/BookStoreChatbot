BookStore Chatbot (Gemini + Streamlit + SQLite) — Final

# Cài
pip install -r requirements.txt

# Tạo DB và seed dữ liệu
python -m app.db.seed_data

# Chạy backend
uvicorn app.main:app --reload

# Chạy giao diện chat
streamlit run streamlit_app.py

# Structure:
```
bookstore_chatbot/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat_router.py
│   │   └── schemas.py
│   │
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── order_flow.py
│   │   ├── view_books_flow.py
│   │   ├── track_order_flow.py
│   │   └── utils.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── seed_data.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── llm_client.py
│   │
│   ├── cache/
│   └── logs/
│       └── app.log
│
├── streamlit_app.py
├── requirements.txt
└── README.md
```

