"""ASGI middleware for OAuth authentication."""

import logging
from typing import List, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

from .context import AuthContext
from .utils import extract_bearer_token

logger = logging.getLogger(__name__)


class OAuthAuthenticationMiddleware:
    """ASGI middleware to handle OAuth authentication for MCP requests."""
    
    def __init__(self, app, skip_paths: Optional[List[str]] = None, oauth_base_url: Optional[str] = None):
        """Initialize OAuth authentication middleware.
        
        Args:
            app: The ASGI application
            skip_paths: List of path prefixes to skip authentication for
            oauth_base_url: Base URL for OAuth endpoints in error responses
        """
        self.app = app
        self.skip_paths = skip_paths or [
            '/auth/',
            '/oauth/', 
            '/.well-known/',
            '/token',
            '/health',
            '/docs',
            '/openapi.json'
        ]
        self.oauth_base_url = oauth_base_url
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object to examine path and headers
        request = Request(scope, receive)
        
        # Skip authentication for OAuth endpoints and other specified paths
        path = request.url.path
        if any(path.startswith(skip_path) for skip_path in self.skip_paths):
            await self.app(scope, receive, send)
            return
        
        # Extract authorization header
        auth_header = request.headers.get('Authorization')
        
        # If no authorization header, return 401 to trigger OAuth flow
        if not auth_header:
            logger.debug(f"No Authorization header for path: {path}")
            await self._send_unauthorized_response(request, scope, receive, send)
            return
        
        # Extract bearer token
        access_token = extract_bearer_token(auth_header)
        if not access_token:
            logger.debug(f"Invalid Authorization header format for path: {path}")
            await self._send_invalid_token_response(scope, receive, send)
            return
        
        # Set token in context for downstream handlers
        AuthContext.set_access_token(access_token)
        logger.debug(f"Set access token in context for path: {path}")
        
        # Continue with the request
        await self.app(scope, receive, send)
    
    async def _send_unauthorized_response(self, request: Request, scope, receive, send):
        """Send 401 Unauthorized response with OAuth information."""
        base_url = self.oauth_base_url or f"{request.url.scheme}://{request.url.netloc}"
        
        response = JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "error_description": "Access token is required. Please authenticate using OAuth 2.0.",
                "oauth_info": {
                    "authorization_endpoint": f"{base_url}/auth/authorize",
                    "token_endpoint": f"{base_url}/token",
                    "metadata_endpoint": f"{base_url}/.well-known/oauth-authorization-server"
                }
            },
            headers={
                "WWW-Authenticate": f'Bearer realm="OAuth MCP Server", authorization_uri="{base_url}/auth/authorize", token_uri="{base_url}/token"'
            }
        )
        await response(scope, receive, send)
    
    async def _send_invalid_token_response(self, scope, receive, send):
        """Send 401 response for invalid token format."""
        response = JSONResponse(
            status_code=401,
            content={
                "error": "invalid_token",
                "error_description": "Invalid Authorization header format. Expected 'Bearer <token>'"
            },
            headers={
                "WWW-Authenticate": 'Bearer realm="OAuth MCP Server", error="invalid_token", error_description="Invalid Authorization header format"'
            }
        )
        await response(scope, receive, send)