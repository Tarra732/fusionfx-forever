# fusionfx-forever/agents/self_healer.py

import time
import random
import subprocess
import smtplib
from core.utils.health import is_overloaded, get_system_health, print_health
from core.utils.alerts import notify_telegram, notify_sms
from core.utils.crypto import rotate_keys_kyber

drawdown_threshold = 0.15  # 15%
max_latency_ms = 250
resource_thresholds = {"cpu": 85, "memory": 85, "disk": 90}
last_key_rotation = time.time()

def get_drawdown():
    # Placeholder - connect to actual portfolio PnL tracking
    return random.uniform(0.01, 0.2)

def get_latency():
    # Simulate latency test (replace with ZeroMQ ping test)
    return random.randint(100, 400)

def restart_agent(agent_name):
    subprocess.run(["docker", "restart", agent_name])
    notify_telegram(f"🔁 Restarted {agent_name} due to overload or failure.")

def handle_failures():
    overloaded = is_overloaded(resource_thresholds)
    latency = get_latency()
    drawdown = get_drawdown()

    print_health()

    if overloaded:
        notify_telegram("⚠️ Resource overload detected.")
        restart_agent("strategist")

    if latency > max_latency_ms:
        notify_telegram(f"⚠️ Latency exceeded: {latency}ms")
        restart_agent("execution_agent")

    if drawdown > drawdown_threshold:
        notify_telegram(f"🚨 Max drawdown breached: {drawdown:.2%}")
        notify_sms("🚨 Drawdown triggered. Manual review recommended.")
        subprocess.run(["docker", "stop", "fusion_agent"])

def maybe_rotate_keys():
    global last_key_rotation
    days_since_rotation = (time.time() - last_key_rotation) / 86400

    if days_since_rotation > 90:
        rotate_keys_kyber(["Frankfurt", "Singapore", "Virginia"])
        notify_telegram("🔐 Kyber1024 keys rotated.")
        last_key_rotation = time.time()

if __name__ == "__main__":
    print("[👨‍⚕️] Self-Healer started")
    while True:
        try:
            handle_failures()
            maybe_rotate_keys()
        except Exception as e:
            notify_telegram(f"❌ Self-healer exception: {str(e)}")
        time.sleep(1800)  # Run every 30 minutes