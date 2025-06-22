# agents/utils/logger.py

import json
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def log_event(event_type, data, level="INFO"):
    """Log events to both file and console"""
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "level": level,
        "data": data
    }
    
    # Log to file
    log_file = LOG_DIR / f"fusionfx_{datetime.utcnow().strftime('%Y%m%d')}.log"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Log to console
    print(f"[{timestamp}] {level} - {event_type}: {json.dumps(data)}")

def log_trade(trade_data):
    """Specialized logging for trade events"""
    log_event("trade_executed", trade_data, "TRADE")

def log_error(error_msg, context=None):
    """Log errors with context"""
    error_data = {"error": str(error_msg)}
    if context:
        error_data["context"] = context
    log_event("error", error_data, "ERROR")

def log_performance(metrics):
    """Log performance metrics"""
    log_event("performance_metrics", metrics, "METRICS")