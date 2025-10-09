from fastapi import FastAPI
from app.api.chat_router import router as chat_router
from app.db.database import init_db

app = FastAPI(title="Bookstore Chatbot", version="1.0")

# Khởi tạo DB
@app.on_event("startup")
def startup():
    init_db()

# Router chính
app.include_router(chat_router, prefix="/chat", tags=["Chatbot"])

@app.get("/")
def root():
    return {"message": "Bookstore Chatbot API đang hoạt động 🚀"}
