# AI Retention Agent

This is a modular Flask-based AI Retention Agent that integrates with Twilio, OpenAI, Zapier, and Google Cloud.

## Features
- Collects and stores caller info (name, phone)
- Uses GPT-4o to manage retention conversations
- Sends results to Zapier
- Modular and scalable code structure

## Environment Variables
See `.env.example` for required keys.

## Running the App
```bash
pip install -r requirements.txt
python main.py
```

Deploy easily with Railway or any cloud platform that supports Flask.
