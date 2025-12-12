"""
Security utilities for handling sensitive data.
"""

import os
import hashlib
import hmac
from typing import Optional
from django.conf import settings
from cryptography.fernet import Fernet
import base64


class SecurityUtils:
    """Security utility class for handling sensitive operations."""
    
    @staticmethod
    def generate_fernet_key() -> str:
        """Generate a Fernet key for encryption."""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def get_fernet_key() -> bytes:
        """
        Get Fernet key from environment or generate one.
        Store FERNET_KEY in your .env file.
        """
        key = os.getenv('FERNET_KEY')
        if not key:
            # Generate a key if not found (for development only)
            key = SecurityUtils.generate_fernet_key()
            os.environ['FERNET_KEY'] = key
        return key.encode()
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt sensitive data."""
        fernet = Fernet(SecurityUtils.get_fernet_key())
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data."""
        try:
            fernet = Fernet(SecurityUtils.get_fernet_key())
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            from .utils import ErrorHandler
            ErrorHandler.log_exception(e, {"operation": "decrypt_data"})
            return None
    
    @staticmethod
    def hash_api_key(api_key: str, salt: Optional[str] = None) -> str:
        """Hash API keys for secure storage."""
        if salt is None:
            salt = settings.SECRET_KEY
        
        # Use HMAC for keyed hashing
        return hmac.new(
            salt.encode(),
            api_key.encode(),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def mask_string(value: str, visible_chars: int = 4) -> str:
        """Mask sensitive strings (like API keys) for logging."""
        if len(value) <= visible_chars * 2:
            return "*" * len(value)
        
        return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]
    
    @staticmethod
    def sanitize_log_data(data: dict) -> dict:
        """Remove or mask sensitive data from logs."""
        sensitive_keys = ['password', 'api_key', 'secret', 'token', 'key', 'auth']
        sanitized = data.copy()
        
        for key in sanitized.keys():
            key_lower = key.lower()
            for sensitive in sensitive_keys:
                if sensitive in key_lower:
                    if isinstance(sanitized[key], str):
                        sanitized[key] = SecurityUtils.mask_string(sanitized[key])
                    else:
                        sanitized[key] = '[REDACTED]'
        
        return sanitized


class EnvironmentValidator:
    """Validate environment configuration."""
    
    @staticmethod
    def check_required_settings():
        """Check that all required settings are configured."""
        required_settings = [
            'DJANGO_SECRET_KEY',
            'DATABASE_URL',
        ]
        
        missing = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing.append(setting)
        
        if missing:
            raise EnvironmentError(
                f"Missing required settings: {', '.join(missing)}. "
                f"Please check your .env file."
            )
    
    @staticmethod
    def check_security_settings():
        """Check security settings for production."""
        if not settings.DEBUG:
            warnings = []
            
            if settings.SECRET_KEY == 'django-insecure-change-me-in-production':
                warnings.append("Using default secret key in production!")
            
            if not settings.SECURE_SSL_REDIRECT:
                warnings.append("SSL redirect is disabled")
            
            if not settings.SESSION_COOKIE_SECURE:
                warnings.append("Session cookies are not secure")
            
            if warnings:
                from .utils import logger
                for warning in warnings:
                    logger.warning(f"Security warning: {warning}")
    
    @staticmethod
    def validate_api_keys():
        """Validate external API keys."""
        api_keys = {
            'YELP_API_KEY': settings.YELP_API_KEY,
            'GOOGLE_PLACES_API_KEY': settings.GOOGLE_PLACES_API_KEY,
        }
        
        missing = [name for name, key in api_keys.items() if not key]
        
        if missing:
            from .utils import logger
            logger.warning(f"Missing API keys: {', '.join(missing)}")
            return False
        
        return True