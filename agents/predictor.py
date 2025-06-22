# agents/predictor.py

import pandas as pd
import numpy as np
import time
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event
from utils.alerts import send_system_alert

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not available. Install for ML predictions.")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[WARNING] LightGBM not available. Install for advanced ML predictions.")

class MarketDataProvider:
    """Provides market data and indicators"""
    
    def __init__(self):
        self.data_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_forex_data(self, pair="EUR/USD", timeframe="1H", periods=100):
        """Get forex price data (simulated for demo)"""
        cache_key = f"{pair}_{timeframe}_{periods}"
        
        # Check cache
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        # Generate synthetic data for demo
        np.random.seed(42)  # For reproducible demo data
        
        dates = pd.date_range(end=datetime.now(), periods=periods, freq=timeframe)
        
        # Generate realistic forex price movements
        base_price = 1.1000 if pair == "EUR/USD" else 1.0000
        returns = np.random.normal(0, 0.001, periods)  # Small daily returns
        returns = np.cumsum(returns)  # Cumulative returns
        
        prices = base_price * (1 + returns)
        
        # Add some intraday volatility
        high = prices * (1 + np.abs(np.random.normal(0, 0.0005, periods)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.0005, periods)))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': high,
            'low': low,
            'close': prices,
            'volume': np.random.randint(1000, 10000, periods)
        })
        
        # Cache the data
        self.data_cache[cache_key] = (data, time.time())
        
        return data
    
    def calculate_technical_indicators(self, data):
        """Calculate technical indicators"""
        df = data.copy()
        
        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volatility
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        
        # Price momentum
        df['momentum_5'] = df['close'].pct_change(5)
        df['momentum_10'] = df['close'].pct_change(10)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
    
    def get_vix_data(self):
        """Get VIX data (simulated)"""
        # Simulate VIX data
        return np.random.uniform(15, 35)  # Typical VIX range
    
    def get_economic_indicators(self):
        """Get economic indicators (simulated)"""
        return {
            'usd_index': np.random.uniform(95, 105),
            'yield_spread': np.random.uniform(1.5, 3.0),
            'oil_price': np.random.uniform(60, 80),
            'gold_price': np.random.uniform(1800, 2000)
        }

class PredictionModel:
    """Machine learning model for price prediction"""
    
    def __init__(self, model_type="lightgbm"):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_names = []
        self.model_path = Path("models/predictor_model.pkl")
        self.model_path.parent.mkdir(exist_ok=True)
        
        self.initialize_model()
        self.load_model()
    
    def initialize_model(self):
        """Initialize the ML model"""
        if self.model_type == "lightgbm" and LIGHTGBM_AVAILABLE:
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        elif SKLEARN_AVAILABLE:
            if self.model_type == "random_forest":
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif self.model_type == "gradient_boosting":
                self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            else:
                self.model = LogisticRegression(random_state=42)
        else:
            # Fallback to simple rule-based model
            self.model = None
    
    def prepare_features(self, data):
        """Prepare features for ML model"""
        df = data.copy()
        
        # Technical indicator features
        features = [
            'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'macd', 'macd_signal', 'macd_histogram',
            'rsi', 'bb_position', 'volatility',
            'momentum_5', 'momentum_10', 'volume_ratio'
        ]
        
        # Add time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_london_session'] = ((df['hour'] >= 8) & (df['hour'] <= 16)).astype(int)
        df['is_ny_session'] = ((df['hour'] >= 13) & (df['hour'] <= 21)).astype(int)
        
        features.extend(['hour', 'day_of_week', 'is_london_session', 'is_ny_session'])
        
        # Add lagged features
        for lag in [1, 2, 3]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            features.extend([f'close_lag_{lag}', f'volume_lag_{lag}'])
        
        # Create target variable (1 if price goes up, 0 if down)
        df['future_return'] = df['close'].shift(-1) / df['close'] - 1
        df['target'] = (df['future_return'] > 0).astype(int)
        
        self.feature_names = features
        return df[features + ['target']].dropna()
    
    def train(self, data):
        """Train the prediction model"""
        if self.model is None:
            return False
        
        try:
            prepared_data = self.prepare_features(data)
            
            if len(prepared_data) < 50:  # Need minimum data
                log_event("insufficient_training_data", {"samples": len(prepared_data)})
                return False
            
            X = prepared_data[self.feature_names]
            y = prepared_data['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features if using sklearn
            if SKLEARN_AVAILABLE and self.scaler:
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_test_scaled = self.scaler.transform(X_test)
            else:
                X_train_scaled = X_train
                X_test_scaled = X_test
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            log_event("model_training_complete", {
                "accuracy": accuracy,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "model_type": self.model_type
            })
            
            self.save_model()
            return True
            
        except Exception as e:
            log_event("model_training_error", {"error": str(e)})
            return False
    
    def predict(self, data):
        """Make prediction on new data"""
        if self.model is None:
            # Fallback to simple rule-based prediction
            return self._rule_based_prediction(data)
        
        try:
            prepared_data = self.prepare_features(data)
            
            if len(prepared_data) == 0:
                return 0.5  # Neutral prediction
            
            X = prepared_data[self.feature_names].iloc[-1:] # Latest data point
            
            # Scale if needed
            if SKLEARN_AVAILABLE and self.scaler:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X
            
            # Get prediction probability
            if hasattr(self.model, 'predict_proba'):
                prob = self.model.predict_proba(X_scaled)[0][1]  # Probability of class 1 (up)
            else:
                prob = self.model.predict(X_scaled)[0]
            
            return prob
            
        except Exception as e:
            log_event("prediction_error", {"error": str(e)})
            return self._rule_based_prediction(data)
    
    def _rule_based_prediction(self, data):
        """Simple rule-based prediction as fallback"""
        try:
            latest = data.iloc[-1]
            
            # Simple momentum + RSI strategy
            score = 0
            
            # RSI signal
            if latest['rsi'] < 30:  # Oversold
                score += 0.3
            elif latest['rsi'] > 70:  # Overbought
                score -= 0.3
            
            # MACD signal
            if latest['macd'] > latest['macd_signal']:
                score += 0.2
            else:
                score -= 0.2
            
            # Moving average signal
            if latest['close'] > latest['sma_20']:
                score += 0.2
            else:
                score -= 0.2
            
            # Bollinger bands signal
            if latest['bb_position'] < 0.2:  # Near lower band
                score += 0.3
            elif latest['bb_position'] > 0.8:  # Near upper band
                score -= 0.3
            
            # Convert to probability (0-1)
            prob = max(0, min(1, 0.5 + score))
            return prob
            
        except Exception as e:
            log_event("rule_based_prediction_error", {"error": str(e)})
            return 0.5  # Neutral
    
    def save_model(self):
        """Save model to disk"""
        if self.model is None:
            return
        
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_type': self.model_type
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            log_event("model_saved", {"path": str(self.model_path)})
            
        except Exception as e:
            log_event("model_save_error", {"error": str(e)})
    
    def load_model(self):
        """Load model from disk"""
        if not self.model_path.exists():
            return
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            
            log_event("model_loaded", {"path": str(self.model_path)})
            
        except Exception as e:
            log_event("model_load_error", {"error": str(e)})

class Predictor:
    """Main predictor agent for forex price forecasting"""
    
    def __init__(self, vix_source="alphavantage", features=None, models=["lightgbm"]):
        self.vix_source = vix_source
        self.features = features or ["london_open_volume", "yield_spread", "usd_index_delta"]
        self.models = models
        
        # Initialize components
        self.data_provider = MarketDataProvider()
        self.prediction_models = {}
        
        # Initialize models
        for model_type in self.models:
            self.prediction_models[model_type] = PredictionModel(model_type)
        
        # Prediction cache
        self.prediction_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        log_event("predictor_initialized", {
            "vix_source": vix_source,
            "features": self.features,
            "models": self.models
        })
    
    def get_market_sentiment(self):
        """Get overall market sentiment indicators"""
        vix = self.data_provider.get_vix_data()
        economic_data = self.data_provider.get_economic_indicators()
        
        # Calculate sentiment score
        sentiment_score = 0
        
        # VIX interpretation (lower VIX = higher risk appetite)
        if vix < 20:
            sentiment_score += 0.3  # Low fear
        elif vix > 30:
            sentiment_score -= 0.3  # High fear
        
        # USD strength
        if economic_data['usd_index'] > 100:
            sentiment_score -= 0.1  # Strong USD (bearish for EUR/USD)
        else:
            sentiment_score += 0.1
        
        return {
            "vix": vix,
            "sentiment_score": sentiment_score,
            "economic_data": economic_data
        }
    
    def forecast_direction(self, pair="EUR/USD", timeframe="1H"):
        """Forecast price direction for a currency pair"""
        cache_key = f"{pair}_{timeframe}"
        
        # Check cache
        if cache_key in self.prediction_cache:
            cached_prediction, timestamp = self.prediction_cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_prediction
        
        try:
            # Get market data
            data = self.data_provider.get_forex_data(pair, timeframe, periods=200)
            data_with_indicators = self.data_provider.calculate_technical_indicators(data)
            
            # Get market sentiment
            sentiment = self.get_market_sentiment()
            
            # Get predictions from all models
            predictions = {}
            for model_name, model in self.prediction_models.items():
                pred = model.predict(data_with_indicators)
                predictions[model_name] = pred
            
            # Ensemble prediction (average of all models)
            if predictions:
                ensemble_pred = np.mean(list(predictions.values()))
            else:
                ensemble_pred = 0.5  # Neutral
            
            # Adjust for market sentiment
            final_pred = ensemble_pred + (sentiment["sentiment_score"] * 0.1)
            final_pred = max(0, min(1, final_pred))  # Clamp to [0, 1]
            
            # Convert to binary bias
            bias = 1 if final_pred > 0.5 else 0
            confidence = abs(final_pred - 0.5) * 2  # Convert to 0-1 confidence
            
            result = {
                "pair": pair,
                "bias": bias,
                "confidence": confidence,
                "probability": final_pred,
                "predictions": predictions,
                "sentiment": sentiment,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache result
            self.prediction_cache[cache_key] = (result, time.time())
            
            log_event("prediction_generated", {
                "pair": pair,
                "bias": "bullish" if bias else "bearish",
                "confidence": confidence,
                "probability": final_pred
            })
            
            return result
            
        except Exception as e:
            log_event("forecast_error", {"pair": pair, "error": str(e)})
            return {
                "pair": pair,
                "bias": 0,
                "confidence": 0.0,
                "probability": 0.5,
                "error": str(e)
            }
    
    def retrain_models(self, pair="EUR/USD"):
        """Retrain prediction models with latest data"""
        log_event("model_retraining_start", {"pair": pair})
        send_system_alert("Starting model retraining...")
        
        try:
            # Get extended historical data for training
            data = self.data_provider.get_forex_data(pair, "1H", periods=1000)
            data_with_indicators = self.data_provider.calculate_technical_indicators(data)
            
            # Train all models
            success_count = 0
            for model_name, model in self.prediction_models.items():
                if model.train(data_with_indicators):
                    success_count += 1
                    log_event("model_retrained", {"model": model_name, "pair": pair})
            
            log_event("model_retraining_complete", {
                "pair": pair,
                "successful_models": success_count,
                "total_models": len(self.prediction_models)
            })
            
            send_system_alert(f"Model retraining complete. {success_count}/{len(self.prediction_models)} models updated.")
            
            return success_count > 0
            
        except Exception as e:
            log_event("model_retraining_error", {"error": str(e)})
            send_system_alert(f"Model retraining failed: {str(e)}")
            return False
    
    def run(self):
        """Main run loop for the predictor agent"""
        log_event("predictor_started", {})
        send_system_alert("Predictor Agent started")
        
        last_retrain = datetime.utcnow()
        retrain_interval = timedelta(days=7)  # Retrain weekly
        
        while True:
            try:
                # Generate predictions for main pairs
                pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
                
                for pair in pairs:
                    prediction = self.forecast_direction(pair)
                    
                    if prediction.get("confidence", 0) > 0.7:  # High confidence prediction
                        bias_text = "Bullish" if prediction["bias"] else "Bearish"
                        send_system_alert(
                            f"📊 High confidence prediction: {pair} {bias_text} "
                            f"(confidence: {prediction['confidence']:.2f})"
                        )
                
                # Check if it's time to retrain models
                if datetime.utcnow() - last_retrain > retrain_interval:
                    self.retrain_models()
                    last_retrain = datetime.utcnow()
                
                # Sleep for 15 minutes
                time.sleep(900)
                
            except Exception as e:
                log_event("predictor_error", {"error": str(e)})
                send_system_alert(f"Predictor error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    predictor = Predictor(
        vix_source="alphavantage",
        features=["london_open_volume", "yield_spread", "usd_index_delta"],
        models=["lightgbm", "random_forest"]
    )
    
    # Test prediction
    result = predictor.forecast_direction("EUR/USD")
    print(f"Prediction result: {result}")
    
    # Start main loop
    predictor.run()