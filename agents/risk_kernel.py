# agents/risk_kernel.py

import requests

class RiskKernel:
    def __init__(self, base_risk=0.1, vix_penalty_curve=None):
        self.base_risk = base_risk
        self.vix_penalty_curve = vix_penalty_curve or [
            {"threshold": 30, "multiplier": 0.8},
            {"threshold": 40, "multiplier": 0.5}
        ]

    def fetch_vix(self):
        try:
            response = requests.get("https://www.alphavantage.co/query", params={
                "function": "VOLATILITY_INDEX",
                "symbol": "VIX",
                "apikey": "demo"  # Replace with your actual Alpha Vantage key
            })
            data = response.json()
            vix_value = float(data["VIX"]["value"])
            return vix_value
        except Exception as e:
            print(f"VIX fetch failed: {e}")
            return 20  # Assume a neutral VIX if fetch fails

    def apply_penalty(self, risk, vix):
        for rule in sorted(self.vix_penalty_curve, key=lambda x: x["threshold"]):
            if vix >= rule["threshold"]:
                risk *= rule["multiplier"]
        return risk

    def calculate_position_size(self):
        vix = self.fetch_vix()
        adjusted_risk = self.apply_penalty(self.base_risk, vix)
        return round(adjusted_risk, 4)