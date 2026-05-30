# agents/order_agent.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq

from langchain_core.prompts import ChatPromptTemplate
from tools.db_tools import get_order_by_id, get_orders_by_customer, get_customer_by_name, get_customer_by_phone
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

# Agent prompt
prompt = ChatPromptTemplate.from_template("""
You are a helpful Indian e-commerce customer support agent.
You help customers track their orders.

Customer Language: {language}
- If language is "hindi" → reply in simple Hindi
- If language is "hinglish" → reply in mix of Hindi and English
- If language is "english" → reply in English

Customer Emotion: {emotion}
- If emotion is "angry" → be extra apologetic and calm
- If emotion is "frustrated" → be patient and reassuring
- If emotion is "happy" → be friendly and cheerful
- If emotion is "neutral" → be professional and helpful

Order Information:
{order_info}

Customer Message: {customer_message}

Give a helpful, warm response about their order status.
Keep it short — max 3 lines.
Include order ID, product name, status, and expected delivery if available.
""")

def run_order_agent(customer_message: str, customer_id: str = None, 
                    language: str = "english", emotion: str = "neutral"):
    
    order_info = "No order found."
    import re
    # Try to find order by order ID mentioned in message
    words = re.findall(r'SR\d+', customer_message.upper())
    for word in words:
      order = get_order_by_id(word)
      if order:
        order_info = f"""
        Order ID: {order['order_id']}
        Product: {order['product_name']}
        Status: {order['status']}
        Courier: {order['courier']}
        Expected Delivery: {order['expected_delivery']}
        Payment: {order['payment_method']} - {order['payment_status']}
        """
        break

    # If no order ID in message, search by customer_id
    if order_info == "No order found." and customer_id:
        orders = get_orders_by_customer(customer_id)
        if orders:
            latest = orders[0]
            order_info = f"""
            Order ID: {latest['order_id']}
            Product: {latest['product_name']}
            Status: {latest['status']}
            Courier: {latest['courier']}
            Expected Delivery: {latest['expected_delivery']}
            Payment: {latest['payment_method']} - {latest['payment_status']}
            """

    # Run LLM
    chain = prompt | llm
    response = chain.invoke({
        "language": language,
        "emotion": emotion,
        "order_info": order_info,
        "customer_message": customer_message
    })

    return response.content


if __name__ == "__main__":
    # Test 1 - English, neutral
    print("=== TEST 1: English ===")
    print(run_order_agent(
        customer_message="Where is my order SR100234?",
        language="english",
        emotion="neutral"
    ))

    print("\n=== TEST 2: Hinglish, angry ===")
    print(run_order_agent(
        customer_message="mera order SR100235 kahan hai, bahut time ho gaya!",
        language="hinglish",
        emotion="angry"
    ))

    print("\n=== TEST 3: Hindi, happy ===")
    print(run_order_agent(
        customer_message="mera order SR100236 delivered hua kya?",
        language="hindi",
        emotion="happy"
    ))