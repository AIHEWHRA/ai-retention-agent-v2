from flask import Blueprint, request
from services.twilio_response import build_gather, build_hangup
from models.session_store import session_memory, customer_info

webhook_bp = Blueprint('webhook_bp', __name__)

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

@webhook_bp.route("/no-input", methods=["POST"])
def no_input():
    return str(build_hangup("It seems we might be having trouble hearing you. Please call back later. Goodbye."))
