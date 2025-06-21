# utils/watchdog.py

import psutil
import time
import threading
from utils.alerts import send_telegram, send_sms

CPU_THRESHOLD = 85
MEMORY_THRESHOLD = 85
LATENCY_THRESHOLD_MS = 300
DRAWDOWN_LIMIT = 0.15

class Watchdog:
    def __init__(self):
        self.latency_check_interval = 10
        self.drawdown = 0.0
        self.current_equity = 10000
        self.peak_equity = 10000

    def check_system_resources(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        if cpu > CPU_THRESHOLD or mem > MEMORY_THRESHOLD:
            send_telegram(f"⚠️ High system usage: CPU {cpu}%, Memory {mem}%")
            if mem > 90:
                send_sms("🚨 Memory exceeds 90% - review VPS performance.")
    
    def update_equity(self, equity):
        self.current_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
        self.drawdown = 1 - (equity / self.peak_equity)
        if self.drawdown >= DRAWDOWN_LIMIT:
            send_telegram(f"❗ Drawdown Alert: {self.drawdown:.2%}")
            if self.drawdown >= 0.20:
                send_sms("🚨 Drawdown >20% - Consider manual review.")

    def check_latency(self, ping_fn):
        try:
            latency = ping_fn()
            if latency > LATENCY_THRESHOLD_MS:
                send_telegram(f"⏱ High latency detected: {latency}ms")
        except Exception as e:
            send_sms(f"⚠️ Latency check failed: {str(e)}")

    def run(self, ping_fn):
        while True:
            self.check_system_resources()
            self.check_latency(ping_fn)
            time.sleep(self.latency_check_interval)