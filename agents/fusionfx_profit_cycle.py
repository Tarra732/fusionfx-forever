# agents/fusionfx_profit_cycle.py

import time
import requests
from decimal import Decimal
from utils.alerts import send_critical_alert
from utils.crypto import send_to_exchange, invest_in_defi_yield_farm, stake_nft_assets
from utils.defi import get_best_yield_opportunity, compound_profits
from agents.utils.logger import log_event
from dotenv import load_dotenv
import os

load_dotenv()

AUTO_COMPOUND = os.getenv("AUTO_COMPOUND", "true").lower() == "true"
INVEST_THRESHOLD = Decimal(os.getenv("INVEST_THRESHOLD", "200"))  # min profit to reinvest
WITHDRAW_RATIO = Decimal(os.getenv("WITHDRAW_RATIO", "0.7"))  # 70% withdraw, 30% invest
EXCHANGE_WALLET = os.getenv("EXCHANGE_WALLET")
FINAL_WALLET = os.getenv("FINAL_WALLET")

def profit_cycle(total_profit):
    try:
        if total_profit < INVEST_THRESHOLD:
            log_event("profit_cycle_skipped", {"reason": "threshold_not_met", "profit": float(total_profit)})
            return

        withdraw_amount = total_profit * WITHDRAW_RATIO
        invest_amount = total_profit - withdraw_amount

        # Step 1: Withdraw portion to exchange
        send_to_exchange(amount=withdraw_amount, wallet=EXCHANGE_WALLET)
        log_event("profit_withdrawn", {"amount": float(withdraw_amount), "to": EXCHANGE_WALLET})

        if not AUTO_COMPOUND:
            log_event("auto_compound_disabled", {})
            return

        # Step 2: Find best DeFi yield or NFT staking option
        best_option = get_best_yield_opportunity(minimum_amount=invest_amount)

        if best_option["type"] == "nft_staking":
            stake_nft_assets(amount=invest_amount, pool=best_option["pool"])
            log_event("nft_staked", {"amount": float(invest_amount), "pool": best_option["pool"]})

        elif best_option["type"] == "defi_yield":
            invest_in_defi_yield_farm(amount=invest_amount, protocol=best_option["protocol"])
            log_event("yield_farm_invested", {"amount": float(invest_amount), "protocol": best_option["protocol"]})

        # Step 3: Compound profits if available
        compound_profits()
        log_event("profits_compounded", {})

    except Exception as e:
        send_critical_alert(f"[Profit Cycle Error] {str(e)}")
        log_event("profit_cycle_error", {"error": str(e)})

if __name__ == "__main__":
    profit_cycle(total_profit=Decimal("250.00"))  # For test