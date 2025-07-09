from flask import Flask
from routes.webhook_routes import webhook_bp
from routes.speech_routes import speech_bp

app = Flask(__name__)
app.register_blueprint(webhook_bp)
app.register_blueprint(speech_bp)
