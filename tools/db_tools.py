# tools/db_tools.py

import sqlite3

DB_PATH = "ecommerce.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # returns dict instead of tuple
    return conn

def get_order_by_id(order_id: str):
    """Fetch order details by order ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_orders_by_customer(customer_id: str):
    """Fetch all orders for a customer"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_by_phone(phone: str):
    """Fetch customer by phone number"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_customer_by_name(name: str):
    """Fetch customer by name (partial match)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE name LIKE ?", (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_product_by_id(product_id: str):
    """Fetch product details by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def search_products(keyword: str):
    """Search products by name or category"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products 
        WHERE name LIKE ? OR category LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_conversation(customer_id: str, message: str, sender: str, emotion: str = "neutral"):
    """Save a conversation message to database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (customer_id, message, sender, emotion)
        VALUES (?, ?, ?, ?)
    """, (customer_id, message, sender, emotion))
    conn.commit()
    conn.close()

def get_conversation_history(customer_id: str, limit: int = 10):
    """Get last N messages for a customer"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message, sender, emotion, timestamp 
        FROM conversations 
        WHERE customer_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (customer_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_emotion_log(customer_id: str, emotion: str, intensity: int):
    """Log detected emotion for a customer"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emotion_logs (customer_id, emotion, intensity)
        VALUES (?, ?, ?)
    """, (customer_id, emotion, intensity))
    conn.commit()
    conn.close()