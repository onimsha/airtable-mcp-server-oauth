"""Authentication utility functions."""

from typing import Optional


def extract_bearer_token(authorization_header: str) -> Optional[str]:
    """Extract bearer token from Authorization header.
    
    Args:
        authorization_header: The Authorization header value
        
    Returns:
        The extracted token or None if invalid format
    """
    if not authorization_header:
        return None
    
    parts = authorization_header.split(' ', 1)
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]