"""MCP OAuth Library

A reusable OAuth 2.0 authorization server library for MCP (Model Context Protocol) servers.

This library provides:
- OAuth 2.0 Authorization Code Flow with PKCE support
- Dynamic Client Registration (RFC 7591)
- OAuth metadata discovery (RFC 8414)
- MCP-specific OAuth integration
- Provider-specific OAuth implementations
- Authentication middleware for FastMCP
"""

from .core.server import MCPOAuthServer
from .core.config import OAuthConfig, ProviderConfig
from .core.flow import OAuthFlow
from .auth.middleware import OAuthAuthenticationMiddleware
from .auth.context import AuthContext

__version__ = "0.1.0"
__all__ = [
    "MCPOAuthServer",
    "OAuthConfig", 
    "ProviderConfig",
    "OAuthFlow",
    "OAuthAuthenticationMiddleware",
    "AuthContext",
]