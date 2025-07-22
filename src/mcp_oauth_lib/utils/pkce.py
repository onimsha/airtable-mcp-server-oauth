"""PKCE (Proof Key for Code Exchange) utilities."""

import hashlib
import base64
import secrets
import string
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def generate_pkce_pair(method: str = "S256", length: int = 128, character_set: Optional[str] = None) -> Tuple[str, str]:
    """Generate a PKCE code verifier and code challenge pair.
    
    Args:
        method: Code challenge method ("S256" or "plain")
        length: Length of the code verifier (43-128 characters)
        character_set: Custom character set for code verifier (default: RFC 7636 compliant)
        
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    if length < 43 or length > 128:
        raise ValueError("Code verifier length must be between 43 and 128 characters")
    
    if character_set is None:
        # RFC 7636 compliant character set
        character_set = string.ascii_letters + string.digits + '-._~'
    
    # Generate code verifier
    code_verifier = ''.join(secrets.choice(character_set) for _ in range(length))
    
    # Generate code challenge
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    elif method == "plain":
        code_challenge = code_verifier
    else:
        raise ValueError(f"Unsupported PKCE method: {method}")
    
    return code_verifier, code_challenge


def generate_provider_compatible_pkce(provider_requirements: Dict[str, Any], method: str = "S256") -> Tuple[str, str]:
    """Generate PKCE pair compatible with specific provider requirements.
    
    Args:
        provider_requirements: Provider-specific PKCE requirements
        method: Code challenge method
        
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    character_set = provider_requirements.get('character_set')
    min_length = provider_requirements.get('min_length', 43)
    max_length = provider_requirements.get('max_length', 128)
    
    # Use max length for better security
    length = max_length
    
    return generate_pkce_pair(method, length, character_set)


def validate_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    """Validate PKCE code challenge against code verifier.
    
    Args:
        code_verifier: The code verifier from the client
        code_challenge: The original code challenge
        method: The challenge method (S256 or plain)
        
    Returns:
        True if PKCE validation succeeds, False otherwise
    """
    try:
        if method == "S256":
            # Compute SHA256 hash of code_verifier
            digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
            # Base64 URL-safe encode without padding
            computed_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
            return computed_challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        else:
            logger.error(f"Unsupported PKCE challenge method: {method}")
            return False
    except Exception as e:
        logger.error(f"PKCE validation error: {e}")
        return False


def validate_code_verifier_format(code_verifier: str, requirements: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """Validate code verifier format against requirements.
    
    Args:
        code_verifier: The code verifier to validate
        requirements: Optional provider-specific requirements
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if requirements is None:
        # RFC 7636 defaults
        requirements = {
            'min_length': 43,
            'max_length': 128,
            'character_set': string.ascii_letters + string.digits + '-._~'
        }
    
    # Check length
    min_length = requirements.get('min_length', 43)
    max_length = requirements.get('max_length', 128)
    
    if len(code_verifier) < min_length or len(code_verifier) > max_length:
        return False, f"Code verifier length must be between {min_length} and {max_length} characters (got {len(code_verifier)})"
    
    # Check character set
    character_set = requirements.get('character_set')
    if character_set:
        invalid_chars = [c for c in code_verifier if c not in character_set]
        if invalid_chars:
            return False, f"Code verifier contains invalid characters: {invalid_chars}"
    
    return True, None