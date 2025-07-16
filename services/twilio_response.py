
from twilio.twiml.voice_response import VoiceResponse, Gather

def build_gather(prompt_text, action):
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=action,
        method="POST",
        timeout=7,
        speech_timeout="5"  # FIX: Allows 5 seconds pause for phone numbers
    )
    gather.say(prompt_text, voice="Polly.Raveena", language="en-US")
    response.append(gather)
    response.redirect("/no-input")
    return response

def build_hangup(message):
    response = VoiceResponse()
    response.say(message, voice="Polly.Raveena", language="en-US")
    response.hangup()
    return response
