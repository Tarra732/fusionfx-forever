# agents/yield_rotation_agent.py

import time
import requests
from datetime import datetime
from agents.utils.logger import log_event
from utils.alerts import send_system_alert

class YieldRotationAgent:
    """Companion agent to monitor multi-chain DeFi yields and rotate funds accordingly."""

    def __init__(self):
        self.last_checked = None
        self.rotation_interval = 3600  # Every hour
        self.yield_sources = [
            {
                "name": "Aave v3 Polygon",
                "api": "https://api.llama.fi/yields",
                "filter": lambda p: p["project"] == "aave" and p["chain"] == "Polygon",
                "cap": 0.25
            },
            {
                "name": "Yearn v3 Ethereum",
                "api": "https://api.llama.fi/yields",
                "filter": lambda p: p["project"] == "yearn" and p["chain"] == "Ethereum",
                "cap": 0.25
            },
            {
                "name": "Beefy BNB",
                "api": "https://api.llama.fi/yields",
                "filter": lambda p: p["project"] == "beefy" and p["chain"] == "BNB Chain",
                "cap": 0.25
            }
        ]

    def fetch_yields(self):
        """Fetch yield data and filter for supported protocols"""
        try:
            result = []
            for source in self.yield_sources:
                res = requests.get(source["api"]).json()
                matches = list(filter(source["filter"], res.get("data", [])))
                for match in matches:
                    match["source"] = source["name"]
                    match["cap"] = source["cap"]
                    result.append(match)
            return result
        except Exception as e:
            log_event("yield_rotation_error", {"error": str(e)})
            return []

    def decide_rotation(self, yield_data):
        """Choose best yield sources under risk constraints"""
        top_yields = sorted(yield_data, key=lambda x: x.get("apy", 0), reverse=True)
        portfolio_allocation = {}
        total_allocated = 0

        for y in top_yields:
            alloc = min(y["cap"], 1 - total_allocated)
            if alloc <= 0:
                break
            portfolio_allocation[y["source"]] = {
                "apy": y.get("apy", 0),
                "allocation": alloc
            }
            total_allocated += alloc

        return portfolio_allocation

    def rotate_funds(self, allocation_plan):
        """Execute fund movement based on allocation plan (simulated here)"""
        for source, details in allocation_plan.items():
            log_event("rotate_funds", {
                "destination": source,
                "apy": details["apy"],
                "allocation": details["allocation"]
            })
        send_system_alert(f"✅ Yield rotation complete at {datetime.utcnow().isoformat()}")

    def run(self):
        """Run loop to periodically rebalance yield farming allocations"""
        while True:
            try:
                now = time.time()
                if not self.last_checked or now - self.last_checked > self.rotation_interval:
                    yield_data = self.fetch_yields()
                    if yield_data:
                        plan = self.decide_rotation(yield_data)
                        self.rotate_funds(plan)
                        self.last_checked = now
                    else:
                        log_event("yield_rotation_no_data", {})
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                log_event("yield_rotation_loop_error", {"error": str(e)})
                time.sleep(60)

if __name__ == "__main__":
    agent = YieldRotationAgent()
    agent.run()