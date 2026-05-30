# tools/emotion_tools.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile"
)

emotion_prompt = ChatPromptTemplate.from_template("""
Analyze the emotion in this customer message.

Customer Message: {message}

Reply with ONLY a JSON object, nothing else:
{{
    "emotion": "angry" or "frustrated" or "happy" or "neutral",
    "intensity": 1 to 10,
    "language": "hindi" or "hinglish" or "english"
}}

Rules:
- angry → strong negative words, complaints, threats
- frustrated → mild negative, waiting too long, confused
- happy → positive words, thank you, great
- neutral → simple questions, no emotion
- intensity → 1 is very mild, 10 is very extreme
- language → detect if message is hindi, hinglish or english
""")


def detect_emotion(message: str) -> dict:
    """Detect emotion, intensity and language from customer message"""
    
    try:
        chain = emotion_prompt | llm
        response = chain.invoke({"message": message})
        
        # Clean response and parse JSON
        import json
        text = response.content.strip()
        
        # Remove markdown if present
        text = text.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(text)
        return {
            "emotion": result.get("emotion", "neutral"),
            "intensity": result.get("intensity", 5),
            "language": result.get("language", "english")
        }
    
    except Exception as e:
        # Default fallback if LLM fails
        return {
            "emotion": "neutral",
            "intensity": 5,
            "language": "english"
        }


if __name__ == "__main__":

    test_messages = [
        "Where is my order SR100234?",
        "mera order kahan hai bahut time ho gaya, bahut gussa aa raha hai!",
        "Thank you so much, my order arrived perfectly!",
        "mujhe refund chahiye, order cancel kar do",
        "yeh kya bakwaas service hai, order nahi aaya abhi tak!!",
        "Nike shoes available hai kya?"
    ]

    print("=== EMOTION DETECTION TESTS ===\n")
    for msg in test_messages:
        result = detect_emotion(msg)
        print(f"Message : {msg}")
        print(f"Emotion : {result['emotion']} (intensity: {result['intensity']})")
        print(f"Language: {result['language']}")
        print("-" * 50)