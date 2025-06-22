# agents/utils/portfolio.py

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

class PortfolioTracker:
    def __init__(self):
        self.trades_file = Path("data/trades.json")
        self.equity_file = Path("data/equity_curve.json")
        self.trades_file.parent.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        if not self.trades_file.exists():
            with open(self.trades_file, "w") as f:
                json.dump([], f)
        
        if not self.equity_file.exists():
            with open(self.equity_file, "w") as f:
                json.dump({"timestamps": [], "equity": [1000.0]}, f)  # Start with $1000
    
    def add_trade(self, trade_data):
        """Add a new trade to the portfolio"""
        with open(self.trades_file, "r") as f:
            trades = json.load(f)
        
        trade_data["timestamp"] = datetime.utcnow().isoformat()
        trades.append(trade_data)
        
        with open(self.trades_file, "w") as f:
            json.dump(trades, f, indent=2)
    
    def update_equity(self, new_equity):
        """Update the equity curve"""
        with open(self.equity_file, "r") as f:
            equity_data = json.load(f)
        
        equity_data["timestamps"].append(datetime.utcnow().isoformat())
        equity_data["equity"].append(new_equity)
        
        with open(self.equity_file, "w") as f:
            json.dump(equity_data, f, indent=2)
    
    def get_trades(self, days_back=30):
        """Get trades from the last N days"""
        with open(self.trades_file, "r") as f:
            trades = json.load(f)
        
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent_trades = [
            trade for trade in trades 
            if datetime.fromisoformat(trade["timestamp"]) > cutoff
        ]
        return recent_trades
    
    def get_equity_curve(self):
        """Get the equity curve data"""
        with open(self.equity_file, "r") as f:
            return json.load(f)

# Global portfolio tracker instance
portfolio_tracker = PortfolioTracker()

def get_portfolio_metrics():
    """Calculate and return portfolio performance metrics"""
    equity_data = portfolio_tracker.get_equity_curve()
    trades = portfolio_tracker.get_trades(30)
    
    if len(equity_data["equity"]) < 2:
        return {
            "sharpe": 0.0,
            "sortino": 0.0,
            "drawdown": 0.0,
            "vix": 20.0,  # Default VIX
            "equity_curve": equity_data["equity"],
            "active_pairs": ["EUR/USD"],
            "is_trending": True,
            "win_rate": 0.5,
            "avg_return": 0.0,
            "volatility": 0.02,
            "trade_frequency": 0.0
        }
    
    equity_series = np.array(equity_data["equity"])
    returns = np.diff(equity_series) / equity_series[:-1]
    
    # Calculate Sharpe ratio
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
    else:
        sharpe = 0.0
    
    # Calculate Sortino ratio
    negative_returns = returns[returns < 0]
    if len(negative_returns) > 0:
        downside_std = np.std(negative_returns)
        sortino = np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0.0
    else:
        sortino = sharpe
    
    # Calculate maximum drawdown
    peak = np.maximum.accumulate(equity_series)
    drawdown = np.max((peak - equity_series) / peak) * 100
    
    # Calculate win rate
    winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0.5
    
    # Calculate average return
    avg_return = np.mean([t.get("pnl", 0) for t in trades]) if trades else 0.0
    
    # Calculate volatility
    volatility = np.std(returns) if len(returns) > 1 else 0.02
    
    # Trade frequency (trades per day)
    trade_frequency = len(trades) / 30.0
    
    return {
        "sharpe": sharpe,
        "sortino": sortino,
        "drawdown": drawdown,
        "vix": 20.0,  # TODO: Connect to real VIX data
        "equity_curve": equity_data["equity"],
        "active_pairs": list(set([t.get("pair", "EUR/USD") for t in trades])) or ["EUR/USD"],
        "is_trending": True,  # TODO: Implement trend detection
        "win_rate": win_rate,
        "avg_return": avg_return,
        "volatility": volatility,
        "trade_frequency": trade_frequency
    }

def add_trade(trade_data):
    """Add a trade to the portfolio"""
    portfolio_tracker.add_trade(trade_data)

def update_equity(new_equity):
    """Update the current equity"""
    portfolio_tracker.update_equity(new_equity)