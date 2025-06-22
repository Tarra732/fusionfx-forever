# agents/fusion_agent.py

from agents.predictor import Predictor
from agents.market_scanner import MarketScanner
from agents.risk_kernel import RiskKernel
from agents.execution_agent import ExecutionAgent
from datetime import datetime, time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.alerts import send_system_alert

class FusionAgent:
    def __init__(self):
        self.predictor = Predictor(
            vix_source="alphavantage",
            features=["london_open_volume", "yield_spread", "usd_index_delta"]
        )
        self.scanner = MarketScanner(
            pairs=["EUR/USD"],
            timeframes=["15M", "4H"],
            adr_threshold=0.0065
        )
        self.risk_kernel = RiskKernel(
            base_risk=0.1,
            vix_penalty_curve=[
                {"threshold": 30, "multiplier": 0.8},
                {"threshold": 40, "multiplier": 0.5}
            ]
        )
        self.executor = ExecutionAgent(
            requote_tolerance=1.2,
            max_retries=3,
            fallback_latency=300
        )
        self.london_boost = {"start": time(7, 45), "end": time(8, 0), "multiplier": 1.8}

    def is_london_open(self, now):
        return self.london_boost["start"] <= now.time() <= self.london_boost["end"]

    def execute(self):
        now = datetime.utcnow()
        scanner_signal = self.scanner.scan()
        predictor_signal = self.predictor.forecast_direction()

        if not scanner_signal or not predictor_signal:
            return

        if scanner_signal["bias"] == predictor_signal["bias"]:
            position_bias = predictor_signal["bias"]
            base_size = self.risk_kernel.calculate_position_size()

            if self.is_london_open(now):
                size = base_size * self.london_boost["multiplier"]
                send_system_alert("🚀 London Boost Applied")
            else:
                size = base_size

            order = {
                "pair": predictor_signal["pair"],
                "direction": "buy" if position_bias else "sell",
                "size": size
            }

            send_system_alert(f"📥 Trade Signal: {order['direction']} {order['pair']} @ size {order['size']:.4f}")
            self.executor.execute_order(order)

if __name__ == "__main__":
    agent = FusionAgent()
    agent.execute()