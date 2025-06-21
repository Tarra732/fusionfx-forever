import time
import logging
from decimal import Decimal
from exchanges import Binance, Kraken, Coinbase
from utils.crypto import encrypt_and_store, get_current_balance
from alerts import notify_telegram, notify_sms

class ProfitManager:
    def __init__(self, cold_wallets, min_sweep=10000):
        self.cold_wallets = cold_wallets
        self.min_sweep = Decimal(min_sweep)

    def check_and_withdraw(self):
        balance = get_current_balance("USDC")
        if balance < self.min_sweep:
            logging.info(f"[ProfitManager] Balance {balance} below sweep threshold")
            return

        for exchange_class in [Binance, Kraken, Coinbase]:
            try:
                exchange = exchange_class()
                logging.info(f"[ProfitManager] Attempting withdrawal via {exchange.name}")
                tx = exchange.withdraw(balance, self.cold_wallets[exchange.name.lower()])
                self.log_attestation(exchange.name, balance, tx)
                notify_telegram(f"✅ Profit of ${balance} withdrawn via {exchange.name}")
                return
            except Exception as e:
                logging.warning(f"[ProfitManager] {exchange.name} withdrawal failed: {e}")
                continue

        # Fallback: Secure the funds and alert
        encrypt_and_store("USDC", balance)
        notify_sms("🚨 All exchange withdrawals failed. Manual action needed.")
        notify_telegram("⚠️ Manual profit retrieval required.")

    def log_attestation(self, exchange, amount, tx_hash):
        with open("logs/profit_attestations.log", "a") as f:
            f.write(f"{time.time()} | {exchange} | ${amount} | TX: {tx_hash}\n")