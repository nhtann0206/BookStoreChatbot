import streamlit as st
import requests

API_URL = "http://localhost:8000/chat"

st.title("📚 Bookstore Chatbot")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Nhập tin nhắn của bạn...")

if user_input:
    st.session_state.history.append(("user", user_input))
    resp = requests.post(API_URL, json={"user_input": user_input})
    bot_reply = resp.json().get("reply", "Lỗi phản hồi.")
    st.session_state.history.append(("bot", bot_reply))

for role, msg in st.session_state.history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(msg)
