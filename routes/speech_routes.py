# File: routes/speech_routes.py

from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from services.openai_service import get_ai_response
from services.zapier_service import send_to_zapier
from models.session_store import session_memory, customer_info
from logic.offer_parser import parse_offer
import json
import os
import re

speech_bp = Blueprint('speech_bp', __name__)

# Load offers from JSON file
current_dir = os.path.dirname(os.path.abspath(__file__))
offers_file = os.path.join(current_dir, "..", "data", "retention_offers.json")
with open(offers_file, "r") as f:
    data = json.load(f)
retention_offers = data["offers"]

accepted_phrases = ["yes", "sounds good", "let’s do it", "i'll take it", "sure", "okay", "i accept", "i'll do that", "that works"]
decline_phrases = ["no", "cancel", "still want to cancel", "go ahead with cancellation", "just cancel"]

def normalize_text(text):
    return text.lower().replace("2", "two").replace("50%", "50 percent")

@speech_bp.route("/collect-info", methods=["POST"])
def collect_info():
    response_text = ""
    call_sid = request.form.get("CallSid")
    speech = request.form.get("SpeechResult", "").strip()
    state = customer_info.get(call_sid, {"step": "name", "retry": 0})

    if state["step"] == "name":
        state["name"] = speech
        state["step"] = "phone"
        response_text = "Thank you. Now please provide the 10-digit phone number associated with your account."

    elif state["step"] == "phone":
        new_digits = re.sub(r"\D", "", speech)
        prior_digits = state.get("phone", "")
        combined = prior_digits + new_digits
        if len(combined) >= 10:
            state["phone"] = combined[:10]
            state["step"] = "done"
            return str(build_gather("Thank you. How can I help you today?", "/process-speech"))
        else:
            state["phone"] = combined
            if state["retry"] == 0:
                state["retry"] += 1
                response_text = "I didn't quite get the full phone number. Please repeat your 10-digit phone number."
            else:
                state["phone"] = "Unknown"
                state["step"] = "done"
                return str(build_gather("Thank you. How can I help you today?", "/process-speech"))

    customer_info[call_sid] = state
    print(f"📇 Captured Customer Info: {state}")
    return str(build_gather(response_text, "/collect-info"))

@speech_bp.route("/process-speech", methods=["POST"])
def process_speech():
    call_sid = request.form.get("CallSid")
    user_input = request.form.get("SpeechResult", "").strip()
    caller_number = request.form.get("From")

    if not user_input:
        return str(build_gather("I'm sorry, I didn't catch that. How can I help you today?", "/process-speech"))

    memory = session_memory.get(call_sid, [])
    memory.append({"role": "user", "content": user_input})
    ai_response = get_ai_response(memory)
    memory.append({"role": "assistant", "content": ai_response})
    session_memory[call_sid] = memory

    print(f"🗣️ User said: {user_input}")
    print(f"🤖 AI replied: {ai_response}")

    info = customer_info.get(call_sid, {})
    name = info.get("name", "Unknown")
    phone = info.get("phone", caller_number)

    ai_response_normalized = normalize_text(ai_response)

    # Detect if the AI made an offer with normalization
    for offer in retention_offers:
        offer_normalized = normalize_text(offer)
        if offer_normalized in ai_response_normalized:
            info["pending_offer"] = offer
            print(f"📝 Offer made: {offer}")
            break

    # Check for user response to pending offer
    pending_offer = info.get("pending_offer")
    if pending_offer:
        if any(p in user_input.lower() for p in accepted_phrases):
            info["offer"] = pending_offer
            info["outcome"] = "accepted"
            info["transcript"] = user_input
            info.pop("pending_offer", None)
        elif any(p in user_input.lower() for p in decline_phrases):
            info["offer"] = pending_offer
            info["outcome"] = "declined"
            info["transcript"] = user_input
            info.pop("pending_offer", None)

    customer_info[call_sid] = info
    print(f"📋 Updated Customer Info: {info}")

    # Fire Zapier only if outcome is set now
    if info.get("outcome"):
        payload = {
            "name": name,
            "phone": phone,
            "email": info.get("email", "Not provided"),
            "offer_presented": info.get("offer", "Not captured"),
            "outcome": info.get("outcome"),
            "transcript": info.get("transcript", "No transcript available")
        }
        print(f"📬 Sending to Zapier: {payload}")
        send_to_zapier(payload)

        if info["outcome"] == "accepted":
            return str(build_hangup(f"Thanks {name}, I’ve confirmed your offer. We're happy to have you stay with us. Goodbye!"))
        else:
            return str(build_hangup("Understood. We'll proceed with your cancellation request. Goodbye!"))

    return str(build_gather(ai_response, "/process-speech"))
    

