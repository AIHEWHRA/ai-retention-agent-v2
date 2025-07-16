# File: services/openai_service.py

from openai import OpenAI
import os
import time

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

def get_ai_response(history):
    try:
        # Create a new thread for the conversation
        thread = client.beta.threads.create()

        # Add messages to the thread
        for message in history:
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role=message["role"],
                content=message["content"]
            )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Wait for the run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Get the assistant's latest message
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        for message in reversed(messages.data):
            if message.role == "assistant":
                return message.content[0].text.value.strip()

        return "I'm sorry, I don't have an answer for that."

    except Exception as e:
        print("❌ Assistant API error:", e)
        return "Sorry, I’m having trouble responding right now. Please try again later."
