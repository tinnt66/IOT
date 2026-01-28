"""
Authentication and Security Middleware for Flask
"""

from .config import settings


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key from request header
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    return api_key == settings.api_key
