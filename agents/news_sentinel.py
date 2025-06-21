# agents/news_sentinel.py

import datetime
import requests
from utils.alerts import send_alert
from core.utils.trading_halt import TradingHaltManager

class NewsSentinel:
    def __init__(self, blackout_rules):
        self.blackout_rules = blackout_rules
        self.trading_halt = TradingHaltManager()

    def fetch_news_events(self):
        try:
            response = requests.get("https://api.forexfactory.com/calendar/today")
            return response.json()  # Assume the API returns JSON news events
        except Exception as e:
            send_alert(f"🛑 Failed to fetch news events: {str(e)}")
            return []

    def evaluate_news(self, news_event):
        title = news_event.get("title", "").lower()
        time_str = news_event.get("time")
        if not time_str:
            return False

        event_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.datetime.utcnow()

        for keyword, blackout in self.blackout_rules.items():
            if keyword.lower() in title:
                pre_hours = blackout.get("pre", 0)
                post_hours = blackout.get("post", 0)
                pre_window = event_time - datetime.timedelta(hours=pre_hours)
                post_window = event_time + datetime.timedelta(hours=post_hours)

                if pre_window <= now <= post_window:
                    return True
        return False

    def run(self):
        news_events = self.fetch_news_events()
        for event in news_events:
            if self.evaluate_news(event):
                self.trading_halt.activate(reason=event.get("title", "Unknown Event"))
                send_alert(f"⚠️ Trading halted due to event: {event.get('title')}")
                return

        self.trading_halt.deactivate_if_clear()
        print("[NewsSentinel] No blackout events detected.")

if __name__ == "__main__":
    blackout_rules = {
        "NFP": {"pre": 4, "post": 3},
        "terror": {"pre": 0, "post": 48}
    }
    sentinel = NewsSentinel(blackout_rules)
    sentinel.run()