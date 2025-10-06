import streamlit as st
from app import nlu, db, router, utils
from dotenv import load_dotenv
import os, uuid

load_dotenv()

st.set_page_config(page_title='BookStore Chatbot', layout='centered')
st.title('📚 BookStore — Chatbot')

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
sid = st.session_state['session_id']

if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {'role':'assistant','content': 'Chào bạn! Tôi có thể giúp gì cho bạn? (Ví dụ: "Tôi muốn mua 2 cuốn Truyện Kiều")'}
    ]
if 'session_data' not in st.session_state:
    st.session_state['session_data'] = {}

for msg in st.session_state['messages']:
    st.chat_message(msg['role']).markdown(msg['content'])

user_input = st.chat_input('Nhập câu hỏi hoặc yêu cầu...')
if user_input:
    st.session_state['messages'].append({'role':'user','content': user_input})
    st.chat_message('user').markdown(user_input)

    parsed = nlu.parse_user_input(user_input)
    st.chat_message('assistant').markdown('Bot đang xử lý...')

    response = router.handle(parsed, sid, st.session_state['session_data'], db, utils)

    st.session_state['messages'].append({'role':'assistant','content': response})
    st.chat_message('assistant').markdown(response)
