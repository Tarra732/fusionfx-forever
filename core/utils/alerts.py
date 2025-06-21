# core/utils/alerts.py

import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Config missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")

def send_sms(message):
    if not TWILIO_SID or not TWILIO_TOKEN:
        print("[SMS] Config missing.")
        return
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        auth = (TWILIO_SID, TWILIO_TOKEN)
        data = {
            "From": TWILIO_FROM,
            "To": TWILIO_TO,
            "Body": message
        }
        requests.post(url, auth=auth, data=data)
    except Exception as e:
        print(f"[SMS ERROR] {e}")