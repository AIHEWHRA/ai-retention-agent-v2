from flask import Blueprint, request, redirect
from services.twilio_response import build_hangup
from models.session_store import session_memory, customer_info

webhook_bp = Blueprint('webhook_bp', __name__)

@webhook_bp.route("/")
def home():
    return "AI Retention Agent is running."

@webhook_bp.route("/twilio-webhook", methods=["POST"])
def twilio_webhook():
    # Directly redirect to collect-info without initializing session here
    return redirect("/collect-info")

@webhook_bp.route("/no-input", methods=["POST"])
def no_input():
    return str(build_hangup("It seems we might be having trouble hearing you. Please call back later. Goodbye."))
