# crypto.py

import hashlib
import base64
import os
from cryptography.fernet import Fernet
from eth_account import Account
from eth_account.messages import encode_defunct


# --- Emergency profit encryption ---

def generate_encryption_key():
    return Fernet.generate_key().decode()


def encrypt_profit_data(data: dict, key: str) -> str:
    fernet = Fernet(key.encode())
    serialized = str(data).encode()
    return fernet.encrypt(serialized).decode()


def decrypt_profit_data(encrypted: str, key: str) -> dict:
    fernet = Fernet(key.encode())
    decrypted = fernet.decrypt(encrypted.encode()).decode()
    return eval(decrypted)  # Assume controlled internal use only


# --- MPC-compatible wallet formatting ---

def format_wallet_address(address: str) -> str:
    return address.lower().replace("0x", "mpc:0x")


# --- Digital signature utils ---

def sign_message(message: str, private_key: str) -> str:
    msg = encode_defunct(text=message)
    signed = Account.sign_message(msg, private_key=private_key)
    return signed.signature.hex()


def recover_signer(message: str, signature: str) -> str:
    msg = encode_defunct(text=message)
    return Account.recover_message(msg, signature=signature)


# --- Hashing utilities ---

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def base64_encode(data: str) -> str:
    return base64.b64encode(data.encode()).decode()


def base64_decode(data: str) -> str:
    return base64.b64decode(data.encode()).decode()