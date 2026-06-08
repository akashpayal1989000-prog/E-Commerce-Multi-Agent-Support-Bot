# agents/supervisor.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from agents.order_agent import run_order_agent
from agents.refund_agent import run_refund_agent
from agents.product_agent import run_product_agent
from tools.emotion_tools import detect_emotion
from tools.db_tools import save_conversation, save_emotion_log

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

# ── State ──────────────────────────────────────────
# This is the shared state that flows through the graph
class SupportState(TypedDict):
    customer_message: str
    customer_id: str
    emotion: str
    intensity: int
    language: str
    intent: str
    response: str

# ── Node 1: Detect Emotion & Language ─────────────
def emotion_node(state: SupportState) -> SupportState:
    print("🔍 Detecting emotion and language...")
    result = detect_emotion(state["customer_message"])
    state["emotion"] = result["emotion"]
    state["intensity"] = result["intensity"]
    state["language"] = result["language"]

    # Save emotion to database
    if state.get("customer_id"):
        save_emotion_log(
            state["customer_id"],
            result["emotion"],
            result["intensity"]
        )
    return state

# ── Node 2: Detect Intent ──────────────────────────
intent_prompt = ChatPromptTemplate.from_template("""
Classify this customer support message into one of these intents:

Message: {message}

Intents:
- order_tracking → asking about order status, location, delivery
- refund_return → asking about return, refund, cancel
- product_query → asking about product price, stock, warranty, recommendation
- escalation → very angry, wants human agent, abusive language
- general → greeting, thank you, other

Reply with ONLY the intent word, nothing else.
""")

def intent_node(state: SupportState) -> SupportState:
    print("🎯 Detecting intent...")
    chain = intent_prompt | llm
    response = chain.invoke({"message": state["customer_message"]})
    state["intent"] = response.content.strip().lower()
    print(f"   Intent: {state['intent']}")
    return state

# ── Node 3: Route to correct agent ────────────────
def route_to_agent(state: SupportState) -> str:
    """This decides which node to go to next"""
    intent = state.get("intent", "general")
    intensity = state.get("intensity", 0)

    # If very angry (intensity 9-10) → escalate to human
    if intensity >= 9:
        return "escalation_node"

    if intent == "order_tracking":
        return "order_node"
    elif intent == "refund_return":
        return "refund_node"
    elif intent == "product_query":
        return "product_node"
    elif intent == "escalation":
        return "escalation_node"
    else:
        return "general_node"

# ── Node 4a: Order Agent ───────────────────────────
def order_node(state: SupportState) -> SupportState:
    print("📦 Running Order Agent...")
    state["response"] = run_order_agent(
        customer_message=state["customer_message"],
        customer_id=state.get("customer_id"),
        language=state["language"],
        emotion=state["emotion"]
    )
    return state

# ── Node 4b: Refund Agent ──────────────────────────
def refund_node(state: SupportState) -> SupportState:
    print("🔄 Running Refund Agent...")
    state["response"] = run_refund_agent(
        customer_message=state["customer_message"],
        customer_id=state.get("customer_id"),
        language=state["language"],
        emotion=state["emotion"]
    )
    return state

# ── Node 4c: Product Agent ─────────────────────────
def product_node(state: SupportState) -> SupportState:
    print("🛍️ Running Product Agent...")
    state["response"] = run_product_agent(
        customer_message=state["customer_message"],
        language=state["language"],
        emotion=state["emotion"]
    )
    return state

# ── Node 4d: Escalation ────────────────────────────
def escalation_node(state: SupportState) -> SupportState:
    print("🚨 Escalating to human agent...")
    if state["language"] == "hindi":
        state["response"] = "Aapki samasya ke liye hum aapko apne senior agent se connect kar rahe hain. Kripya 2-3 minute prateeksha karein. 🙏"
    elif state["language"] == "hinglish":
        state["response"] = "Aapki problem ke liye humara senior agent aapse connect karega. Please 2-3 minutes wait karein. 🙏"
    else:
        state["response"] = "We are connecting you to a senior support agent right away. Please wait 2-3 minutes. 🙏"
    return state

# ── Node 4e: General ───────────────────────────────
def general_node(state: SupportState) -> SupportState:
    print("💬 Running General Response...")
    if state["language"] == "hindi":
        state["response"] = "Namaste! Main aapki kaise madad kar sakta hoon? Aap order tracking, refund, ya product ke baare mein pooch sakte hain."
    elif state["language"] == "hinglish":
        state["response"] = "Hello! Main aapki kaise help kar sakta hoon? Order track karna ho, refund chahiye, ya product query ho — batao!"
    else:
        state["response"] = "Hello! How can I help you today? I can assist with order tracking, refunds, returns, and product queries."
    return state

# ── Node 5: Save Conversation ──────────────────────
def save_node(state: SupportState) -> SupportState:
    print("💾 Saving conversation...")
    if state.get("customer_id"):
        save_conversation(
            state["customer_id"],
            state["customer_message"],
            "user",
            state["emotion"]
        )
        save_conversation(
            state["customer_id"],
            state["response"],
            "bot",
            "neutral"
        )
    return state

# ── Build the Graph ────────────────────────────────
def build_graph():
    graph = StateGraph(SupportState)

    # Add all nodes
    graph.add_node("emotion_node", emotion_node)
    graph.add_node("intent_node", intent_node)
    graph.add_node("order_node", order_node)
    graph.add_node("refund_node", refund_node)
    graph.add_node("product_node", product_node)
    graph.add_node("escalation_node", escalation_node)
    graph.add_node("general_node", general_node)
    graph.add_node("save_node", save_node)

    # Entry point
    graph.set_entry_point("emotion_node")

    # Flow: emotion → intent → route
    graph.add_edge("emotion_node", "intent_node")
    graph.add_conditional_edges("intent_node", route_to_agent, {
        "order_node": "order_node",
        "refund_node": "refund_node",
        "product_node": "product_node",
        "escalation_node": "escalation_node",
        "general_node": "general_node"
    })

    # All agents → save → END
    graph.add_edge("order_node", "save_node")
    graph.add_edge("refund_node", "save_node")
    graph.add_edge("product_node", "save_node")
    graph.add_edge("escalation_node", "save_node")
    graph.add_edge("general_node", "save_node")
    graph.add_edge("save_node", END)

    return graph.compile()


# ── Run Function ───────────────────────────────────
def run_support_bot(customer_message: str, customer_id: str = None):
    graph = build_graph()
    
    initial_state = SupportState(
        customer_message=customer_message,
        customer_id=customer_id or "",
        emotion="neutral",
        intensity=0,
        language="english",
        intent="",
        response=""
    )
    
    result = graph.invoke(initial_state)
    return result["response"]


if __name__ == "__main__":
    tests = [
        ("Where is my order SR100234?", "C001"),
        ("mera order SR100235 kahan hai, bahut time ho gaya!", "C002"),
        ("I want to return my order SR100236", "C003"),
        ("OnePlus phone ki price kya hai?", "C001"),
        ("yeh bakwaas service hai!! main abhi consumer forum mein complaint karunga!!", "C002"),
        ("Hello, how are you?", None),
    ]

    print("=" * 60)
    for message, cid in tests:
        print(f"\n👤 Customer: {message}")
        print(f"🤖 Bot: {run_support_bot(message, cid)}")
        print("-" * 60)