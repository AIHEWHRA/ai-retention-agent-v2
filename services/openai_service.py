# File: services/openai_service.py

from openai import OpenAI
import os
import json
import time

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Load offers from JSON data file
def load_retention_offers():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    offers_file = os.path.join(current_dir, "..", "data", "retention_offers.json")
    with open(offers_file, "r") as f:
        data = json.load(f)
    return data["offers"]

retention_offers = load_retention_offers()
offers_list_text = ", ".join(retention_offers)

retention_prompt = (
    "You are a helpful and persuasive AI retention assistant for Hurricane Express Wash. "
    "Start by asking why the customer wants to cancel. Listen carefully. "
    f"Once the reason is given, offer one of the following options if appropriate: {offers_list_text}. "
    "Only offer options from this list. Never invent new offers. "
    "If a customer accepts an offer, confirm it and thank them. "
    "If they decline after being offered something, proceed with cancellation. "
    "Always be friendly, empathetic, and concise."
)

def get_ai_response(history, use_retrieval=False):
    try:
        if use_retrieval:
            # Use Assistants API with Retrieval (for FAQs, SOPs)
            thread = client.beta.threads.create()
            for msg in history:
                client.beta.threads.messages.create(thread.id, role=msg["role"], content=msg["content"])

            run = client.beta.threads.runs.create(thread.id, assistant_id=ASSISTANT_ID)

            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(thread.id, run.id)

            response = client.beta.threads.messages.list(thread.id)
            return response.data[0].content[0].text.value.strip()
        
        else:
            # Use regular GPT chat for retention loop
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": retention_prompt},
                    *history
                ]
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ AI error:", e)
        return "Sorry, I’m having trouble responding right now. Please try again later."
