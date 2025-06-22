# core/utils/crypto.py

import hashlib
import base64
import os
import json
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("[WARNING] cryptography not available. Install for encryption features.")

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False
    print("[WARNING] eth_account not available. Install for blockchain features.")

# --- Emergency profit encryption ---

def generate_encryption_key():
    """Generate a new encryption key"""
    if CRYPTOGRAPHY_AVAILABLE:
        return Fernet.generate_key().decode()
    else:
        # Fallback to simple base64 encoding (not secure)
        return base64.b64encode(os.urandom(32)).decode()

def get_or_create_master_key():
    """Get or create the master encryption key"""
    key_file = Path("data/master.key")
    key_file.parent.mkdir(exist_ok=True)
    
    if key_file.exists():
        with open(key_file, 'r') as f:
            return f.read().strip()
    else:
        key = generate_encryption_key()
        with open(key_file, 'w') as f:
            f.write(key)
        # Set restrictive permissions
        os.chmod(key_file, 0o600)
        return key

def encrypt_data(data, key=None):
    """Encrypt data using Fernet encryption"""
    if not CRYPTOGRAPHY_AVAILABLE:
        # Fallback to simple base64 encoding (not secure)
        return base64.b64encode(json.dumps(data).encode()).decode()
    
    if key is None:
        key = get_or_create_master_key()
    
    fernet = Fernet(key.encode())
    serialized = json.dumps(data).encode()
    return fernet.encrypt(serialized)

def decrypt_data(encrypted_data, key=None):
    """Decrypt data using Fernet encryption"""
    if not CRYPTOGRAPHY_AVAILABLE:
        # Fallback from base64 encoding
        try:
            return json.loads(base64.b64decode(encrypted_data).decode())
        except:
            return None
    
    if key is None:
        key = get_or_create_master_key()
    
    try:
        fernet = Fernet(key.encode())
        decrypted = fernet.decrypt(encrypted_data).decode()
        return json.loads(decrypted)
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def encrypt_profit_data(data: dict, key: str = None) -> str:
    """Legacy function for profit data encryption"""
    return encrypt_data(data, key)

def decrypt_profit_data(encrypted: str, key: str = None) -> dict:
    """Legacy function for profit data decryption"""
    return decrypt_data(encrypted, key)

# --- MPC-compatible wallet formatting ---

def format_wallet_address(address: str) -> str:
    """Format wallet address for MPC compatibility"""
    if not address:
        return ""
    return address.lower().replace("0x", "mpc:0x")

def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address format"""
    if not address:
        return False
    
    # Remove 0x prefix if present
    addr = address.replace("0x", "").replace("mpc:", "")
    
    # Check if it's 40 hex characters
    if len(addr) != 40:
        return False
    
    try:
        int(addr, 16)
        return True
    except ValueError:
        return False

# --- Digital signature utils ---

def sign_message(message: str, private_key: str) -> str:
    """Sign a message with a private key"""
    if not ETH_ACCOUNT_AVAILABLE:
        # Fallback to simple hash
        return sha256(message + private_key)
    
    try:
        msg = encode_defunct(text=message)
        signed = Account.sign_message(msg, private_key=private_key)
        return signed.signature.hex()
    except Exception as e:
        print(f"Signing error: {e}")
        return sha256(message + private_key)

def recover_signer(message: str, signature: str) -> str:
    """Recover the signer address from a message and signature"""
    if not ETH_ACCOUNT_AVAILABLE:
        return "0x0000000000000000000000000000000000000000"
    
    try:
        msg = encode_defunct(text=message)
        return Account.recover_message(msg, signature=signature)
    except Exception as e:
        print(f"Recovery error: {e}")
        return "0x0000000000000000000000000000000000000000"

def generate_wallet():
    """Generate a new Ethereum wallet"""
    if not ETH_ACCOUNT_AVAILABLE:
        # Generate a mock wallet
        private_key = os.urandom(32).hex()
        address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
        return {"private_key": private_key, "address": address}
    
    try:
        account = Account.create()
        return {
            "private_key": account.privateKey.hex(),
            "address": account.address
        }
    except Exception as e:
        print(f"Wallet generation error: {e}")
        return None

# --- Hashing utilities ---

def sha256(data: str) -> str:
    """Calculate SHA256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()

def sha256_bytes(data: bytes) -> str:
    """Calculate SHA256 hash of bytes"""
    return hashlib.sha256(data).hexdigest()

def md5(data: str) -> str:
    """Calculate MD5 hash of data"""
    return hashlib.md5(data.encode()).hexdigest()

def base64_encode(data: str) -> str:
    """Base64 encode string data"""
    return base64.b64encode(data.encode()).decode()

def base64_decode(data: str) -> str:
    """Base64 decode string data"""
    try:
        return base64.b64decode(data.encode()).decode()
    except Exception as e:
        print(f"Base64 decode error: {e}")
        return ""

def base64_encode_bytes(data: bytes) -> str:
    """Base64 encode bytes data"""
    return base64.b64encode(data).decode()

def base64_decode_bytes(data: str) -> bytes:
    """Base64 decode to bytes"""
    try:
        return base64.b64decode(data.encode())
    except Exception as e:
        print(f"Base64 decode error: {e}")
        return b""

# --- Key derivation ---

def derive_key_from_password(password: str, salt: bytes = None) -> str:
    """Derive encryption key from password using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)
    
    # Use PBKDF2 for key derivation
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    
    if CRYPTOGRAPHY_AVAILABLE:
        # Convert to Fernet-compatible key
        return base64.urlsafe_b64encode(key).decode()
    else:
        return base64.b64encode(key).decode()

# --- Secure random generation ---

def generate_secure_random(length: int = 32) -> str:
    """Generate cryptographically secure random string"""
    return base64.urlsafe_b64encode(os.urandom(length)).decode()

def generate_nonce() -> str:
    """Generate a nonce for cryptographic operations"""
    return generate_secure_random(16)

# --- Data integrity ---

def calculate_checksum(data: str) -> str:
    """Calculate checksum for data integrity verification"""
    return sha256(data)

def verify_checksum(data: str, checksum: str) -> bool:
    """Verify data integrity using checksum"""
    return calculate_checksum(data) == checksum

# --- Secure storage helpers ---

def secure_store(data: dict, filename: str, password: str = None) -> bool:
    """Securely store data to file with encryption"""
    try:
        if password:
            key = derive_key_from_password(password)
            encrypted_data = encrypt_data(data, key)
        else:
            encrypted_data = encrypt_data(data)
        
        filepath = Path("data/secure") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        if isinstance(encrypted_data, bytes):
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
        else:
            with open(filepath, 'w') as f:
                f.write(encrypted_data)
        
        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        return True
        
    except Exception as e:
        print(f"Secure store error: {e}")
        return False

def secure_load(filename: str, password: str = None) -> dict:
    """Securely load data from encrypted file"""
    try:
        filepath = Path("data/secure") / filename
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
        except:
            with open(filepath, 'r') as f:
                encrypted_data = f.read()
        
        if password:
            key = derive_key_from_password(password)
            return decrypt_data(encrypted_data, key)
        else:
            return decrypt_data(encrypted_data)
            
    except Exception as e:
        print(f"Secure load error: {e}")
        return None