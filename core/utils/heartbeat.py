# utils/heartbeat.py

import time
import datetime
from core.utils.alerts import send_telegram

HEARTBEAT_INTERVAL_MINUTES = 60  # Sends an update every hour

def send_heartbeat():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    send_telegram(f"✅ FusionFX Heartbeat: Bot operational at {timestamp}")

def start_heartbeat():
    while True:
        send_heartbeat()
        time.sleep(HEARTBEAT_INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    start_heartbeat()