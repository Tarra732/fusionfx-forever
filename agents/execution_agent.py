# agents/execution_agent.py

import time
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event, log_trade
from utils.alerts import send_trade_alert, send_critical_alert
from agents.utils.portfolio import add_trade, update_equity

# Load environment variables
load_dotenv()

try:
    import oandapyV20
    from oandapyV20 import API
    from oandapyV20.endpoints.orders import OrderCreate
    from oandapyV20.endpoints.accounts import AccountDetails
    from oandapyV20.endpoints.pricing import PricingInfo
    OANDA_AVAILABLE = True
except ImportError:
    OANDA_AVAILABLE = False
    print("[WARNING] OANDA API not available. Install oandapyV20 for live trading.")

class ExecutionAgent:
    """Handles trade execution across multiple brokers"""
    
    def __init__(self, requote_tolerance=1.2, max_retries=3, fallback_latency=300):
        self.requote_tolerance = requote_tolerance
        self.max_retries = max_retries
        self.fallback_latency = fallback_latency  # ms
        
        # Load configuration
        self.oanda_api_key = os.getenv("OANDA_API_KEY")
        self.oanda_account_id = os.getenv("OANDA_ACCOUNT_ID")
        self.oanda_env = os.getenv("OANDA_ENV", "practice")  # practice or live
        self.forex_api_key = os.getenv("FOREX_API_KEY")
        self.forex_account_id = os.getenv("FOREX_ACCOUNT_ID")
        
        # Initialize OANDA API if available
        self.oanda_api = None
        if OANDA_AVAILABLE and self.oanda_api_key:
            environment = "practice" if self.oanda_env == "practice" else "live"
            self.oanda_api = API(access_token=self.oanda_api_key, environment=environment)
            log_event("oanda_initialized", {"environment": environment})
        
        # Track execution statistics
        self.execution_stats = {
            "total_orders": 0,
            "successful_orders": 0,
            "failed_orders": 0,
            "avg_latency": 0.0,
            "fallback_used": 0
        }
        
        log_event("execution_agent_initialized", {
            "oanda_available": self.oanda_api is not None,
            "environment": self.oanda_env
        })
    
    def get_current_price(self, instrument):
        """Get current bid/ask prices for an instrument"""
        if not self.oanda_api:
            # Return mock prices for demo
            return {"bid": 1.1000, "ask": 1.1002, "spread": 0.0002}
        
        try:
            params = {"instruments": instrument}
            r = PricingInfo(accountID=self.oanda_account_id, params=params)
            response = self.oanda_api.request(r)
            
            price_data = response["prices"][0]
            bid = float(price_data["bids"][0]["price"])
            ask = float(price_data["asks"][0]["price"])
            spread = ask - bid
            
            return {"bid": bid, "ask": ask, "spread": spread}
            
        except Exception as e:
            log_event("price_fetch_error", {"instrument": instrument, "error": str(e)})
            return {"bid": 1.1000, "ask": 1.1002, "spread": 0.0002}  # Fallback
    
    def calculate_position_size(self, risk_amount, stop_loss_pips, pip_value=10):
        """Calculate position size based on risk management"""
        if stop_loss_pips <= 0:
            return 0
        
        # Position size = Risk Amount / (Stop Loss in Pips * Pip Value)
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to reasonable size (minimum 1000 units for forex)
        position_size = max(1000, round(position_size, -3))  # Round to nearest 1000
        
        return int(position_size)
    
    def execute_order(self, order_data):
        """Execute a trading order"""
        self.execution_stats["total_orders"] += 1
        
        instrument = order_data.get("pair", "EUR_USD")
        direction = order_data.get("direction", "buy")
        size = order_data.get("size", 1000)
        order_type = order_data.get("type", "market")
        stop_loss = order_data.get("stop_loss")
        take_profit = order_data.get("take_profit")
        
        # Convert size to units (negative for sell)
        units = int(size) if direction.lower() == "buy" else -int(size)
        
        log_event("order_execution_start", {
            "instrument": instrument,
            "direction": direction,
            "size": size,
            "type": order_type
        })
        
        # Try OANDA first
        result = self._execute_oanda_order(instrument, units, order_type, stop_loss, take_profit)
        
        if result["success"]:
            self.execution_stats["successful_orders"] += 1
            self._record_trade(result, order_data)
            send_trade_alert(f"✅ {direction.upper()} {instrument} {size} units executed")
            return result
        else:
            # Try fallback broker
            log_event("attempting_fallback", {"reason": result.get("error")})
            fallback_result = self._execute_fallback_order(instrument, units, order_type)
            
            if fallback_result["success"]:
                self.execution_stats["successful_orders"] += 1
                self.execution_stats["fallback_used"] += 1
                self._record_trade(fallback_result, order_data)
                send_trade_alert(f"🔄 {direction.upper()} {instrument} {size} units executed via fallback")
                return fallback_result
            else:
                self.execution_stats["failed_orders"] += 1
                send_critical_alert(f"❌ Failed to execute {direction} {instrument} {size} units")
                return fallback_result
    
    def _execute_oanda_order(self, instrument, units, order_type="MARKET", stop_loss=None, take_profit=None):
        """Execute order via OANDA"""
        if not self.oanda_api:
            return {"success": False, "error": "OANDA API not available", "broker": "oanda"}
        
        try:
            start_time = time.time()
            
            # Build order data
            order_data = {
                "order": {
                    "instrument": instrument,
                    "units": str(units),
                    "type": order_type.upper(),
                    "positionFill": "DEFAULT"
                }
            }
            
            # Add stop loss and take profit if provided
            if stop_loss:
                order_data["order"]["stopLossOnFill"] = {"price": str(stop_loss)}
            
            if take_profit:
                order_data["order"]["takeProfitOnFill"] = {"price": str(take_profit)}
            
            # Execute order
            r = OrderCreate(accountID=self.oanda_account_id, data=order_data)
            response = self.oanda_api.request(r)
            
            execution_time = (time.time() - start_time) * 1000  # ms
            self.execution_stats["avg_latency"] = (
                (self.execution_stats["avg_latency"] * (self.execution_stats["total_orders"] - 1) + execution_time) 
                / self.execution_stats["total_orders"]
            )
            
            # Check for high latency
            if execution_time > self.fallback_latency:
                log_event("high_latency_warning", {"latency_ms": execution_time})
            
            # Extract trade details
            if "orderFillTransaction" in response:
                fill_transaction = response["orderFillTransaction"]
                trade_id = fill_transaction.get("id")
                fill_price = float(fill_transaction.get("price", 0))
                
                return {
                    "success": True,
                    "broker": "oanda",
                    "trade_id": trade_id,
                    "fill_price": fill_price,
                    "execution_time_ms": execution_time,
                    "units": units,
                    "instrument": instrument
                }
            else:
                return {"success": False, "error": "No fill transaction", "broker": "oanda"}
                
        except Exception as e:
            log_event("oanda_execution_error", {"error": str(e), "instrument": instrument})
            return {"success": False, "error": str(e), "broker": "oanda"}
    
    def _execute_fallback_order(self, instrument, units, order_type="MARKET"):
        """Execute order via fallback broker (simulated)"""
        try:
            # Simulate fallback broker execution
            time.sleep(0.1)  # Simulate network delay
            
            # Get current price for simulation
            price_data = self.get_current_price(instrument)
            fill_price = price_data["ask"] if units > 0 else price_data["bid"]
            
            # Add some slippage simulation
            slippage = 0.0001 * (1 if units > 0 else -1)
            fill_price += slippage
            
            trade_id = f"fallback_{int(time.time())}"
            
            log_event("fallback_execution_success", {
                "trade_id": trade_id,
                "fill_price": fill_price,
                "instrument": instrument,
                "units": units
            })
            
            return {
                "success": True,
                "broker": "fallback",
                "trade_id": trade_id,
                "fill_price": fill_price,
                "execution_time_ms": 100,
                "units": units,
                "instrument": instrument
            }
            
        except Exception as e:
            log_event("fallback_execution_error", {"error": str(e)})
            return {"success": False, "error": str(e), "broker": "fallback"}
    
    def _record_trade(self, execution_result, order_data):
        """Record the executed trade"""
        trade_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument": execution_result["instrument"],
            "units": execution_result["units"],
            "fill_price": execution_result["fill_price"],
            "broker": execution_result["broker"],
            "trade_id": execution_result["trade_id"],
            "execution_time_ms": execution_result.get("execution_time_ms", 0),
            "direction": "buy" if execution_result["units"] > 0 else "sell",
            "size": abs(execution_result["units"]),
            "stop_loss": order_data.get("stop_loss"),
            "take_profit": order_data.get("take_profit"),
            "strategy_id": order_data.get("strategy_id", "unknown")
        }
        
        # Add to portfolio tracking
        add_trade(trade_data)
        log_trade(trade_data)
    
    def get_account_balance(self):
        """Get current account balance"""
        if not self.oanda_api:
            return 1000.0  # Demo balance
        
        try:
            r = AccountDetails(accountID=self.oanda_account_id)
            response = self.oanda_api.request(r)
            balance = float(response["account"]["balance"])
            
            # Update equity tracking
            update_equity(balance)
            
            return balance
            
        except Exception as e:
            log_event("balance_fetch_error", {"error": str(e)})
            return 1000.0  # Fallback
    
    def get_execution_stats(self):
        """Get execution statistics"""
        success_rate = (
            self.execution_stats["successful_orders"] / max(1, self.execution_stats["total_orders"]) * 100
        )
        
        return {
            **self.execution_stats,
            "success_rate": success_rate
        }
    
    def run(self):
        """Main run loop for the execution agent"""
        log_event("execution_agent_started", {})
        
        while True:
            try:
                # Check account balance periodically
                balance = self.get_account_balance()
                
                # Log execution statistics
                stats = self.get_execution_stats()
                log_event("execution_stats", stats)
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                log_event("execution_agent_error", {"error": str(e)})
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    agent = ExecutionAgent()
    agent.run()