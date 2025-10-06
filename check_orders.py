from app import db

def main():
    print("=== 📦 Orders ===")
    orders = db.list_orders()
    if not orders:
        print("Chưa có đơn hàng nào.")
    else:
        for o in orders:
            print(f"Order ID: {o['order_id']}, Khách: {o['customer_name']}, "
                  f"Sách: {o['book_title']}, SL: {o['quantity']}, "
                  f"Trạng thái: {o['status']}, SĐT: {o['phone']}, Địa chỉ: {o['address']}")

    print("\n=== 📚 Books (Stock) ===")
    books = db.find_books()
    for b in books:
        print(f"[{b['book_id']}] {b['title']} — {b['author']} | Giá: {b['price']} | "
              f"Tồn kho: {b['stock']} | Thể loại: {b['category']}")

if __name__ == "__main__":
    main()
