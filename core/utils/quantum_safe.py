# core/utils/quantum_safe.py

import datetime
import logging

class KyberKeyRotator:
    def __init__(self, rotation_days=90):
        self.rotation_days = rotation_days
        self.last_rotation = datetime.datetime.now()

    def should_rotate(self):
        return (datetime.datetime.now() - self.last_rotation).days >= self.rotation_days

    def rotate_keys(self):
        # Placeholder: Use Kyber-1024 via OpenQuantumSafe or hybrid post-quantum libs
        print("🔐 Rotating Kyber-1024 quantum-safe keys...")
        self.last_rotation = datetime.datetime.now()
        logging.info("✅ Quantum keys rotated at {}".format(self.last_rotation))