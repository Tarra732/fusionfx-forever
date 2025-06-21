# agents/market_scanner.py

import datetime
import numpy as np
import pandas as pd
from utils.alerts import send_alert
from core.utils.market_data import get_candles
from core.utils.patterns import detect_fvg, detect_liquidity_sweep

class MarketScanner:
    def __init__(self, pairs, timeframes, adr_threshold):
        self.pairs = pairs
        self.timeframes = timeframes
        self.adr_threshold = adr_threshold
        self.last_scan = {}

    def compute_adr(self, df):
        df['range'] = df['high'] - df['low']
        return df['range'].rolling(window=14).mean().iloc[-1]

    def scan_pair(self, pair, timeframe):
        df = get_candles(pair, timeframe)
        if df is None or df.empty:
            return None

        adr = self.compute_adr(df)
        if adr < self.adr_threshold:
            timeframe = "4H" if timeframe == "15M" else timeframe
            df = get_candles(pair, timeframe)
            adr = self.compute_adr(df)

        signals = []
        if detect_fvg(df):
            signals.append("FVG")
        if detect_liquidity_sweep(df):
            signals.append("LiquiditySweep")

        if signals:
            payload = {
                "pair": pair,
                "timeframe": timeframe,
                "signals": signals,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            send_alert(f"📡 Market signal: {pair} | {', '.join(signals)} @ {timeframe}")
            return payload
        return None

    def run(self):
        results = []
        for pair in self.pairs:
            for tf in self.timeframes:
                key = f"{pair}-{tf}"
                if self.last_scan.get(key) == datetime.date.today():
                    continue
                result = self.scan_pair(pair, tf)
                if result:
                    results.append(result)
                    self.last_scan[key] = datetime.date.today()
        return results

if __name__ == "__main__":
    scanner = MarketScanner(
        pairs=["EUR/USD"],
        timeframes=["15M", "4H"],
        adr_threshold=0.0065
    )
    signals = scanner.run()
    print(signals)