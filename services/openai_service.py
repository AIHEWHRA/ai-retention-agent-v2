# File: services/openai_service.py

from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load offers from JSON data file
def load_retention_offers():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    offers_file = os.path.join(current_dir, "..", "data", "retention_offers.json")
    with open(offers_file, "r") as f:
        data = json.load(f)
    return data["offers"]

retention_offers = load_retention_offers()
offers_list_text = ", ".join(retention_offers)

system_prompt = (
    "You are a helpful and persuasive AI retention assistant for Hurricane Express Wash. "
    "Start by asking why the customer wants to cancel. Listen carefully. "
    f"Once the reason is given, offer one of the following options if appropriate: {offers_list_text}. "
    "Only offer options from this list. Never invent new offers. "
    "If a customer accepts an offer, confirm it and thank them. "
    "If they decline after being offered something, proceed with cancellation. "
    "Always be friendly, empathetic, and concise."
)

def get_ai_response(history):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *history
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT error:", e)
        return "Sorry, I’m having trouble responding right now. Please try again later."
