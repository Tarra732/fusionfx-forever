# agents/risk_kernel.py

import numpy as np
import time
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event
from agents.utils.portfolio import get_portfolio_metrics
from utils.alerts import send_critical_alert, send_system_alert

class RiskKernel:
    """Advanced risk management system for position sizing and risk control"""
    
    def __init__(self, base_risk=0.02, vix_penalty_curve=None, max_drawdown=0.15):
        self.base_risk = base_risk  # Base risk per trade (2% of account)
        self.max_drawdown = max_drawdown  # Maximum allowed drawdown (15%)
        self.vix_penalty_curve = vix_penalty_curve or [
            {"threshold": 20, "multiplier": 1.0},   # Normal market
            {"threshold": 25, "multiplier": 0.8},   # Elevated volatility
            {"threshold": 30, "multiplier": 0.6},   # High volatility
            {"threshold": 40, "multiplier": 0.3},   # Extreme volatility
            {"threshold": 50, "multiplier": 0.1}    # Crisis mode
        ]
        
        # Risk limits
        self.max_positions = 5
        self.max_risk_per_pair = 0.05  # 5% max risk per currency pair
        self.max_correlation_exposure = 0.10  # 10% max for correlated pairs
        
        # Dynamic risk adjustment parameters
        self.win_rate_threshold = 0.4  # Reduce risk if win rate below 40%
        self.sharpe_threshold = 0.5    # Reduce risk if Sharpe ratio below 0.5
        self.volatility_lookback = 20  # Days to look back for volatility calculation
        
        # Risk state tracking
        self.risk_state = "normal"  # normal, cautious, defensive, emergency
        self.last_risk_update = datetime.utcnow()
        
        # Data storage
        self.risk_data_file = Path("data/risk_metrics.json")
        self.risk_data_file.parent.mkdir(exist_ok=True)
        
        log_event("risk_kernel_initialized", {
            "base_risk": base_risk,
            "max_drawdown": max_drawdown,
            "max_positions": self.max_positions
        })
    
    def fetch_vix(self):
        """Fetch current VIX value"""
        try:
            # Try to fetch real VIX data (would need API key)
            # For demo, we'll simulate VIX data
            vix_value = np.random.uniform(15, 35)  # Typical VIX range
            
            log_event("vix_fetched", {"vix": vix_value})
            return vix_value
            
        except Exception as e:
            log_event("vix_fetch_error", {"error": str(e)})
            return 20.0  # Default neutral VIX
    
    def get_market_volatility(self):
        """Calculate current market volatility metrics"""
        try:
            portfolio_metrics = get_portfolio_metrics()
            
            # Get recent volatility
            current_volatility = portfolio_metrics.get("volatility", 0.02)
            
            # Calculate volatility regime
            if current_volatility < 0.01:
                regime = "low"
            elif current_volatility < 0.02:
                regime = "normal"
            elif current_volatility < 0.04:
                regime = "high"
            else:
                regime = "extreme"
            
            return {
                "volatility": current_volatility,
                "regime": regime,
                "annualized_vol": current_volatility * np.sqrt(252)
            }
            
        except Exception as e:
            log_event("volatility_calculation_error", {"error": str(e)})
            return {"volatility": 0.02, "regime": "normal", "annualized_vol": 0.32}
    
    def apply_vix_penalty(self, base_risk, vix):
        """Apply VIX-based risk reduction"""
        multiplier = 1.0
        
        for rule in sorted(self.vix_penalty_curve, key=lambda x: x["threshold"], reverse=True):
            if vix >= rule["threshold"]:
                multiplier = rule["multiplier"]
                break
        
        adjusted_risk = base_risk * multiplier
        
        log_event("vix_penalty_applied", {
            "vix": vix,
            "multiplier": multiplier,
            "base_risk": base_risk,
            "adjusted_risk": adjusted_risk
        })
        
        return adjusted_risk
    
    def apply_performance_penalty(self, base_risk):
        """Apply performance-based risk adjustments"""
        try:
            portfolio_metrics = get_portfolio_metrics()
            
            multiplier = 1.0
            
            # Win rate adjustment
            win_rate = portfolio_metrics.get("win_rate", 0.5)
            if win_rate < self.win_rate_threshold:
                win_rate_penalty = 0.5 + (win_rate / self.win_rate_threshold) * 0.5
                multiplier *= win_rate_penalty
            
            # Sharpe ratio adjustment
            sharpe = portfolio_metrics.get("sharpe", 0.0)
            if sharpe < self.sharpe_threshold:
                sharpe_penalty = 0.5 + max(0, sharpe / self.sharpe_threshold) * 0.5
                multiplier *= sharpe_penalty
            
            # Drawdown adjustment
            current_drawdown = portfolio_metrics.get("drawdown", 0.0) / 100
            if current_drawdown > self.max_drawdown * 0.5:  # 50% of max drawdown
                drawdown_penalty = 1.0 - (current_drawdown / self.max_drawdown) * 0.5
                multiplier *= max(0.1, drawdown_penalty)
            
            adjusted_risk = base_risk * multiplier
            
            log_event("performance_penalty_applied", {
                "win_rate": win_rate,
                "sharpe": sharpe,
                "drawdown": current_drawdown,
                "multiplier": multiplier,
                "adjusted_risk": adjusted_risk
            })
            
            return adjusted_risk
            
        except Exception as e:
            log_event("performance_penalty_error", {"error": str(e)})
            return base_risk
    
    def calculate_position_size(self, account_balance=None, stop_loss_pips=None, pair="EUR/USD"):
        """Calculate optimal position size based on risk management rules"""
        try:
            # Get current account balance
            if account_balance is None:
                portfolio_metrics = get_portfolio_metrics()
                account_balance = portfolio_metrics.get("equity_curve", [1000])[-1]
            
            # Get market conditions
            vix = self.fetch_vix()
            volatility_data = self.get_market_volatility()
            
            # Start with base risk
            risk_amount = account_balance * self.base_risk
            
            # Apply VIX penalty
            risk_amount = self.apply_vix_penalty(risk_amount, vix)
            
            # Apply performance penalty
            risk_amount = self.apply_performance_penalty(risk_amount)
            
            # Apply volatility adjustment
            vol_multiplier = 1.0
            if volatility_data["regime"] == "high":
                vol_multiplier = 0.7
            elif volatility_data["regime"] == "extreme":
                vol_multiplier = 0.4
            
            risk_amount *= vol_multiplier
            
            # Calculate position size based on stop loss
            if stop_loss_pips and stop_loss_pips > 0:
                # Assume $10 per pip for major pairs (simplified)
                pip_value = 10
                position_size = risk_amount / (stop_loss_pips * pip_value)
                
                # Round to reasonable size
                position_size = max(1000, round(position_size, -3))  # Minimum 1000 units
            else:
                # Default position size based on volatility
                position_size = risk_amount / (volatility_data["volatility"] * account_balance)
                position_size = max(1000, round(position_size, -3))
            
            # Apply maximum position limits
            max_position_value = account_balance * self.max_risk_per_pair
            max_position_size = max_position_value / 1.1  # Assume EUR/USD around 1.1
            
            final_position_size = min(position_size, max_position_size)
            
            # Update risk state
            self._update_risk_state(vix, volatility_data, account_balance)
            
            # Log the calculation
            log_event("position_size_calculated", {
                "account_balance": account_balance,
                "base_risk": self.base_risk,
                "vix": vix,
                "volatility_regime": volatility_data["regime"],
                "stop_loss_pips": stop_loss_pips,
                "calculated_size": position_size,
                "final_size": final_position_size,
                "risk_amount": risk_amount,
                "risk_state": self.risk_state
            })
            
            return int(final_position_size)
            
        except Exception as e:
            log_event("position_size_error", {"error": str(e)})
            # Return conservative default
            return 1000
    
    def _update_risk_state(self, vix, volatility_data, account_balance):
        """Update overall risk state based on market conditions"""
        portfolio_metrics = get_portfolio_metrics()
        current_drawdown = portfolio_metrics.get("drawdown", 0.0) / 100
        
        # Determine risk state
        if current_drawdown > self.max_drawdown * 0.8:  # 80% of max drawdown
            new_state = "emergency"
        elif vix > 40 or volatility_data["regime"] == "extreme":
            new_state = "defensive"
        elif vix > 25 or current_drawdown > self.max_drawdown * 0.5:
            new_state = "cautious"
        else:
            new_state = "normal"
        
        # Check for state change
        if new_state != self.risk_state:
            log_event("risk_state_change", {
                "old_state": self.risk_state,
                "new_state": new_state,
                "vix": vix,
                "drawdown": current_drawdown,
                "volatility_regime": volatility_data["regime"]
            })
            
            # Send alerts for critical state changes
            if new_state == "emergency":
                send_critical_alert(f"Risk state: EMERGENCY - Drawdown {current_drawdown:.1%}")
            elif new_state == "defensive" and self.risk_state != "emergency":
                send_system_alert(f"Risk state: DEFENSIVE - VIX {vix:.1f}")
            
            self.risk_state = new_state
        
        self.last_risk_update = datetime.utcnow()
    
    def check_position_limits(self, new_position_data):
        """Check if new position violates risk limits"""
        try:
            # Get current positions (simplified - would integrate with broker API)
            current_positions = self._get_current_positions()
            
            # Check maximum number of positions
            if len(current_positions) >= self.max_positions:
                log_event("position_limit_exceeded", {
                    "current_positions": len(current_positions),
                    "max_positions": self.max_positions
                })
                return False, "Maximum number of positions reached"
            
            # Check pair-specific risk
            pair = new_position_data.get("pair", "EUR/USD")
            pair_exposure = sum(pos["risk_amount"] for pos in current_positions if pos["pair"] == pair)
            
            portfolio_metrics = get_portfolio_metrics()
            account_balance = portfolio_metrics.get("equity_curve", [1000])[-1]
            max_pair_risk = account_balance * self.max_risk_per_pair
            
            if pair_exposure + new_position_data.get("risk_amount", 0) > max_pair_risk:
                log_event("pair_risk_limit_exceeded", {
                    "pair": pair,
                    "current_exposure": pair_exposure,
                    "new_risk": new_position_data.get("risk_amount", 0),
                    "max_pair_risk": max_pair_risk
                })
                return False, f"Pair risk limit exceeded for {pair}"
            
            # Check correlation limits (simplified)
            correlated_pairs = self._get_correlated_pairs(pair)
            correlated_exposure = sum(
                pos["risk_amount"] for pos in current_positions 
                if pos["pair"] in correlated_pairs
            )
            
            max_correlation_risk = account_balance * self.max_correlation_exposure
            if correlated_exposure + new_position_data.get("risk_amount", 0) > max_correlation_risk:
                log_event("correlation_limit_exceeded", {
                    "pair": pair,
                    "correlated_pairs": correlated_pairs,
                    "correlated_exposure": correlated_exposure,
                    "max_correlation_risk": max_correlation_risk
                })
                return False, "Correlation risk limit exceeded"
            
            return True, "Position approved"
            
        except Exception as e:
            log_event("position_limit_check_error", {"error": str(e)})
            return False, f"Error checking limits: {str(e)}"
    
    def _get_current_positions(self):
        """Get current open positions (simplified)"""
        # In real implementation, this would query the broker API
        # For demo, return empty list
        return []
    
    def _get_correlated_pairs(self, pair):
        """Get pairs that are correlated with the given pair"""
        correlation_map = {
            "EUR/USD": ["GBP/USD", "AUD/USD"],
            "GBP/USD": ["EUR/USD", "AUD/USD"],
            "USD/JPY": ["USD/CHF"],
            "AUD/USD": ["EUR/USD", "GBP/USD", "NZD/USD"],
            "NZD/USD": ["AUD/USD"]
        }
        
        return correlation_map.get(pair, [])
    
    def get_risk_metrics(self):
        """Get current risk metrics and state"""
        portfolio_metrics = get_portfolio_metrics()
        vix = self.fetch_vix()
        volatility_data = self.get_market_volatility()
        
        return {
            "risk_state": self.risk_state,
            "base_risk": self.base_risk,
            "current_drawdown": portfolio_metrics.get("drawdown", 0.0),
            "max_drawdown_limit": self.max_drawdown * 100,
            "vix": vix,
            "volatility_regime": volatility_data["regime"],
            "win_rate": portfolio_metrics.get("win_rate", 0.5),
            "sharpe_ratio": portfolio_metrics.get("sharpe", 0.0),
            "last_update": self.last_risk_update.isoformat()
        }
    
    def emergency_stop(self):
        """Emergency stop - halt all trading"""
        log_event("emergency_stop_triggered", {"risk_state": self.risk_state})
        send_critical_alert("🚨 EMERGENCY STOP: All trading halted due to risk limits")
        
        # In real implementation, this would:
        # 1. Close all open positions
        # 2. Cancel all pending orders
        # 3. Set trading to manual mode
        # 4. Send notifications to all channels
        
        self.risk_state = "emergency"
        return True
    
    def run(self):
        """Main run loop for the risk kernel"""
        log_event("risk_kernel_started", {})
        send_system_alert("Risk Kernel started")
        
        while True:
            try:
                # Update risk metrics
                risk_metrics = self.get_risk_metrics()
                
                # Check for emergency conditions
                if risk_metrics["current_drawdown"] > self.max_drawdown * 100:
                    self.emergency_stop()
                
                # Log current risk state
                log_event("risk_metrics_update", risk_metrics)
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                log_event("risk_kernel_error", {"error": str(e)})
                send_system_alert(f"Risk Kernel error: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    risk_kernel = RiskKernel()
    
    # Test position size calculation
    position_size = risk_kernel.calculate_position_size(
        account_balance=10000,
        stop_loss_pips=20,
        pair="EUR/USD"
    )
    print(f"Calculated position size: {position_size}")
    
    # Start main loop
    risk_kernel.run()