# File: routes/speech_routes.py

from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from services.openai_service import get_ai_response
from services.zapier_service import send_to_zapier
from models.session_store import session_memory, customer_info
from services.account_service import find_user_by_phone
import re
import json

speech_bp = Blueprint('speech_bp', __name__)

accepted_phrases = ["yes", "sounds good", "let’s do it", "i'll take it", "sure", "okay", "i accept", "i'll do that", "that works"]
decline_phrases = ["no", "cancel", "still want to cancel", "go ahead with cancellation", "just cancel"]

cancel_keywords = ["cancel", "stop membership", "end my membership", "terminate membership"]

def normalize_text(text):
    return text.lower().replace("2", "two").replace("50%", "50 percent")

@speech_bp.route("/collect-info", methods=["POST"])
def collect_info():
    call_sid = request.form.get("CallSid")

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

    history = session_memory.get(call_sid, [])
    info = customer_info.get(call_sid, {})

    history.append({"role": "user", "content": speech})

    ai_response = get_ai_response(history)
    history.append({"role": "assistant", "content": ai_response})

    # Summarize for Zapier in a new thread
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    summary_prompt = [{
        "role": "user",
        "content": "Please summarize the following conversation as JSON with keys: offer, outcome, transcript. Only respond with valid JSON, no extra text.\n\n" + conversation_text
    }]

    summary_response = get_ai_response(summary_prompt)

    try:
        summary_dict = json.loads(summary_response)
        send_to_zapier(summary_dict)
    except Exception as e:
        print("❌ JSON parsing error:", e)
        print("Raw summary response:", summary_response)

        fallback_summary = {
            "offer": "unknown",
            "outcome": "unknown",
            "transcript": conversation_text
        }
        send_to_zapier(fallback_summary)

    session_memory[call_sid] = history

    return str(build_gather(ai_response, "/process-speech"))
