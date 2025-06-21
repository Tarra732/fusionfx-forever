# core/utils/trading_halt.py

import os
import time

HALT_FILE_PATH = "/tmp/fusionfx_trading_halt.flag"

class TradingHaltManager:
    def __init__(self, file_path=HALT_FILE_PATH):
        self.file_path = file_path

    def activate(self, reason="unspecified"):
        with open(self.file_path, "w") as f:
            f.write(f"{reason} | {int(time.time())}")
        print(f"[TradingHalt] HALT ACTIVATED: {reason}")

    def deactivate(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            print("[TradingHalt] ✅ HALT DEACTIVATED")

    def is_halted(self):
        return os.path.exists(self.file_path)

    def get_reason(self):
        if self.is_halted():
            with open(self.file_path, "r") as f:
                return f.read().strip()
        return "No halt"

    def deactivate_if_clear(self):
        # Optional logic for timed halts
        if self.is_halted():
            reason_time = self.get_reason().split("|")[-1]
            try:
                elapsed = time.time() - int(reason_time)
                if elapsed > 60 * 60 * 6:  # 6-hour automatic clearance
                    self.deactivate()
                    print("[TradingHalt] Auto-clear triggered after 6 hours")
            except Exception:
                pass  # Ignore malformed file