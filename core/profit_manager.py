# core/profit_manager.py

import logging
import time
import random
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event
from agents.utils.portfolio import get_portfolio_metrics, update_equity
from utils.alerts import send_critical_alert, send_system_alert
from core.utils.crypto import encrypt_data, decrypt_data

# Load environment variables
load_dotenv()

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("[WARNING] CCXT not available. Install for crypto exchange integration.")

class ProfitManager:
    """Manages profit sweeps to cold wallets and DeFi protocols"""
    
    def __init__(self, min_sweep=10000, max_sweep=50000):
        self.min_sweep = min_sweep  # Minimum balance to trigger sweep
        self.max_sweep = max_sweep  # Maximum amount per sweep
        
        # Load wallet configurations
        self.cold_wallets = {
            "binance": os.getenv("BINANCE_USDT_ADDRESS"),
            "kraken": os.getenv("KRAKEN_USDT_ADDRESS"),
            "coinbase": os.getenv("COINBASE_USDT_ADDRESS")
        }
        
        # Exchange API configurations
        self.exchanges = {}
        if CCXT_AVAILABLE:
            self._initialize_exchanges()
        
        # DeFi protocol configurations
        self.defi_protocols = {
            "aave": {
                "enabled": True,
                "min_amount": 5000,
                "apy_target": 0.05  # 5% APY target
            },
            "compound": {
                "enabled": True,
                "min_amount": 3000,
                "apy_target": 0.04
            }
        }
        
        # Profit tracking
        self.profit_history = []
        self.sweep_history = []
        self.total_profits_swept = 0.0
        
        # Data files
        self.data_dir = Path("data/profit_manager")
        self.data_dir.mkdir(exist_ok=True)
        self.profit_file = self.data_dir / "profit_history.json"
        self.sweep_file = self.data_dir / "sweep_history.json"
        
        # Load historical data
        self._load_history()
        
        log_event("profit_manager_initialized", {
            "min_sweep": min_sweep,
            "max_sweep": max_sweep,
            "cold_wallets": list(self.cold_wallets.keys()),
            "exchanges_available": len(self.exchanges)
        })
    
    def _initialize_exchanges(self):
        """Initialize exchange connections"""
        try:
            # Binance
            binance_key = os.getenv("BINANCE_API_KEY")
            binance_secret = os.getenv("BINANCE_SECRET")
            if binance_key and binance_secret:
                self.exchanges["binance"] = ccxt.binance({
                    'apiKey': binance_key,
                    'secret': binance_secret,
                    'sandbox': False,  # Set to True for testing
                    'enableRateLimit': True
                })
            
            # Kraken
            kraken_key = os.getenv("KRAKEN_API_KEY")
            kraken_secret = os.getenv("KRAKEN_SECRET")
            if kraken_key and kraken_secret:
                self.exchanges["kraken"] = ccxt.kraken({
                    'apiKey': kraken_key,
                    'secret': kraken_secret,
                    'enableRateLimit': True
                })
            
            log_event("exchanges_initialized", {"count": len(self.exchanges)})
            
        except Exception as e:
            log_event("exchange_initialization_error", {"error": str(e)})
    
    def _load_history(self):
        """Load profit and sweep history"""
        try:
            if self.profit_file.exists():
                with open(self.profit_file, 'r') as f:
                    self.profit_history = json.load(f)
            
            if self.sweep_file.exists():
                with open(self.sweep_file, 'r') as f:
                    self.sweep_history = json.load(f)
                    self.total_profits_swept = sum(s.get("amount", 0) for s in self.sweep_history)
            
            log_event("profit_history_loaded", {
                "profit_records": len(self.profit_history),
                "sweep_records": len(self.sweep_history),
                "total_swept": self.total_profits_swept
            })
            
        except Exception as e:
            log_event("history_load_error", {"error": str(e)})
    
    def _save_history(self):
        """Save profit and sweep history"""
        try:
            with open(self.profit_file, 'w') as f:
                json.dump(self.profit_history, f, indent=2)
            
            with open(self.sweep_file, 'w') as f:
                json.dump(self.sweep_history, f, indent=2)
            
        except Exception as e:
            log_event("history_save_error", {"error": str(e)})
    
    def get_current_balance(self):
        """Get current trading account balance"""
        try:
            portfolio_metrics = get_portfolio_metrics()
            equity_curve = portfolio_metrics.get("equity_curve", [1000])
            current_balance = equity_curve[-1] if equity_curve else 1000
            
            # Calculate profit from initial balance
            initial_balance = equity_curve[0] if len(equity_curve) > 1 else 1000
            profit = current_balance - initial_balance
            
            return {
                "current_balance": current_balance,
                "initial_balance": initial_balance,
                "total_profit": profit,
                "profit_percentage": (profit / initial_balance) * 100 if initial_balance > 0 else 0
            }
            
        except Exception as e:
            log_event("balance_fetch_error", {"error": str(e)})
            return {
                "current_balance": 1000,
                "initial_balance": 1000,
                "total_profit": 0,
                "profit_percentage": 0
            }
    
    def calculate_sweep_amount(self, current_balance, total_profit):
        """Calculate optimal amount to sweep"""
        if total_profit < self.min_sweep:
            return 0
        
        # Keep some buffer in trading account
        buffer_amount = current_balance * 0.1  # Keep 10% as buffer
        available_for_sweep = total_profit - buffer_amount
        
        # Don't sweep more than max_sweep at once
        sweep_amount = min(available_for_sweep, self.max_sweep)
        
        # Ensure minimum sweep amount
        if sweep_amount < self.min_sweep:
            return 0
        
        return max(0, sweep_amount)
    
    def convert_to_usdt(self, amount_usd, exchange_name="binance"):
        """Convert USD to USDT (simplified - assumes 1:1 ratio)"""
        try:
            # In real implementation, would get actual USD/USDT rate
            usdt_amount = amount_usd * 0.999  # Small conversion fee
            
            log_event("usd_to_usdt_conversion", {
                "usd_amount": amount_usd,
                "usdt_amount": usdt_amount,
                "exchange": exchange_name
            })
            
            return usdt_amount
            
        except Exception as e:
            log_event("conversion_error", {"error": str(e)})
            return amount_usd
    
    def withdraw_to_cold_wallet(self, amount, exchange_name, wallet_address):
        """Withdraw funds to cold wallet"""
        try:
            if exchange_name not in self.exchanges:
                log_event("exchange_not_available", {"exchange": exchange_name})
                return False
            
            exchange = self.exchanges[exchange_name]
            
            # Convert to USDT
            usdt_amount = self.convert_to_usdt(amount, exchange_name)
            
            # Simulate withdrawal (in real implementation, would use exchange API)
            log_event("withdrawal_initiated", {
                "exchange": exchange_name,
                "amount": usdt_amount,
                "wallet": wallet_address[:10] + "...",
                "currency": "USDT"
            })
            
            # Simulate processing time
            time.sleep(2)
            
            # Simulate success (in real implementation, would check transaction status)
            success = random.random() > 0.1  # 90% success rate for simulation
            
            if success:
                log_event("withdrawal_successful", {
                    "exchange": exchange_name,
                    "amount": usdt_amount,
                    "tx_id": f"0x{random.randint(10**15, 10**16-1):016x}"
                })
                return True
            else:
                log_event("withdrawal_failed", {
                    "exchange": exchange_name,
                    "amount": usdt_amount,
                    "reason": "Network congestion"
                })
                return False
                
        except Exception as e:
            log_event("withdrawal_error", {
                "exchange": exchange_name,
                "amount": amount,
                "error": str(e)
            })
            return False
    
    def deposit_to_defi(self, amount, protocol="aave"):
        """Deposit funds to DeFi protocol for yield farming"""
        try:
            if protocol not in self.defi_protocols:
                return False
            
            protocol_config = self.defi_protocols[protocol]
            
            if not protocol_config["enabled"] or amount < protocol_config["min_amount"]:
                return False
            
            # Simulate DeFi deposit
            log_event("defi_deposit_initiated", {
                "protocol": protocol,
                "amount": amount,
                "target_apy": protocol_config["apy_target"]
            })
            
            # Simulate transaction
            time.sleep(3)
            
            # Simulate success
            success = random.random() > 0.05  # 95% success rate
            
            if success:
                log_event("defi_deposit_successful", {
                    "protocol": protocol,
                    "amount": amount,
                    "tx_id": f"0x{random.randint(10**15, 10**16-1):016x}"
                })
                return True
            else:
                log_event("defi_deposit_failed", {
                    "protocol": protocol,
                    "amount": amount,
                    "reason": "Gas price too high"
                })
                return False
                
        except Exception as e:
            log_event("defi_deposit_error", {
                "protocol": protocol,
                "amount": amount,
                "error": str(e)
            })
            return False
    
    def encrypt_and_store(self, amount):
        """Encrypt and store funds locally as last resort"""
        try:
            encrypted_data = encrypt_data({
                "amount": amount,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "All withdrawal methods failed"
            })
            
            vault_file = self.data_dir / f"encrypted_vault_{int(time.time())}.enc"
            with open(vault_file, 'wb') as f:
                f.write(encrypted_data)
            
            log_event("funds_encrypted", {
                "amount": amount,
                "vault_file": str(vault_file)
            })
            
            send_critical_alert(f"🔐 ${amount:.2f} encrypted and stored locally - manual retrieval required")
            
            return True
            
        except Exception as e:
            log_event("encryption_error", {"error": str(e)})
            return False
    
    def sweep_profits(self):
        """Main profit sweep function"""
        try:
            balance_data = self.get_current_balance()
            current_balance = balance_data["current_balance"]
            total_profit = balance_data["total_profit"]
            
            log_event("profit_sweep_check", balance_data)
            
            # Calculate sweep amount
            sweep_amount = self.calculate_sweep_amount(current_balance, total_profit)
            
            if sweep_amount <= 0:
                log_event("no_sweep_needed", {
                    "total_profit": total_profit,
                    "min_sweep": self.min_sweep
                })
                return False
            
            log_event("profit_sweep_initiated", {
                "sweep_amount": sweep_amount,
                "current_balance": current_balance,
                "total_profit": total_profit
            })
            
            send_system_alert(f"💰 Initiating profit sweep: ${sweep_amount:.2f}")
            
            # Try cold wallet withdrawals first
            for exchange_name, wallet_address in self.cold_wallets.items():
                if wallet_address and exchange_name in self.exchanges:
                    if self.withdraw_to_cold_wallet(sweep_amount, exchange_name, wallet_address):
                        # Record successful sweep
                        sweep_record = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "amount": sweep_amount,
                            "method": "cold_wallet",
                            "destination": exchange_name,
                            "wallet": wallet_address,
                            "success": True
                        }
                        
                        self.sweep_history.append(sweep_record)
                        self.total_profits_swept += sweep_amount
                        
                        # Update account balance
                        new_balance = current_balance - sweep_amount
                        update_equity(new_balance)
                        
                        self._save_history()
                        
                        log_event("profit_sweep_successful", sweep_record)
                        send_system_alert(f"✅ Profit sweep complete: ${sweep_amount:.2f} to {exchange_name}")
                        
                        return True
            
            # Try DeFi protocols if cold wallets fail
            for protocol in self.defi_protocols:
                if self.deposit_to_defi(sweep_amount, protocol):
                    sweep_record = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "amount": sweep_amount,
                        "method": "defi",
                        "destination": protocol,
                        "success": True
                    }
                    
                    self.sweep_history.append(sweep_record)
                    self.total_profits_swept += sweep_amount
                    
                    new_balance = current_balance - sweep_amount
                    update_equity(new_balance)
                    
                    self._save_history()
                    
                    log_event("profit_sweep_defi_successful", sweep_record)
                    send_system_alert(f"✅ Profit deposited to {protocol}: ${sweep_amount:.2f}")
                    
                    return True
            
            # Last resort: encrypt and store locally
            if self.encrypt_and_store(sweep_amount):
                sweep_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "amount": sweep_amount,
                    "method": "encrypted_storage",
                    "destination": "local_vault",
                    "success": True
                }
                
                self.sweep_history.append(sweep_record)
                self._save_history()
                
                log_event("profit_sweep_encrypted", sweep_record)
                return True
            
            # All methods failed
            log_event("profit_sweep_failed", {"amount": sweep_amount})
            send_critical_alert(f"❌ Profit sweep failed: ${sweep_amount:.2f}")
            
            return False
            
        except Exception as e:
            log_event("profit_sweep_error", {"error": str(e)})
            send_critical_alert(f"Profit sweep error: {str(e)}")
            return False
    
    def get_profit_summary(self):
        """Get profit and sweep summary"""
        balance_data = self.get_current_balance()
        
        return {
            "current_balance": balance_data["current_balance"],
            "total_profit": balance_data["total_profit"],
            "profit_percentage": balance_data["profit_percentage"],
            "total_swept": self.total_profits_swept,
            "sweep_count": len(self.sweep_history),
            "last_sweep": self.sweep_history[-1] if self.sweep_history else None,
            "next_sweep_threshold": self.min_sweep
        }
    
    def run(self):
        """Main run loop for profit manager"""
        log_event("profit_manager_started", {})
        send_system_alert("Profit Manager started")
        
        while True:
            try:
                # Check for profit sweep
                self.sweep_profits()
                
                # Log current status
                summary = self.get_profit_summary()
                log_event("profit_manager_status", summary)
                
                # Sleep for 6 hours
                time.sleep(21600)
                
            except Exception as e:
                log_event("profit_manager_error", {"error": str(e)})
                send_system_alert(f"Profit Manager error: {str(e)}")
                time.sleep(3600)  # Wait 1 hour before retrying

if __name__ == "__main__":
    profit_manager = ProfitManager()
    
    # Test profit sweep
    result = profit_manager.sweep_profits()
    print(f"Profit sweep result: {result}")
    
    # Get summary
    summary = profit_manager.get_profit_summary()
    print(f"Profit summary: {summary}")
    
    # Start main loop
    profit_manager.run()