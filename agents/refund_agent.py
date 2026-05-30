# agents/refund_agent.py

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tools.db_tools import get_order_by_id, get_orders_by_customer
from data.policies import POLICIES
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

prompt = ChatPromptTemplate.from_template("""
You are a helpful Indian e-commerce refund and return support agent.

Customer Language: {language}
- If language is "hindi" → reply in simple Hindi
- If language is "hinglish" → reply in mix of Hindi and English
- If language is "english" → reply in English

Customer Emotion: {emotion}
- If emotion is "angry" → be extra apologetic, offer compensation
- If emotion is "frustrated" → be patient and reassuring
- If emotion is "happy" → be friendly
- If emotion is "neutral" → be professional

Order Information:
{order_info}

Return & Refund Policies:
{policies}

Customer Message: {customer_message}

Based on the order and policies:
1. Check if return is eligible (based on status and return policy)
2. Tell customer clearly if they can or cannot return
3. If eligible → explain exact steps to return
4. If refund → mention how many days it will take
5. Be warm and helpful

Keep response under 4 lines.
""")


def check_return_eligibility(order: dict) -> dict:
    """Check if order is eligible for return"""
    
    non_returnable = ["no return", "no returns"]
    status = order.get("status", "").lower()
    return_policy = order.get("return_policy", "").lower() if order.get("return_policy") else ""
    
    # Check if product is non-returnable
    if any(phrase in return_policy for phrase in non_returnable):
        return {
            "eligible": False,
            "reason": "This product category does not support returns"
        }
    
    # Check order status
    if status == "delivered":
        return {
            "eligible": True,
            "reason": "Order delivered, return window open"
        }
    elif status == "cancelled":
        return {
            "eligible": False,
            "reason": "Order already cancelled, refund already initiated"
        }
    elif status in ["pending", "shipped", "out for delivery"]:
        return {
            "eligible": False,
            "reason": "Order not yet delivered, cannot initiate return yet"
        }
    
    return {"eligible": False, "reason": "Unable to determine eligibility"}


def run_refund_agent(customer_message: str, customer_id: str = None,
                     language: str = "english", emotion: str = "neutral"):
    
    order_info = "No order found."
    eligibility_info = ""

    # Extract order ID from message
    order_ids = re.findall(r'SR\d+', customer_message.upper())
    
    order = None
    for order_id in order_ids:
        order = get_order_by_id(order_id)
        if order:
            break

    # If no order ID in message, get latest order of customer
    if not order and customer_id:
        orders = get_orders_by_customer(customer_id)
        if orders:
            order = orders[0]

    if order:
        eligibility = check_return_eligibility(order)
        eligibility_info = f"Return Eligible: {eligibility['eligible']} — {eligibility['reason']}"
        
        order_info = f"""
        Order ID: {order['order_id']}
        Product: {order['product_name']}
        Status: {order['status']}
        Amount: Rs {order['amount']}
        Payment Method: {order['payment_method']}
        Payment Status: {order['payment_status']}
        {eligibility_info}
        """

    # Get policies
    policies = f"""
    Return Policy: {POLICIES['return']}
    Refund Policy: {POLICIES['refund']}
    """

    chain = prompt | llm
    response = chain.invoke({
        "language": language,
        "emotion": emotion,
        "order_info": order_info,
        "policies": policies,
        "customer_message": customer_message
    })

    return response.content


if __name__ == "__main__":
    
    print("=== TEST 1: Return delivered order (English) ===")
    print(run_refund_agent(
        customer_message="I want to return my order SR100236",
        language="english",
        emotion="neutral"
    ))

    print("\n=== TEST 2: Refund cancelled order (Hinglish, frustrated) ===")
    print(run_refund_agent(
        customer_message="mera order SR100238 cancel hua hai, mujhe refund kab milega?",
        language="hinglish",
        emotion="frustrated"
    ))

    print("\n=== TEST 3: Return non-returnable item (Hindi, angry) ===")
    print(run_refund_agent(
        customer_message="mujhe SR100236 wapas karna hai, saree pasand nahi aayi",
        language="hindi",
        emotion="angry"
    ))

    print("\n=== TEST 4: Return not yet delivered (English) ===")
    print(run_refund_agent(
        customer_message="I want to return SR100234 it hasn't arrived yet",
        language="english",
        emotion="neutral"
    ))