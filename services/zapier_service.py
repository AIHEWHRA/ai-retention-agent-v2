import requests
import os

def send_to_zapier(data):
    try:
        webhook_url = os.getenv("ZAPIER_WEBHOOK_URL")
        if webhook_url:
            requests.post(webhook_url, json=data)
            print(f"✅ Sent to Zapier: {data}")
    except Exception as e:
        print("❌ Zapier error:", e)
