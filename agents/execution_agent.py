# agents/execution_agent.py

import time
import logging
from core.utils.alerts import notify_telegram
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate
from forex_com import ForexComAPI  # Placeholder for fallback broker

class ExecutionAgent:
    def __init__(self, config):
        self.oanda = API(access_token=config["OANDA_API_KEY"])
        self.forex_com = ForexComAPI(config["FOREX_COM_API_KEY"])
        self.requote_tolerance = config.get("requote_tolerance", 1.2)
        self.max_retries = config.get("max_retries", 3)
        self.fallback_latency = config.get("fallback_latency", 300)  # ms
        self.live_account = config.get("live_account", False)

    def execute_order(self, pair, units, direction, price):
        order = {
            "order": {
                "instrument": pair,
                "units": str(units if direction == "buy" else -units),
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }

        try:
            start = time.time()
            r = OrderCreate(accountID=self.get_account_id(), data=order)
            self.oanda.request(r)
            latency = (time.time() - start) * 1000  # ms

            if latency > self.fallback_latency:
                logging.warning(f"High latency ({latency}ms). Attempting fallback to Forex.com.")
                return self._fallback_order(pair, units, direction)

            logging.info(f"Trade executed: {direction} {pair} ({units}) via OANDA")
            notify_telegram(f"✅ Executed {direction.upper()} {pair} ({units})")

        except Exception as e:
            logging.error(f"OANDA execution failed: {e}")
            return self._fallback_order(pair, units, direction)

    def _fallback_order(self, pair, units, direction):
        try:
            result = self.forex_com.place_order(pair, units, direction)
            logging.info(f"Trade executed via Forex.com fallback: {result}")
            notify_telegram(f"🔄 Fallback trade executed on Forex.com: {direction} {pair}")
        except Exception as e:
            logging.critical(f"⚠️ Fallback execution failed: {e}")
            notify_telegram(f"❌ All trade routes failed: {direction} {pair}")
            return None

    def get_account_id(self):
        # Replace with dynamic lookup or config file reference
        return "YOUR_OANDA_ACCOUNT_ID"