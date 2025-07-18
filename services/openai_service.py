
import os
import json
from openai import OpenAI
from services.account_service import (
    lookup_user_by_phone,
    cancel_membership,
    pause_membership,
    apply_retention_offer
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

RETENTION_OFFERS = [
    "50% off next two billing cycles",
    "Pause membership for up to 3 months",
    "Downgrade to a lower plan",
    "Apply $10 account credit"
]

functions = [
    {
        "name": "lookup_user_by_phone",
        "description": "Verify user by looking up their phone number in AMP.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": { "type": "string", "description": "The user's 10-digit phone number." }
            },
            "required": ["phone_number"]
        }
    },
    {
        "name": "cancel_membership",
        "description": "Cancel the user's membership via AMP API.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": { "type": "string", "description": "AMP user ID." }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "pause_membership",
        "description": "Pause the user's membership via AMP API.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": { "type": "string", "description": "AMP user ID." }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "apply_retention_offer",
        "description": "Apply a retention offer to the user's account.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": { "type": "string" },
                "offer": { "type": "string", "description": "The specific retention offer." }
            },
            "required": ["user_id", "offer"]
        }
    }
]

def run_chat_completion(history):
    try:
        phone_number = None
        user_id = None
        user_name = None

        for msg in history:
            if msg["role"] == "user":
                digits = ''.join(filter(str.isdigit, msg["content"]))
                if len(digits) == 10:
                    phone_number = digits
            elif msg["role"] == "function":
                try:
                    parsed = json.loads(msg.get("content", "{}"))
                    user_id = parsed.get("id") or parsed.get("user_id")
                    user_name = parsed.get("name")
                except:
                    pass

        system_prompt = f"""
        You are Hurricane Express Wash's AI Retention Agent.
        Always address the user by name if known: {user_name or 'Customer'}.
        Only offer the following retention options: {", ".join(RETENTION_OFFERS)}.
        If user_id is known and they are not an active member, escalate with outcome = follow-up-needed.
        Always confirm if the customer is open to a retention offer before canceling.
        Reply in strict JSON:
        {{
          "reply": "Message to user",
          "offer": "Offer made or 'none'",
          "outcome": "accepted / declined / cancellation processed / ongoing / follow-up-needed",
          "transcript": "Summary of conversation"
        }}
        Do not wrap or decorate your reply. Only emit valid JSON.
        """.strip()

        messages = [{"role": "system", "content": system_prompt}] + history

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=functions,
            function_call="auto"
        )

        choice = response.choices[0]
        if choice.finish_reason == "function_call":
            fn = choice.message.function_call
            args = json.loads(fn.arguments)
            name = fn.name

            if name == "lookup_user_by_phone":
                result = lookup_user_by_phone(args["phone_number"])
            elif name == "cancel_membership":
                result = cancel_membership(args["user_id"])
            elif name == "pause_membership":
                result = pause_membership(args["user_id"])
            elif name == "apply_retention_offer":
                if args["offer"] not in RETENTION_OFFERS:
                    return {"reply": "That offer is not available.", "offer": "none", "outcome": "follow-up-needed", "transcript": "Invalid offer attempt."}
                result = apply_retention_offer(args["user_id"], args["offer"])
            else:
                result = {"error": "Unknown function"}

            history.append({"role": "function", "name": name, "content": json.dumps(result)})
            return run_chat_completion(history)

        else:
            try:
                return json.loads(choice.message.content.strip())
            except Exception:
                return {
                    "reply": choice.message.content.strip(),
                    "offer": "none",
                    "outcome": "follow-up-needed",
                    "transcript": "Could not parse response."
                }

    except Exception as e:
        return {
            "reply": "Sorry, something went wrong.",
            "offer": "none",
            "outcome": "follow-up-needed",
            "transcript": str(e)
        }
