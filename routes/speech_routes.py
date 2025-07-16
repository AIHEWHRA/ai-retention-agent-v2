# File: routes/speech_routes.py

from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from services.openai_service import get_structured_ai_response
from services.zapier_service import send_to_zapier
from models.session_store import session_memory, customer_info
from services.account_service import find_user_by_phone
import re

speech_bp = Blueprint('speech_bp', __name__)

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

    response_data = get_structured_ai_response(history)

    reply = response_data["reply"]
    offer = response_data["offer"]
    outcome = response_data["outcome"]
    transcript = response_data["transcript"]

    session_memory[call_sid] = history

    # Decide if conversation is done
    if outcome in ["accepted", "declined", "cancellation processed"]:
        summary_dict = {
            "offer": offer,
            "outcome": outcome,
            "transcript": transcript
        }
        send_to_zapier(summary_dict)

        return str(build_hangup("Thank you for your time today. Goodbye."))

    else:
        # Continue the conversation
        return str(build_gather(reply, "/process-speech"))
