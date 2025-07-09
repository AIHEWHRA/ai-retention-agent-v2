from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_response(history):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content":
                 "You are a helpful and persuasive AI retention assistant for Hurricane Express Wash..."},
                *history
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT error:", e)
        return "Sorry, I’m having trouble responding right now. Please try again later."
