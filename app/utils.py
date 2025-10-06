def format_action_result(res):
    if isinstance(res, list):
        if not res:
            return 'Không tìm thấy sách phù hợp.'
        lines = ['**Kết quả tìm kiếm:**']
        for r in res:
            lines.append(f"- [{r.get('book_id')}] {r.get('title')} — {r.get('author')} | Giá: {r.get('book_price') or r.get('price')} | Tồn: {r.get('stock')}")
        return '\n'.join(lines)
    if isinstance(res, dict):
        if res.get('order_id'):
            return f"✅ Đơn đã tạo — Order ID: {res.get('order_id')}, Sách: {res.get('book_title')}, SL: {res.get('quantity')}, Trạng thái: {res.get('status')}."
        if res.get('error'):
            return '⚠️ ' + res.get('error')
    return str(res)
