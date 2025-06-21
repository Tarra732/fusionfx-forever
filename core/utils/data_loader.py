# utils/data_loader.py

import requests
import pandas as pd
import zipfile
import io
import os
import json
from datetime import datetime

TRUEFX_URL = "https://www.truefx.com/dev/data"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

def load_truefx_zip(symbol="EURUSD", month="JUNE-2024"):
    """
    Downloads and parses historical tick data from TrueFX.
    """
    filename = f"{symbol}-2024-06.zip"
    url = f"{TRUEFX_URL}/2024/{month}/{filename}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to download: {url}")
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        csv_file = [f for f in z.namelist() if f.endswith(".csv")][0]
        with z.open(csv_file) as f:
            df = pd.read_csv(f, names=["timestamp", "bid", "ask"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def fetch_alpha_vantage_vix(api_key):
    """
    Retrieves VIX data from Alpha Vantage.
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "^VIX",
        "apikey": api_key,
        "datatype": "json"
    }
    response = requests.get(ALPHA_VANTAGE_URL, params=params)
    
    if response.status_code != 200:
        raise Exception("Alpha Vantage API error")

    data = response.json()
    if "Time Series (Daily)" not in data:
        raise Exception("Unexpected API format")

    records = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(records, orient="index")
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={"4. close": "vix_close"})
    df["vix_close"] = df["vix_close"].astype(float)
    return df[["vix_close"]].sort_index()

def normalize_forex(df, symbol="EUR/USD"):
    """
    Normalizes tick or OHLC data for feature input.
    """
    df = df.copy()
    df["mid"] = (df["bid"] + df["ask"]) / 2
    df["returns"] = df["mid"].pct_change()
    df["symbol"] = symbol
    return df.dropna()

def load_config(path="config/fusionfx_config.json"):
    """
    Loads and parses the system config JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing config file at {path}")
    with open(path, "r") as f:
        return json.load(f)

def get_latest_ohlc(data, interval="15min"):
    """
    Returns resampled OHLC from raw tick data.
    """
    data = data.set_index("timestamp")
    ohlc = data["mid"].resample(interval).ohlc()
    return ohlc.dropna()