import sqlite3
from config import DATABASE_NAME

def connect():
    return sqlite3.connect(DATABASE_NAME, check_same_thread=False)

db = connect()
cursor = db.cursor()

def create_tables():

    # USER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
        fullname TEXT,
        balance INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        ref INTEGER DEFAULT 0,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # PRODUCT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        category TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    # KEY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys_stock(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        key TEXT,
        sold INTEGER DEFAULT 0
    )
    """)

    # ORDER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        price INTEGER,
        key TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # COUPON
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        discount INTEGER,
        quantity INTEGER
    )
    """)

    db.commit()

create_tables()

# ---------------- USER ----------------

def create_user(uid, username, fullname):

    cursor.execute(
        "SELECT id FROM users WHERE id=?",
        (uid,)
    )

    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO users(id,username,fullname)
        VALUES(?,?,?)
        """,
        (
            uid,
            username,
            fullname
        )
    )

    db.commit()

def get_user(uid):

    cursor.execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    )

    return cursor.fetchone()

def add_balance(uid, money):

    cursor.execute(
        """
        UPDATE users
        SET balance=balance+?
        WHERE id=?
        """,
        (
            money,
            uid
        )
    )

    db.commit()

def remove_balance(uid, money):

    cursor.execute(
        """
        UPDATE users
        SET balance=balance-?
        WHERE id=?
        """,
        (
            money,
            uid
        )
    )

    db.commit()

def get_balance(uid):

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE id=?
        """,
        (
            uid,
        )
    )

    r = cursor.fetchone()

    if r:
        return r[0]

    return 0