"""
Encryption utilities for passwords
"""
import os
from cryptography.fernet import Fernet, InvalidToken # --- CORRECTED IMPORT ---

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not set in the environment variables!")

# Initialize Fernet cipher
cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns it as a string."""
    if not data:
        return data
    encrypted_bytes = cipher.encrypt(data.encode())
    return encrypted_bytes.decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string and returns it as a string."""
    if not encrypted_data:
        return encrypted_data
    try:
        decrypted_bytes = cipher.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        print("❌ CRITICAL: Failed to decrypt data. Key may have changed or data is corrupt.")
        raise
    except Exception as e:
        print(f"❌ An unexpected error occurred during decryption: {e}")
        raise

