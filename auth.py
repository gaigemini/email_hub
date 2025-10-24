"""
Authentication - Static API Key
"""
from fastapi import HTTPException, status
import os

# Get API key from environment variable
STATIC_API_KEY = os.getenv("API_KEY", "")

if not STATIC_API_KEY:
    print("⚠️  WARNING: API_KEY not set in environment variables!")
    print("⚠️  Using default key for development only!")
    STATIC_API_KEY = "dev-api-key-change-this-in-production"


def verify_api_key(api_key: str) -> bool:
    """Verify API key against static key from environment"""
    if api_key != STATIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return True