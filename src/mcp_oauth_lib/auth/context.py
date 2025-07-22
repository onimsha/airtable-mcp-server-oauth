"""Authentication context management for MCP OAuth flow."""

import logging
import threading
from contextvars import ContextVar

from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

# Context variable to store the current access token
_access_token_context: ContextVar[str | None] = ContextVar("access_token", default=None)

# Thread-local storage as fallback for FastMCP redirects
_thread_local = threading.local()


class AuthContext:
    """Authentication context manager for MCP requests."""

    @staticmethod
    def set_access_token(token: str) -> None:
        """Set the access token in the current context and thread-local storage."""
        _access_token_context.set(token)
        _thread_local.access_token = token
        logger.debug("Set access token in both context and thread-local storage")

    @staticmethod
    def get_access_token() -> str | None:
        """Get the access token from context or thread-local storage."""
        # Try context first
        token = _access_token_context.get()
        if token:
            return token

        # Fallback to thread-local storage for FastMCP redirects
        return getattr(_thread_local, "access_token", None)

    @staticmethod
    def require_access_token() -> str:
        """Get the access token from context, raising an exception if not present."""
        token = AuthContext.get_access_token()
        if not token:
            logger.error("No access token found in context or thread-local storage")
            raise HTTPException(
                status_code=401,
                detail="Access token required",
                headers={
                    "WWW-Authenticate": 'Bearer realm="OAuth API", error="invalid_token", error_description="Access token is required"'
                },
            )
        return token

    @staticmethod
    def clear_access_token() -> None:
        """Clear the access token from context and thread-local storage."""
        _access_token_context.set(None)
        if hasattr(_thread_local, "access_token"):
            delattr(_thread_local, "access_token")
        logger.debug("Cleared access token from context and thread-local storage")
