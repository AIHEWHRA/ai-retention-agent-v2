from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from models.session_store import session_memory, customer_info
from services.logger import log_conversation
from logic.offer_parser import parse_offer
from openai import OpenAI
import os
import json

webhook_bp = Blueprint('webhook_bp', __name__)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@webhook_bp.route("/")
def home():
    return "AI Retention Agent is running."

@webhook_bp.route("/twilio-webhook", methods=["POST"])
def twilio_webhook():
    call_sid = request.form.get("CallSid")
    session_memory[call_sid] = []
    customer_info[call_sid] = {"step": "name", "retry": 0}

    prompt = "Hello, thank you for calling Hurricane Express Wash. To better serve you today, please provide your first and last name."
    return str(build_gather(prompt, "/collect-info"))

@webhook_bp.route("/collect-info", methods=["POST"])
def collect_info():
    call_sid = request.form.get("CallSid")
    user_input = request.form.get("SpeechResult") or ""

    # Save the user input in memory
    session_memory.setdefault(call_sid, []).append({"role": "user", "content": user_input})

    # Load your SOP prompt from /prompts/
    with open("prompts/retention_sop.md") as f:
        sop = f.read()

    # Build the full conversation so far
    messages = [{"role": "system", "content": sop}] + session_memory[call_sid]

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    bot_reply = response.choices[0].message.content

    # Save the bot reply to session
    session_memory[call_sid].append({"role": "assistant", "content": bot_reply})

    # Use your parser to figure out what to do
    status, offer_used, explanation = parse_offer(user_input, session_memory[call_sid])

    retention_offer_made = True if offer_used != "unknown" else False
    customer_decision = status if status else "unknown"
    final_action = "retained" if status == "accepted" else ("cancelled" if status == "declined" else "unknown")

    # Log to Postgres
    log_conversation(
        customer_input=user_input,
        ai_response=bot_reply,
        retention_offer_made=retention_offer_made,
        customer_decision=customer_decision,
        final_action=final_action,
        full_messages=json.dumps(messages)
    )

    # If declined → hang up politely
    if status == "declined":
        return str(build_hangup("Your membership has been cancelled as requested. Thank you for being with Hurricane Express Wash."))

    # Otherwise → ask next question / confirm
    return str(build_gather(bot_reply, "/collect-info"))

@webhook_bp.route("/no-input", methods=["POST"])
def no_input():
    return str(build_hangup("It seems we might be having trouble hearing you. Please call back later. Goodbye."))


    # ✅ Parse what happened
    status, offer_used, explanation = parse_offer(user_input, session_memory[call_sid])

    retention_offer_made = True if offer_used != "unknown" else False
    customer_decision = status if status else "unknown"
    final_action = "retained" if status == "accepted" else ("cancelled" if status == "declined" else "unknown")

    # ✅ Log everything
    log_conversation(
        customer_input=user_input,
        ai_response=bot_reply,
        retention_offer_made=retention_offer_made,
        customer_decision=customer_decision,
        final_action=final_action,
        full_messages=json.dumps(messages)
    )

    # If customer declined → hang up
    if status == "declined":
        return str(build_hangup("Your plan has been cancelled as requested. Thank you for being with Hurricane Express Wash."))

    # Otherwise, continue the convo
    return str(build_gather(bot_reply, "/collect-info"))

