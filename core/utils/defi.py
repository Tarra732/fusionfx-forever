# defi.py

import requests
import time
from decimal import Decimal
from utils.alerts import send_telegram_alert

DEFI_PROTOCOLS = [
    {"name": "AAVE", "chain": "ETH", "min_apy": 3.5},
    {"name": "EigenLayer", "chain": "ETH", "min_apy": 5.0},
    {"name": "Pendle", "chain": "ARBI", "min_apy": 7.2}
]

def check_defi_opportunities(usdc_balance: float):
    eligible = []
    for protocol in DEFI_PROTOCOLS:
        apy = fetch_protocol_apy(protocol["name"])
        if apy and apy >= protocol["min_apy"]:
            eligible.append({
                "protocol": protocol["name"],
                "chain": protocol["chain"],
                "apy": apy
            })
    return eligible if usdc_balance >= 10000 else []


def fetch_protocol_apy(protocol: str) -> float:
    try:
        if protocol == "AAVE":
            res = requests.get("https://api.llama.fi/protocol/aave")
            return float(res.json()["apy"])  # Placeholder structure
        elif protocol == "EigenLayer":
            return 5.2  # Placeholder static APY
        elif protocol == "Pendle":
            return 7.8  # Simulated APY feed
    except Exception as e:
        send_telegram_alert(f"⚠️ Failed to fetch APY for {protocol}: {str(e)}")
    return 0.0


def auto_compound_trigger(usdc_balance: float):
    if usdc_balance > 10000:
        eligible = check_defi_opportunities(usdc_balance)
        if eligible:
            selected = max(eligible, key=lambda x: x["apy"])
            send_telegram_alert(f"🔁 Auto-compounding {usdc_balance} USDC into {selected['protocol']} on {selected['chain']} at {selected['apy']}% APY")
            return selected
    return None


def simulate_yield_allocation(protocol: str, principal: float, days: int) -> float:
    apy = fetch_protocol_apy(protocol)
    rate = Decimal(apy) / Decimal(100)
    return float(principal * ((1 + rate / 365) ** days))