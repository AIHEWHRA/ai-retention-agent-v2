# File: logic/offer_parser.py

import json
import os

# Load offers from JSON data file
def load_retention_offers():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    offers_file = os.path.join(current_dir, "..", "data", "retention_offers.json")
    with open(offers_file, "r") as f:
        data = json.load(f)
    return data["offers"]

retention_offers = load_retention_offers()

# Phrases that count as acceptance
accepted_phrases = ["yes", "sounds good", "let’s do it", "i'll take it", "sure", "okay", "i accept", "i'll do that", "that works"]

# Phrases that count as decline
decline_phrases = ["no", "cancel", "still want to cancel", "go ahead with cancellation", "just cancel"]


def parse_offer(user_input, memory):
    """
    Determines if the user has accepted or declined an offer.

    Args:
        user_input (str): The latest input from the user.
        memory (list): The conversation history.

    Returns:
        outcome (str or None): 'accepted', 'declined', or None.
        offer_used (str or None): The specific offer mentioned, or 'unknown'.
        transcript (str or None): The relevant transcript snippet.
    """
    user_input_lower = user_input.lower()

    accepted = any(p in user_input_lower for p in accepted_phrases)
    declined = any(p in user_input_lower for p in decline_phrases)

    # Check the previous AI message for any offered retention options
    prior_message = memory[-2]["content"].lower() if len(memory) >= 2 else ""
    offered = None
    for o in retention_offers:
        if o.lower() in prior_message:
            offered = o
            break

    # If the user accepted an offer that was presented
    if accepted and offered:
        return "accepted", offered, f"User accepted offer: {offered}"

    # If the user declined after an offer was presented
    if declined and offered:
        return "declined", offered, user_input

    # If the user said cancel but no offer was made yet, return None to keep conversation going
    return None, None, None
