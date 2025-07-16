# File: services/openai_service.py

from openai import OpenAI
import os
import json
import time

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

def get_structured_ai_response(history):
    try:
        # Create a new thread for the conversation
        thread = client.beta.threads.create()

        # Add conversation messages
        for message in history:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role=message["role"],
                content=message["content"]
            )

        # Run the Assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Poll until complete
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Get the latest assistant message
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        for message in reversed(messages.data):
            if message.role == "assistant":
                # Expect raw JSON output from assistant
                raw_text = message.content[0].text.value.strip()
                try:
                    return json.loads(raw_text)
                except json.JSONDecodeError:
                    print("❌ JSON parsing error:", raw_text)
                    # Fallback structure
                    return {
                        "reply": raw_text,
                        "offer": "unknown",
                        "outcome": "unknown",
                        "transcript": "\n".join([m['content'] for m in history if m['role'] == 'user'])
                    }

        return {
            "reply": "I'm sorry, I didn't catch that. Could you repeat?",
            "offer": "unknown",
            "outcome": "unknown",
            "transcript": "\n".join([m['content'] for m in history if m['role'] == 'user'])
        }

    except Exception as e:
        print("❌ Assistant API error:", e)
        return {
            "reply": "I'm sorry, there was a system issue. Please try again later.",
            "offer": "unknown",
            "outcome": "unknown",
            "transcript": "\n".join([m['content'] for m in history if m['role'] == 'user'])
        }

