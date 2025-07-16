# File: routes/speech_routes.py

from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from services.openai_service import get_ai_response
from services.zapier_service import send_to_zapier
from models.session_store import session_memory, customer_info
from services.account_service import find_user_by_phone
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
noise_phrases = [
    "clears throat", "cough", "paper rustling", "background noise", 
    "typing", "unintelligible", "noise", "unknown speech", ""
]

cancel_keywords = ["cancel", "stop membership", "end my membership", "terminate membership"]
location_keywords = ["location", "closest", "near me", "address"]
faq_keywords = ["how do i", "app help", "faq", "troubleshoot", "support", "mobile app"]


def normalize_text(text):
    return text.lower().replace("2", "two").replace("50%", "50 percent")

@speech_bp.route("/collect-info", methods=["POST"])
def collect_info():
    call_sid = request.form.get("CallSid")

    # Always reset for new calls to avoid stuck states
    customer_info[call_sid] = {"step": "verify", "retry": 0}

    state = customer_info[call_sid]
    speech = request.form.get("SpeechResult", "").strip()

    if state["step"] == "verify":
        incoming_phone = request.form.get("From").replace("+1", "")
        user_lookup = find_user_by_phone(incoming_phone)

        if user_lookup and isinstance(user_lookup, list) and len(user_lookup) > 0:
            user = user_lookup[0]
            state["verified"] = True
            state["user_id"] = user.get("id")
            state["name"] = user.get("name", "there")
            state["step"] = "done"
            customer_info[call_sid] = state
            greeting = f"Hey {state['name']}, thank you for calling in today. How can we help you?"
            return str(build_gather(greeting, "/process-speech"))
        else:
            state["verified"] = False
            state["step"] = "mobile_app_check"
            customer_info[call_sid] = state
            response_text = "Are you a Hurricane Express mobile app user? Please say yes or no."
            return str(build_gather(response_text, "/collect-info"))

    elif state["step"] == "mobile_app_check":
        if "yes" in speech.lower():
            state["step"] = "collect_phone"
            response_text = "Please say the 10-digit phone number associated with your mobile app account."
        elif "no" in speech.lower():
            state["step"] = "collect_name"
            response_text = "No problem. Let's get your info. Please say your first and last name."
        else:
            response_text = "I didn't catch that. Are you a mobile app user? Please say yes or no."

        customer_info[call_sid] = state
        return str(build_gather(response_text, "/collect-info"))

    elif state["step"] == "collect_phone":
        new_digits = re.sub(r"\D", "", speech)
        if len(new_digits) == 10:
            user_lookup = find_user_by_phone(new_digits)
            if user_lookup and isinstance(user_lookup, list) and len(user_lookup) > 0:
                user = user_lookup[0]
                state["verified"] = True
                state["user_id"] = user.get("id")
                state["name"] = user.get("name", "there")
                state["step"] = "done"
                customer_info[call_sid] = state
                greeting = f"Hey {state['name']}, thank you for calling in today. How can we help you?"
                return str(build_gather(greeting, "/process-speech"))
            else:
                state["retry"] += 1
                if state["retry"] >= 2:
                    state["step"] = "collect_name"
                    response_text = "We couldn't find your account. Please say your first and last name."
                else:
                    response_text = "I couldn't find that phone number. Please say your 10-digit mobile app phone number again."
        else:
            response_text = "That didn't sound like a 10-digit phone number. Please say it again."

        customer_info[call_sid] = state
        return str(build_gather(response_text, "/collect-info"))

    elif state["step"] == "collect_name":
        state["name"] = speech
        state["step"] = "collect_manual_phone"
        response_text = "Thank you. Please say your 10-digit phone number."
        customer_info[call_sid] = state
        return str(build_gather(response_text, "/collect-info"))

    elif state["step"] == "collect_manual_phone":
        new_digits = re.sub(r"\D", "", speech)
        if len(new_digits) == 10:
            state["phone"] = new_digits
            state["step"] = "done"
            customer_info[call_sid] = state
            return str(build_gather("Thank you. How can I help you today?", "/process-speech"))
        else:
            response_text = "That didn't sound like a 10-digit phone number. Please say it again."
            customer_info[call_sid] = state
            return str(build_gather(response_text, "/collect-info"))

    customer_info[call_sid] = state
    return str(build_gather("I'm sorry, I didn't catch that. Could you please repeat?", "/collect-info"))

@speech_bp.route("/process-speech", methods=["POST"])
def process_speech():
    call_sid = request.form.get("CallSid")
    speech = request.form.get("SpeechResult", "").strip()

    # Retrieve session state
    history = session_memory.get(call_sid, [])
    info = customer_info.get(call_sid, {})

    # Add user input to history
    history.append({"role": "user", "content": speech})

    # Determine intent
    text = normalize_text(speech)
    offer_detected = parse_offer(text, retention_offers)

    # Check if it's a cancellation request
    if any(keyword in text for keyword in cancel_keywords):
        reply = "I'm sorry to hear you'd like to cancel. Can you share why you're thinking about it?"
        history.append({"role": "assistant", "content": reply})
        session_memory[call_sid] = history
        return str(build_gather(reply, "/process-speech"))

    # Handle retention offer acceptance or decline
    if offer_detected:
        info["offer"] = offer_detected
        if any(phrase in text for phrase in accepted_phrases):
            info["outcome"] = "accepted"
            info["transcript"] = speech
            send_to_zapier(info)
            session_memory[call_sid] = history
            return str(build_hangup(f"Great! We've applied the {offer_detected} to your account. Thank you for staying with us."))
        elif any(phrase in text for phrase in decline_phrases):
            info["outcome"] = "declined"
            info["transcript"] = speech
            send_to_zapier(info)
            session_memory[call_sid] = history
            return str(build_hangup("Understood. We've processed your cancellation. Goodbye."))

    # Use OpenAI for dynamic retention conversation
    ai_response = get_ai_response(history)
    history.append({"role": "assistant", "content": ai_response})

    # Update session
    session_memory[call_sid] = history

    return str(build_gather(ai_response, "/process-speech"))
