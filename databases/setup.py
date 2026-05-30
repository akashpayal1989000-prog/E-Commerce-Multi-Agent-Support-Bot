# database/setup.py

import sqlite3
import sys
import os

# This allows us to import from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.customers import CUSTOMERS
from data.orders import ORDERS
from data.products import PRODUCTS
from data.policies import POLICIES

DB_PATH = "ecommerce.db"

def create_tables(conn):
    cursor = conn.cursor()

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            pincode TEXT,
            language TEXT
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            price INTEGER,
            stock TEXT,
            rating REAL,
            description TEXT,
            return_policy TEXT,
            warranty TEXT
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            product_id TEXT,
            product_name TEXT,
            quantity INTEGER,
            amount INTEGER,
            status TEXT,
            courier TEXT,
            awb_code TEXT,
            order_date TEXT,
            expected_delivery TEXT,
            city TEXT,
            payment_method TEXT,
            payment_status TEXT,
            razorpay_order_id TEXT,
            razorpay_payment_id TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        )
    """)

    # Conversations table (memory)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            message TEXT,
            sender TEXT,
            emotion TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Emotion logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            emotion TEXT,
            intensity INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            rating INTEGER,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    print("✅ All tables created!")


def insert_data(conn):
    cursor = conn.cursor()

    # Insert customers
    for c in CUSTOMERS:
        cursor.execute("""
            INSERT OR IGNORE INTO customers 
            VALUES (?,?,?,?,?,?,?)
        """, (
            c["customer_id"], c["name"], c["email"],
            c["phone"], c["city"], c["pincode"], c["language"]
        ))

    # Insert products
    for p in PRODUCTS:
        cursor.execute("""
            INSERT OR IGNORE INTO products 
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            p["product_id"], p["name"], p["category"],
            p["price"], p["stock"], p["rating"],
            p["description"], p["return_policy"], p["warranty"]
        ))

    # Insert orders
    for o in ORDERS:
        cursor.execute("""
            INSERT OR IGNORE INTO orders 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            o["order_id"], o["customer_id"], o["product_id"],
            o["product_name"], o["quantity"], o["amount"],
            o["status"], o["courier"], o["awb_code"],
            o["order_date"], o["expected_delivery"], o["city"],
            o["payment_method"], o["payment_status"],
            o["razorpay_order_id"], o["razorpay_payment_id"]
        ))

    conn.commit()
    print("✅ All data inserted!")


def setup_database():
    print("🔧 Setting up database...")
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    insert_data(conn)
    conn.close()
    print(f"✅ Database ready at {DB_PATH}")


if __name__ == "__main__":
    setup_database()