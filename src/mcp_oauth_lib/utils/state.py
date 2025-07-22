"""State management utilities for OAuth flow."""

import logging
import secrets
import time
from typing import Any

logger = logging.getLogger(__name__)


def generate_secure_state(length: int = 32) -> str:
    """Generate a secure random state string for CSRF protection.

    Args:
        length: Length of the state string (in URL-safe base64 characters)

    Returns:
        Secure random state string
    """
    return secrets.token_urlsafe(length)


def cleanup_expired_entries(
    storage: dict[str, dict[str, Any]], expiry_seconds: int
) -> int:
    """Clean up expired entries from a storage dictionary.

    Args:
        storage: Dictionary containing entries with 'created_at' timestamp
        expiry_seconds: Number of seconds after which entries expire

    Returns:
        Number of entries cleaned up
    """
    current_time = time.time()
    expired_keys = []

    for key, entry in storage.items():
        created_at = entry.get("created_at", 0)
        if current_time - created_at > expiry_seconds:
            expired_keys.append(key)

    for key in expired_keys:
        del storage[key]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

    return len(expired_keys)


def is_entry_expired(entry: dict[str, Any], expiry_seconds: int) -> bool:
    """Check if an entry is expired.

    Args:
        entry: Dictionary containing 'created_at' timestamp
        expiry_seconds: Number of seconds after which entries expire

    Returns:
        True if expired, False otherwise
    """
    created_at = entry.get("created_at", 0)
    return time.time() - created_at > expiry_seconds
