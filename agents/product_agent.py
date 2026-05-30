# agents/product_agent.py

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tools.db_tools import search_products, get_product_by_id
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

prompt = ChatPromptTemplate.from_template("""
You are a helpful Indian e-commerce product specialist agent.
You help customers find products, check prices, stock, and warranty.

Customer Language: {language}
- If language is "hindi" → reply in simple Hindi
- If language is "hinglish" → reply in mix of Hindi and English  
- If language is "english" → reply in English

Customer Emotion: {emotion}
- If emotion is "angry" → be extra helpful and apologetic
- If emotion is "frustrated" → be patient
- If emotion is "happy" → be enthusiastic and friendly
- If emotion is "neutral" → be professional

Products Found:
{products_info}

Customer Message: {customer_message}

Based on products found:
1. Answer their specific question (price, stock, warranty, return policy)
2. If asking for recommendation → suggest best match with reason
3. Mention price in Rs (rupees)
4. Keep response under 4 lines
5. Be warm and helpful
""")


def run_product_agent(customer_message: str, language: str = "english", 
                      emotion: str = "neutral"):

    products_info = "No products found."

    # Keywords to search from message
    # Extract meaningful words (ignore common words)
    ignore_words = {
        "ka", "ki", "ke", "hai", "kya", "mujhe", "mera", "mere",
        "is", "the", "a", "an", "what", "how", "much", "price",
        "cost", "tell", "me", "about", "do", "you", "have", "i",
        "want", "need", "looking", "for", "can", "please", "stock",
        "available", "suggest", "recommend", "best", "good", "karo",
        "batao", "chahiye", "accha", "acha"
    }

    words = customer_message.lower().split()
    search_words = [w for w in words if w not in ignore_words and len(w) > 2]

    # Search products for each keyword
    found_products = []
    seen_ids = set()

    for word in search_words:
        results = search_products(word)
        for p in results:
            if p["product_id"] not in seen_ids:
                found_products.append(p)
                seen_ids.add(p["product_id"])

    if found_products:
        products_info = ""
        for p in found_products[:3]:  # max 3 products
            products_info += f"""
            Product: {p['name']}
            Category: {p['category']}
            Price: Rs {p['price']}
            Stock: {p['stock']}
            Rating: {p['rating']}/5
            Description: {p['description']}
            Return Policy: {p['return_policy']}
            Warranty: {p['warranty']}
            ---
            """

    chain = prompt | llm
    response = chain.invoke({
        "language": language,
        "emotion": emotion,
        "products_info": products_info,
        "customer_message": customer_message
    })

    return response.content


if __name__ == "__main__":

    print("=== TEST 1: Price check (English) ===")
    print(run_product_agent(
        customer_message="What is the price of OnePlus phone?",
        language="english",
        emotion="neutral"
    ))

    print("\n=== TEST 2: Stock check (Hinglish) ===")
    print(run_product_agent(
        customer_message="Nike shoes available hai kya stock mein?",
        language="hinglish",
        emotion="neutral"
    ))

    print("\n=== TEST 3: Recommendation (Hindi) ===")
    print(run_product_agent(
        customer_message="mujhe ek accha phone suggest karo budget mein",
        language="hindi",
        emotion="happy"
    ))

    print("\n=== TEST 4: Warranty check (English) ===")
    print(run_product_agent(
        customer_message="what is the warranty on Prestige induction cooktop?",
        language="english",
        emotion="neutral"
    ))