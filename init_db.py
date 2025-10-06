from app.db import init_db
if __name__ == '__main__':
    init_db(seed=True)
    print('Database initialized (bookstore.db)')
