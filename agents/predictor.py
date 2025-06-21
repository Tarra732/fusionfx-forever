# agents/predictor.py

import pandas as pd
import numpy as np
from nixtla.forecast import TimeGPT
from sklearn.ensemble import GradientBoostingClassifier
from core.utils.market_data import get_indicator_data
from utils.alerts import send_alert

class Predictor:
    def __init__(self, vix_source, features):
        self.vix_source = vix_source
        self.features = features
        self.timegpt = TimeGPT(token="your_timegpt_api_key")
        self.model = GradientBoostingClassifier(n_estimators=100)

    def load_features(self):
        data = {}
        for f in self.features:
            df = get_indicator_data(f)
            if df is not None:
                data[f] = df
        return pd.concat(data.values(), axis=1)

    def forecast_direction(self, pair="EUR/USD"):
        prices = get_indicator_data(f"{pair}_close", lookback=100)
        if prices is None or prices.empty:
            return None

        df = self.load_features()
        df["future_return"] = prices.pct_change().shift(-1)
        df.dropna(inplace=True)
        df["label"] = np.where(df["future_return"] > 0, 1, 0)

        X = df[self.features]
        y = df["label"]
        self.model.fit(X, y)

        latest_features = X.iloc[-1].values.reshape(1, -1)
        prediction = self.model.predict(latest_features)[0]

        gpt_forecast = self.timegpt.forecast(prices[-60:], horizon=5)
        gpt_bias = 1 if gpt_forecast[-1] > prices.iloc[-1] else 0

        final_bias = 1 if (prediction + gpt_bias) >= 1 else 0

        send_alert(f"📊 Predictor Bias: {'Bullish' if final_bias else 'Bearish'} | ML: {prediction} | GPT: {gpt_bias}")
        return {"pair": pair, "bias": final_bias}

if __name__ == "__main__":
    predictor = Predictor(
        vix_source="alphavantage",
        features=["london_open_volume", "yield_spread", "usd_index_delta"]
    )
    output = predictor.forecast_direction()
    print(output)