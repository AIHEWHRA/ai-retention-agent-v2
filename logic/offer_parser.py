retention_offers = ["free month", "downgrade", "pause", "credits"]
accepted_phrases = ["yes", "sounds good", "let’s do it", "i'll take it", "sure", "okay"]

def parse_offer(user_input, memory):
    accepted = any(p in user_input.lower() for p in accepted_phrases)
    prior = memory[-2]["content"].lower() if len(memory) >= 2 else ""
    offered = any(o in prior for o in retention_offers)
    offer_used = next((o for o in retention_offers if o in prior), "unknown")

    if accepted and offered:
        return "accepted", offer_used, f"User accepted offer: {offer_used}"
    elif "cancel" in user_input.lower():
        return "declined", offer_used, user_input
    return None, None, None
