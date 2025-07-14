# File: services/openai_service.py

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load your approved retention offers from data if desired
# For now, keeping the static list for clarity
retention_offers_text = (
    "1) Free month of service, 2) Downgrade membership, "
    "3) Pause membership, 4) Apply credits."
)

system_prompt = (
    "You are a helpful and persuasive AI retention assistant for Hurricane Express Wash. "
    "Start by asking why the customer wants to cancel. Listen carefully. "
    "Once the reason is given, offer one of the following options if appropriate: "
    + retention_offers_text + " "
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
