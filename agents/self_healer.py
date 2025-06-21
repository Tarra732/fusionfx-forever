# agents/self_healer.py

import os, time, psutil
from utils.alerts import send_telegram, send_sms
from utils.crypto import rotate_keys

THRESHOLDS = {
    "memory": 85,   # in percent
    "latency": 250, # in ms
    "drawdown": 15  # in percent
}

QUANTUM_ROTATION_INTERVAL = 90 * 24 * 60 * 60  # 90 days

def get_system_latency():
    # Simulated ping logic
    return 180  # replace with real latency measurement

def get_drawdown():
    # Placeholder: replace with real portfolio drawdown logic
    return 9.2

def should_trigger_killswitch(drawdown, consecutive_losses):
    return drawdown >= THRESHOLDS["drawdown"] or consecutive_losses >= 7

def monitor_system():
    memory = psutil.virtual_memory().percent
    latency = get_system_latency()
    drawdown = get_drawdown()
    
    print(f"[SelfHealer] mem={memory}%, latency={latency}ms, dd={drawdown}%")

    if memory > THRESHOLDS["memory"]:
        send_telegram("⚠️ High memory usage! Restarting agents.")
        restart_agents()

    if latency > THRESHOLDS["latency"]:
        send_telegram("⚠️ High latency detected. Triggering fallback mode.")
        os.system("python agents/cloud_nomad.py")

    if should_trigger_killswitch(drawdown, get_consecutive_losses()):
        send_sms("🚨 KILL SWITCH ACTIVATED: System drawdown exceeded threshold.")
        halt_trading()

def restart_agents():
    os.system("supervisorctl restart all")

def halt_trading():
    os.system("touch /tmp/trading_halted.flag")

def get_consecutive_losses():
    # Read loss streak from logs or db
    return 3

def maybe_rotate_keys():
    last_rotated = float(open("keys/last_rotation.txt").read().strip())
    now = time.time()
    if now - last_rotated >= QUANTUM_ROTATION_INTERVAL:
        rotate_keys(algorithm="kyber1024", shard_locs=["Frankfurt", "Singapore", "Virginia"])
        with open("keys/last_rotation.txt", "w") as f:
            f.write(str(now))
        send_telegram("🔐 Quantum keys rotated successfully.")

if __name__ == "__main__":
    while True:
        monitor_system()
        maybe_rotate_keys()
        time.sleep(300)  # check every 5 mins