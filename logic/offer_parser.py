# File: logic/offer_parser.py

# List of available retention offers
retention_offers = ["free month", "downgrade", "pause", "credits"]

# Phrases that count as acceptance
accepted_phrases = ["yes", "sounds good", "let’s do it", "i'll take it", "sure", "okay"]

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

    # Check if the user accepted an offer
    accepted = any(p in user_input.lower() for p in accepted_phrases)

    # Check the previous AI message for offers
    prior = memory[-2]["content"].lower() if len(memory) >= 2 else ""
    offered = any(o in prior for o in retention_offers)
    offer_used = next((o for o in retention_offers if o in prior), "unknown")

    # If an offer was made and user accepted
    if accepted and offered:
        return "accepted", offer_used, f"User accepted offer: {offer_used}"

    # If user said 'cancel' but no offer was made, DO NOT trigger decline yet
    # Only allow decline if an offer was actually presented
    elif "cancel" in user_input.lower() and offered:
        return "declined", offer_used, user_input

    # No final outcome yet; keep conversation going
    return None, None, None
