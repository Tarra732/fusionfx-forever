# utils/alerts.py

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TO = os.getenv("TWILIO_TO_NUMBER")

def send_telegram(message):
    """Send message via Telegram bot"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM] Config missing. Message: {message}")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(f"[TELEGRAM] Sent: {message}")
            return True
        else:
            print(f"[TELEGRAM ERROR] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False

def send_sms(message):
    """Send SMS via Twilio"""
    if not TWILIO_SID or not TWILIO_TOKEN:
        print(f"[SMS] Config missing. Message: {message}")
        return False
    
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        auth = (TWILIO_SID, TWILIO_TOKEN)
        data = {
            "From": TWILIO_FROM,
            "To": TWILIO_TO,
            "Body": message
        }
        
        response = requests.post(url, auth=auth, data=data, timeout=10)
        if response.status_code == 201:
            print(f"[SMS] Sent: {message}")
            return True
        else:
            print(f"[SMS ERROR] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[SMS ERROR] {e}")
        return False

def send_alert(message, channels=["telegram"]):
    """Send alert via multiple channels"""
    success = True
    
    if "telegram" in channels:
        success &= send_telegram(message)
    
    if "sms" in channels:
        success &= send_sms(message)
    
    return success

def send_critical_alert(message):
    """Send critical alert via all channels"""
    return send_alert(f"🚨 CRITICAL: {message}", channels=["telegram", "sms"])

def send_trade_alert(message):
    """Send trade-related alert"""
    return send_alert(f"💰 TRADE: {message}", channels=["telegram"])

def send_system_alert(message):
    """Send system-related alert"""
    return send_alert(f"⚙️ SYSTEM: {message}", channels=["telegram"])