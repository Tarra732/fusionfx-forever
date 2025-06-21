# run.py

import subprocess
import threading
from core.utils.heartbeat import start_heartbeat
from core.utils.alerts import send_telegram

AGENT_SCRIPTS = [
    "agents/news_sentinel.py",
    "agents/compliance.py",
    "agents/market_scanner.py",
    "agents/predictor.py",
    "agents/risk_kernel.py",
    "agents/fusion_agent.py",
    "agents/execution_agent.py",
    "agents/dao_governor.mjs",
    "agents/profit_manager.py",
    "agents/cloud_nomad.py",
    "agents/depin_manager.py",
    "core/meta_controller.py",
    "core/strategist_agent.py"
]

def launch_agent(script):
    try:
        if script.endswith(".mjs"):
            subprocess.Popen(["node", script])
        else:
            subprocess.Popen(["python", script])
        print(f"[+] Launched: {script}")
    except Exception as e:
        send_telegram(f"🚨 Agent launch failed: {script} - {e}")

def start_all_agents():
    for script in AGENT_SCRIPTS:
        threading.Thread(target=launch_agent, args=(script,), daemon=True).start()

if __name__ == "__main__":
    send_telegram("🚀 FusionFX Autonomous System Starting...")
    start_all_agents()
    start_heartbeat()