# fusionfx-forever/core/utils/health.py

import psutil
import time
import os

def get_system_health():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "net_io": psutil.net_io_counters()._asdict(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def is_overloaded(thresholds=None):
    if thresholds is None:
        thresholds = {
            "cpu": 85,
            "memory": 85,
            "disk": 90
        }
    
    health = get_system_health()
    return (
        health["cpu_percent"] > thresholds["cpu"] or
        health["memory_percent"] > thresholds["memory"] or
        health["disk_percent"] > thresholds["disk"]
    )

def print_health():
    health = get_system_health()
    print(f"[HEALTH] {health['timestamp']} | CPU: {health['cpu_percent']}% | RAM: {health['memory_percent']}% | Disk: {health['disk_percent']}%")