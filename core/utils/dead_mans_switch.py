# core/utils/dead_mans_switch.py

import datetime
from utils.alerts import send_sms, send_telegram

class DeadMansSwitch:
    def __init__(self, last_checkin, interval_days=365):
        self.last_checkin = last_checkin
        self.interval_days = interval_days

    def is_expired(self):
        return (datetime.datetime.now() - self.last_checkin).days >= self.interval_days

    def trigger(self):
        if self.is_expired():
            send_sms("🚨 Dead Man's Switch Triggered: DAO fallback initiated")
            send_telegram("⚠️ Bot unresponsive beyond allowed threshold. DAO control activated.")
            return True
        return False