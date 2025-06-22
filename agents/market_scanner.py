# agents/market_scanner.py

import datetime
import numpy as np
import pandas as pd
import time
import os
import sys
from pathlib import Path
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event
from utils.alerts import send_system_alert

class MarketDataProvider:
    """Provides market data for scanning"""
    
    def __init__(self):
        self.data_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_candles(self, pair="EUR/USD", timeframe="1H", periods=100):
        """Get candlestick data for a currency pair"""
        cache_key = f"{pair}_{timeframe}_{periods}"
        
        # Check cache
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        # Generate synthetic data for demo
        np.random.seed(hash(pair) % 2**32)  # Consistent seed per pair
        
        dates = pd.date_range(end=datetime.datetime.now(), periods=periods, freq=timeframe)
        
        # Generate realistic forex price movements
        base_price = 1.1000 if pair == "EUR/USD" else 1.0000
        if "JPY" in pair:
            base_price = 110.0
        elif "GBP" in pair:
            base_price = 1.3000
        
        # Generate price series with realistic volatility
        returns = np.random.normal(0, 0.0008, periods)  # Small returns
        returns = np.cumsum(returns)  # Cumulative returns
        
        close_prices = base_price * (1 + returns)
        
        # Generate OHLC data
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        
        # Add realistic high/low spreads
        volatility = np.abs(np.random.normal(0, 0.0003, periods))
        high_prices = np.maximum(open_prices, close_prices) + volatility
        low_prices = np.minimum(open_prices, close_prices) - volatility
        
        volumes = np.random.randint(1000, 10000, periods)
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        })
        
        # Cache the data
        self.data_cache[cache_key] = (data, time.time())
        
        return data

class PatternDetector:
    """Detects trading patterns in market data"""
    
    @staticmethod
    def detect_fair_value_gap(df, min_gap_pips=5):
        """Detect Fair Value Gaps (FVG)"""
        if len(df) < 3:
            return False
        
        # Look for gaps between candles
        for i in range(1, len(df) - 1):
            prev_candle = df.iloc[i-1]
            current_candle = df.iloc[i]
            next_candle = df.iloc[i+1]
            
            # Bullish FVG: gap between prev low and next high
            if (prev_candle['low'] > next_candle['high'] and 
                current_candle['close'] > current_candle['open']):
                gap_size = (prev_candle['low'] - next_candle['high']) * 10000  # Convert to pips
                if gap_size >= min_gap_pips:
                    return True
            
            # Bearish FVG: gap between prev high and next low
            if (prev_candle['high'] < next_candle['low'] and 
                current_candle['close'] < current_candle['open']):
                gap_size = (next_candle['low'] - prev_candle['high']) * 10000  # Convert to pips
                if gap_size >= min_gap_pips:
                    return True
        
        return False
    
    @staticmethod
    def detect_liquidity_sweep(df, lookback=20):
        """Detect liquidity sweeps (stop hunts)"""
        if len(df) < lookback + 5:
            return False
        
        recent_data = df.tail(lookback)
        
        # Find recent highs and lows
        recent_high = recent_data['high'].max()
        recent_low = recent_data['low'].min()
        
        latest_candle = df.iloc[-1]
        
        # Check if latest candle swept liquidity
        if latest_candle['high'] > recent_high and latest_candle['close'] < recent_high:
            return True  # Bearish liquidity sweep
        
        if latest_candle['low'] < recent_low and latest_candle['close'] > recent_low:
            return True  # Bullish liquidity sweep
        
        return False
    
    @staticmethod
    def detect_order_block(df, lookback=10):
        """Detect order blocks (institutional levels)"""
        if len(df) < lookback + 5:
            return False
        
        recent_data = df.tail(lookback)
        
        # Look for strong rejection candles
        for i in range(len(recent_data)):
            candle = recent_data.iloc[i]
            body_size = abs(candle['close'] - candle['open'])
            wick_size = max(
                candle['high'] - max(candle['open'], candle['close']),
                min(candle['open'], candle['close']) - candle['low']
            )
            
            # Strong rejection if wick is 2x body size
            if wick_size > body_size * 2 and body_size > 0:
                return True
        
        return False
    
    @staticmethod
    def detect_break_of_structure(df, lookback=20):
        """Detect break of market structure"""
        if len(df) < lookback + 5:
            return False
        
        recent_data = df.tail(lookback)
        
        # Find swing highs and lows
        highs = []
        lows = []
        
        for i in range(2, len(recent_data) - 2):
            candle = recent_data.iloc[i]
            
            # Check if it's a swing high
            if (candle['high'] > recent_data.iloc[i-1]['high'] and 
                candle['high'] > recent_data.iloc[i-2]['high'] and
                candle['high'] > recent_data.iloc[i+1]['high'] and
                candle['high'] > recent_data.iloc[i+2]['high']):
                highs.append(candle['high'])
            
            # Check if it's a swing low
            if (candle['low'] < recent_data.iloc[i-1]['low'] and 
                candle['low'] < recent_data.iloc[i-2]['low'] and
                candle['low'] < recent_data.iloc[i+1]['low'] and
                candle['low'] < recent_data.iloc[i+2]['low']):
                lows.append(candle['low'])
        
        latest_close = df.iloc[-1]['close']
        
        # Check for break of structure
        if highs and latest_close > max(highs):
            return True  # Bullish break of structure
        
        if lows and latest_close < min(lows):
            return True  # Bearish break of structure
        
        return False

class MarketScanner:
    """Scans multiple currency pairs for trading opportunities"""
    
    def __init__(self, pairs=None, timeframes=None, adr_threshold=0.0065):
        self.pairs = pairs or ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
        self.timeframes = timeframes or ["15M", "1H", "4H"]
        self.adr_threshold = adr_threshold
        self.last_scan = {}
        
        # Initialize components
        self.data_provider = MarketDataProvider()
        self.pattern_detector = PatternDetector()
        
        # Scan results storage
        self.scan_results = []
        self.scan_history_file = Path("data/scan_history.json")
        self.scan_history_file.parent.mkdir(exist_ok=True)
        
        log_event("market_scanner_initialized", {
            "pairs": self.pairs,
            "timeframes": self.timeframes,
            "adr_threshold": adr_threshold
        })
    
    def compute_adr(self, df, period=14):
        """Compute Average Daily Range"""
        if len(df) < period:
            return 0
        
        df = df.copy()
        df['range'] = df['high'] - df['low']
        adr = df['range'].rolling(window=period).mean().iloc[-1]
        return adr
    
    def compute_volatility_metrics(self, df):
        """Compute various volatility metrics"""
        if len(df) < 20:
            return {}
        
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        
        return {
            "volatility": df['returns'].std(),
            "atr": self.compute_atr(df),
            "range_ratio": (df['high'] - df['low']).mean() / df['close'].mean()
        }
    
    def compute_atr(self, df, period=14):
        """Compute Average True Range"""
        if len(df) < period + 1:
            return 0
        
        df = df.copy()
        df['prev_close'] = df['close'].shift(1)
        
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        atr = df['true_range'].rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def analyze_market_structure(self, df):
        """Analyze overall market structure"""
        if len(df) < 50:
            return {"trend": "unknown", "strength": 0}
        
        # Simple trend analysis using moving averages
        df = df.copy()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        latest = df.iloc[-1]
        
        # Determine trend
        if latest['close'] > latest['sma_20'] > latest['sma_50']:
            trend = "bullish"
            strength = min(1.0, (latest['close'] - latest['sma_50']) / latest['sma_50'] * 100)
        elif latest['close'] < latest['sma_20'] < latest['sma_50']:
            trend = "bearish"
            strength = min(1.0, (latest['sma_50'] - latest['close']) / latest['sma_50'] * 100)
        else:
            trend = "sideways"
            strength = 0.5
        
        return {"trend": trend, "strength": strength}
    
    def scan_pair(self, pair, timeframe):
        """Scan a single currency pair for signals"""
        try:
            # Get market data
            df = self.data_provider.get_candles(pair, timeframe, periods=100)
            if df is None or len(df) < 20:
                return None
            
            # Compute metrics
            adr = self.compute_adr(df)
            volatility_metrics = self.compute_volatility_metrics(df)
            market_structure = self.analyze_market_structure(df)
            
            # Check if market is active enough
            if adr < self.adr_threshold:
                log_event("low_volatility_skip", {
                    "pair": pair,
                    "timeframe": timeframe,
                    "adr": adr,
                    "threshold": self.adr_threshold
                })
                return None
            
            # Detect patterns
            signals = []
            signal_strength = 0
            
            if self.pattern_detector.detect_fair_value_gap(df):
                signals.append("FVG")
                signal_strength += 0.3
            
            if self.pattern_detector.detect_liquidity_sweep(df):
                signals.append("LiquiditySweep")
                signal_strength += 0.4
            
            if self.pattern_detector.detect_order_block(df):
                signals.append("OrderBlock")
                signal_strength += 0.2
            
            if self.pattern_detector.detect_break_of_structure(df):
                signals.append("BreakOfStructure")
                signal_strength += 0.5
            
            # Create scan result
            if signals:
                result = {
                    "pair": pair,
                    "timeframe": timeframe,
                    "signals": signals,
                    "signal_strength": signal_strength,
                    "adr": adr,
                    "volatility": volatility_metrics.get("volatility", 0),
                    "atr": volatility_metrics.get("atr", 0),
                    "market_structure": market_structure,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "current_price": df.iloc[-1]['close']
                }
                
                log_event("market_signal_detected", result)
                
                # Send alert for strong signals
                if signal_strength >= 0.5:
                    send_system_alert(
                        f"📡 Strong signal: {pair} | {', '.join(signals)} @ {timeframe} "
                        f"(strength: {signal_strength:.2f})"
                    )
                
                return result
            
            return None
            
        except Exception as e:
            log_event("scan_pair_error", {
                "pair": pair,
                "timeframe": timeframe,
                "error": str(e)
            })
            return None
    
    def scan_all_pairs(self):
        """Scan all configured pairs and timeframes"""
        results = []
        
        for pair in self.pairs:
            for timeframe in self.timeframes:
                # Check if we've scanned this recently
                scan_key = f"{pair}_{timeframe}"
                last_scan_time = self.last_scan.get(scan_key, 0)
                
                # Skip if scanned within last 15 minutes
                if time.time() - last_scan_time < 900:
                    continue
                
                result = self.scan_pair(pair, timeframe)
                if result:
                    results.append(result)
                
                self.last_scan[scan_key] = time.time()
        
        # Store results
        if results:
            self.scan_results.extend(results)
            self._save_scan_history()
        
        return results
    
    def _save_scan_history(self):
        """Save scan history to file"""
        try:
            # Keep only last 1000 results
            if len(self.scan_results) > 1000:
                self.scan_results = self.scan_results[-1000:]
            
            with open(self.scan_history_file, 'w') as f:
                json.dump(self.scan_results, f, indent=2)
                
        except Exception as e:
            log_event("scan_history_save_error", {"error": str(e)})
    
    def get_scan_summary(self):
        """Get summary of recent scans"""
        if not self.scan_results:
            return {"total_signals": 0, "pairs_scanned": 0, "last_scan": None}
        
        recent_scans = [
            s for s in self.scan_results 
            if datetime.datetime.fromisoformat(s["timestamp"]) > 
               datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        ]
        
        return {
            "total_signals": len(recent_scans),
            "pairs_scanned": len(set(s["pair"] for s in recent_scans)),
            "signal_types": list(set(
                signal for s in recent_scans for signal in s["signals"]
            )),
            "strongest_signal": max(recent_scans, key=lambda x: x["signal_strength"]) if recent_scans else None,
            "last_scan": recent_scans[-1]["timestamp"] if recent_scans else None
        }
    
    def run(self):
        """Main run loop for market scanner"""
        log_event("market_scanner_started", {})
        send_system_alert("Market Scanner started")
        
        while True:
            try:
                # Scan all pairs
                results = self.scan_all_pairs()
                
                # Log scan summary
                summary = self.get_scan_summary()
                log_event("scan_cycle_complete", {
                    "new_signals": len(results),
                    "summary": summary
                })
                
                # Sleep for 10 minutes
                time.sleep(600)
                
            except Exception as e:
                log_event("market_scanner_error", {"error": str(e)})
                send_system_alert(f"Market Scanner error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    scanner = MarketScanner(
        pairs=["EUR/USD", "GBP/USD", "USD/JPY"],
        timeframes=["15M", "1H", "4H"],
        adr_threshold=0.0065
    )
    
    # Test single scan
    results = scanner.scan_all_pairs()
    print(f"Scan results: {len(results)} signals found")
    
    for result in results:
        print(f"Signal: {result['pair']} - {result['signals']} (strength: {result['signal_strength']:.2f})")
    
    # Start main loop
    scanner.run()