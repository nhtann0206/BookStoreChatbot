import logging
logging.basicConfig(level=logging.INFO)

REQUIRED_ORDER_FIELDS = ['book_id','quantity','customer_name','phone','address']

def _next_missing(pending):
    for f in REQUIRED_ORDER_FIELDS:
        if pending.get(f) in (None, ''):
            return f
    return None

def handle(parsed: dict, session_id: str, session_store: dict, db_module, utils_module) -> str:
    # session_store is a dict stored in streamlit's session_state
    if session_id not in session_store:
        session_store[session_id] = {'pending_order':{}, 'intent':None}
    sess = session_store[session_id]
    intent = parsed.get('action')
    if intent == 'search':
        filters = parsed.get('filters', {})
        books = db_module.find_books(title=filters.get('title',''), author=filters.get('author',''), category=filters.get('category',''))
        return utils_module.format_action_result(books)
    if intent == 'chitchat':
        raw = parsed.get('raw','')
        if 'chào' in raw.lower():
            return 'Xin chào bạn 👋! Tôi có thể giúp gì cho bạn?'
        return '🙂 Tôi luôn sẵn sàng hỗ trợ bạn.'
    if intent == 'order':
        sess['intent'] = 'order'
        pending = sess['pending_order']
        # merge parsed fields
        # book_title/author -> resolve to book_id
        bt = parsed.get('book_title','')
        if bt:
            candidates = db_module.find_books(title=bt)
            if candidates:
                pending['book_id'] = candidates[0]['book_id']
                pending['book_title'] = candidates[0]['title']
        if parsed.get('quantity'):
            pending['quantity'] = int(parsed.get('quantity'))
        if parsed.get('customer_name'):
            pending['customer_name'] = parsed.get('customer_name')
        if parsed.get('phone'):
            pending['phone'] = parsed.get('phone')
        if parsed.get('address'):
            pending['address'] = parsed.get('address')
        # check missing
        miss = [f for f in REQUIRED_ORDER_FIELDS if pending.get(f) in (None,'')]
        if miss:
            nxt = _next_missing(pending)
            if nxt == 'book_id':
                return 'Bạn muốn đặt sách nào?'
            if nxt == 'quantity':
                return 'Bạn muốn mua bao nhiêu cuốn?'
            if nxt == 'customer_name':
                return 'Bạn vui lòng cho tôi biết tên của bạn để tiếp tục đặt hàng.'
            if nxt == 'phone':
                return 'Vui lòng cung cấp số điện thoại để tôi ghi nhận đơn hàng.'
            if nxt == 'address':
                return 'Bạn cho tôi xin địa chỉ giao hàng nhé.'
        # all good -> create order
        res = db_module.create_order(pending.get('customer_name'), pending.get('phone'), pending.get('address'), pending.get('book_id'), int(pending.get('quantity')))
        # reset pending
        session_store[session_id] = {'pending_order':{}, 'intent':None}
        return utils_module.format_action_result(res)
    return '⚠️ Tôi chưa hiểu yêu cầu.'
