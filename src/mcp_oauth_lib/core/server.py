"""Main OAuth server implementation for MCP."""

import logging
import time
from typing import Any

from fastmcp import FastMCP
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from ..auth.middleware import OAuthAuthenticationMiddleware
from ..providers.base import BaseOAuthProvider
from .config import OAuthConfig
from .flow import OAuthFlow

logger = logging.getLogger(__name__)


class MCPOAuthServer:
    """OAuth 2.0 authorization server for MCP with provider abstraction."""

    def __init__(
        self,
        config: OAuthConfig,
        provider: BaseOAuthProvider,
        mcp_app: FastMCP | None = None,
    ):
        """Initialize the OAuth server.

        Args:
            config: OAuth server configuration
            provider: OAuth provider implementation
            mcp_app: Optional existing FastMCP app to extend
        """
        self.config = config
        self.provider = provider
        self.oauth_flow = OAuthFlow(config, provider)
        self.mcp_app = mcp_app

        logger.info(
            f"Initialized OAuth server for provider: {provider.config.provider_name}"
        )

    def register_oauth_endpoints(self, mcp_app: FastMCP) -> None:
        """Register OAuth endpoints with FastMCP application.

        Args:
            mcp_app: FastMCP application to register endpoints with
        """

        # OAuth metadata discovery endpoint
        @mcp_app.custom_route(
            "/.well-known/oauth-authorization-server", methods=["GET", "OPTIONS"]
        )
        async def oauth_metadata(request: Request) -> JSONResponse:
            """OAuth authorization server metadata discovery endpoint."""
            logger.debug("=== METADATA REQUEST ===")
            logger.debug(f"Method: {request.method}")
            logger.debug(f"URL: {request.url}")

            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                metadata = self.oauth_flow.get_oauth_metadata()
                logger.debug(
                    f"Returning OAuth metadata for provider: {self.provider.config.provider_name}"
                )

                return self._create_cors_response(metadata)
            except Exception as e:
                logger.error(f"Failed to get OAuth metadata: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to get OAuth metadata"
                )

        # Authorization initiation endpoint
        @mcp_app.custom_route("/auth/authorize", methods=["GET"])
        async def authorize(request: Request) -> RedirectResponse:
            """Initiate OAuth authorization flow."""
            logger.debug("🚨 AUTHORIZATION ENDPOINT CALLED! 🚨")
            logger.debug(f"Method: {request.method}")
            logger.debug(f"URL: {request.url}")
            logger.debug(f"Query params: {dict(request.query_params)}")

            # Extract user_id from query parameters
            user_id = request.query_params.get("user_id")

            return await self.oauth_flow.initiate_authorization(request, user_id)

        # Authorization callback endpoint
        @mcp_app.custom_route("/auth/callback", methods=["GET"])
        async def callback(request: Request) -> JSONResponse:
            """Handle OAuth authorization callback."""
            # Extract parameters from query string
            code = request.query_params.get("code")
            state = request.query_params.get("state")
            error = request.query_params.get("error")

            if not code or not state:
                raise HTTPException(
                    status_code=400, detail="Missing required parameters"
                )

            return await self.oauth_flow.handle_callback(request, code, state, error)

        # Token exchange endpoint
        @mcp_app.custom_route("/token", methods=["POST", "OPTIONS"])
        async def token_exchange(request: Request) -> JSONResponse:
            """Exchange authorization code for access tokens."""
            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                # Parse request body
                code, code_verifier = await self._parse_token_request(request)

                if not code:
                    raise HTTPException(
                        status_code=400, detail="Missing required parameter: code"
                    )

                logger.debug(
                    f"Token exchange request - code: {code[:10]}..., code_verifier: {'provided' if code_verifier else 'missing'}"
                )

                response = await self.oauth_flow.exchange_code_for_tokens(
                    code, code_verifier
                )

                # Add CORS headers
                if hasattr(response, "headers"):
                    self._add_cors_headers(response.headers)

                return response

            except Exception as e:
                logger.error(f"Token exchange endpoint error: {e}")
                return self._create_cors_response(
                    {"error": "server_error", "error_description": str(e)},
                    status_code=500,
                )

        # Token refresh endpoint (if provider supports it)
        @mcp_app.custom_route("/oauth/refresh", methods=["POST"])
        async def refresh_token(request: Request) -> JSONResponse:
            """Refresh OAuth access token."""
            refresh_token_value = await self._extract_refresh_token(request)
            user_id = request.query_params.get("user_id")

            if not refresh_token_value:
                raise HTTPException(
                    status_code=400, detail="Missing refresh_token parameter"
                )

            try:
                success, token_data = await self.provider.refresh_access_token(
                    refresh_token_value
                )

                if not success or not token_data:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "refresh_failed",
                            "error_description": "Failed to refresh access token",
                        },
                    )

                return JSONResponse(content=token_data)

            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "refresh_error", "error_description": str(e)},
                )

        # Token introspection endpoint (if provider supports it)
        @mcp_app.custom_route("/oauth/introspect", methods=["POST"])
        async def introspect_token(request: Request) -> JSONResponse:
            """Introspect OAuth token."""
            token = await self._extract_token_parameter(request, "token")

            if not token:
                raise HTTPException(status_code=400, detail="Missing token parameter")

            try:
                token_info = await self.provider.introspect_token(token)

                if token_info is None:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "invalid_token",
                            "error_description": "Token is invalid or expired",
                        },
                    )

                return JSONResponse(content=token_info)

            except Exception as e:
                logger.error(f"Token introspection failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "introspection_error",
                        "error_description": str(e),
                    },
                )

        # Token revocation endpoint (if provider supports it)
        @mcp_app.custom_route("/oauth/revoke", methods=["POST"])
        async def revoke_token(request: Request) -> JSONResponse:
            """Revoke OAuth token."""
            token = await self._extract_token_parameter(request, "token")
            user_id = request.query_params.get("user_id")

            if not token:
                raise HTTPException(status_code=400, detail="Missing token parameter")

            try:
                success = await self.provider.revoke_token(token)

                if not success:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "revocation_failed",
                            "error_description": "Failed to revoke token",
                        },
                    )

                return JSONResponse(
                    content={
                        "status": "success",
                        "message": "Token revoked successfully",
                    }
                )

            except Exception as e:
                logger.error(f"Token revocation failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "revocation_error", "error_description": str(e)},
                )

        # OAuth protected resource metadata endpoints
        @mcp_app.custom_route(
            "/.well-known/oauth-protected-resource", methods=["GET", "OPTIONS"]
        )
        async def oauth_protected_resource(request: Request) -> JSONResponse:
            """OAuth protected resource metadata."""
            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                base_url = self.config.get_base_url()
                protected_resource_metadata = {
                    "resource": base_url,
                    "authorization_servers": [base_url],
                    "scopes_supported": self.provider.get_supported_scopes(),
                    "bearer_methods_supported": ["header"],
                    "resource_documentation": f"{base_url}/docs",
                }
                return self._create_cors_response(protected_resource_metadata)
            except Exception as e:
                logger.error(f"Failed to get OAuth protected resource metadata: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get OAuth protected resource metadata",
                )

        # MCP-specific OAuth protected resource endpoint
        @mcp_app.custom_route(
            "/.well-known/oauth-protected-resource/mcp", methods=["GET", "OPTIONS"]
        )
        async def mcp_oauth_protected_resource(request: Request) -> JSONResponse:
            """MCP-specific OAuth protected resource metadata."""
            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                base_url = self.config.get_base_url()
                mcp_metadata = {
                    "mcpVersion": self.config.mcp_version,
                    "serverName": self.config.server_name,
                    "serverVersion": self.config.server_version,
                    "protocolVersion": "1.0",
                    "resource": base_url,
                    "authorization_servers": [base_url],
                    "scopes_required": ["data.records:read"],
                    "scopes_supported": self.provider.get_supported_scopes(),
                    "bearer_methods_supported": ["header"],
                    "oauth_flows_supported": ["authorization_code"],
                    "registration_endpoint": self.config.get_registration_endpoint(),
                    "authorization_endpoint": self.config.get_authorization_endpoint(),
                    "token_endpoint": self.config.get_token_endpoint(),
                    "mcp_endpoints": {
                        "tools": f"{base_url}/mcp/tools",
                        "resources": f"{base_url}/mcp/resources",
                    },
                }
                return self._create_cors_response(mcp_metadata)
            except Exception as e:
                logger.error(
                    f"Failed to get MCP OAuth protected resource metadata: {e}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get MCP OAuth protected resource metadata",
                )

        # OAuth Authorization Server metadata with MCP extension
        @mcp_app.custom_route(
            "/.well-known/oauth-authorization-server/mcp", methods=["GET", "OPTIONS"]
        )
        async def oauth_authorization_server_mcp(request: Request) -> JSONResponse:
            """OAuth authorization server metadata with MCP extensions."""
            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                metadata = self.oauth_flow.get_oauth_metadata()
                # Add MCP-specific extensions
                metadata.update(
                    {
                        "mcp_version": self.config.mcp_version,
                        "mcp_extensions": {
                            "automatic_flow": True,
                            "bearer_token_auth": True,
                            "pkce_required": self.config.enable_pkce,
                        },
                    }
                )
                return self._create_cors_response(metadata)
            except Exception as e:
                logger.error(
                    f"Failed to get MCP OAuth authorization server metadata: {e}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get MCP OAuth authorization server metadata",
                )

        # Dynamic Client Registration endpoint
        @mcp_app.custom_route("/oauth/register", methods=["POST", "OPTIONS"])
        async def register_client(request: Request) -> JSONResponse:
            """Register a new OAuth client dynamically."""
            # Handle CORS preflight
            if request.method == "OPTIONS":
                return self._create_cors_response({})

            try:
                # Parse the registration request
                registration_request = {}
                try:
                    registration_request = await request.json()
                except Exception:
                    logger.debug("No JSON body in registration request, using defaults")

                logger.debug(f"Client registration request: {registration_request}")

                # Extract redirect URIs from request or use defaults
                redirect_uris = registration_request.get("redirect_uris", [])
                if not redirect_uris:
                    # Provide default redirect URIs for MCP clients
                    base_url = self.config.get_base_url()
                    redirect_uris = [
                        f"{base_url}/auth/callback",
                        "http://localhost:3000/callback",  # Common development URI
                        "urn:ietf:wg:oauth:2.0:oob",  # Out-of-band flow
                    ]

                # Generate unique client credentials
                client_id = f"mcp-client-{int(time.time())}"
                client_secret = f"mcp-secret-{int(time.time())}"

                # Create client registration response according to RFC 7591
                client_info = {
                    # Required fields
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": redirect_uris,
                    # Grant types and response types
                    "grant_types": registration_request.get(
                        "grant_types", ["authorization_code", "refresh_token"]
                    ),
                    "response_types": registration_request.get(
                        "response_types", ["code"]
                    ),
                    # Client metadata
                    "client_name": registration_request.get(
                        "client_name", "MCP OAuth Client"
                    ),
                    "scope": " ".join(self.provider.get_supported_scopes()),
                    # Authentication method
                    "token_endpoint_auth_method": registration_request.get(
                        "token_endpoint_auth_method", "client_secret_basic"
                    ),
                    # OAuth endpoints
                    "authorization_endpoint": self.config.get_authorization_endpoint(),
                    "token_endpoint": self.config.get_token_endpoint(),
                    "registration_endpoint": self.config.get_registration_endpoint(),
                    # Client registration metadata
                    "client_id_issued_at": int(time.time()),
                    "client_secret_expires_at": 0,  # Never expires
                    # MCP-specific metadata
                    "mcp_version": self.config.mcp_version,
                    "server_name": self.config.server_name,
                }

                # Add optional fields if provided in request
                if "client_uri" in registration_request:
                    client_info["client_uri"] = registration_request["client_uri"]
                if "logo_uri" in registration_request:
                    client_info["logo_uri"] = registration_request["logo_uri"]
                if "tos_uri" in registration_request:
                    client_info["tos_uri"] = registration_request["tos_uri"]
                if "policy_uri" in registration_request:
                    client_info["policy_uri"] = registration_request["policy_uri"]

                logger.info(f"Registered new OAuth client: {client_id}")
                return self._create_cors_response(client_info)

            except Exception as e:
                logger.error(f"Failed to register OAuth client: {e}")
                return self._create_cors_response(
                    {"error": "invalid_client_metadata", "error_description": str(e)},
                    status_code=400,
                )

        # OAuth app info endpoint
        @mcp_app.custom_route("/oauth/app", methods=["GET"])
        async def oauth_app_info(request: Request) -> JSONResponse:
            """OAuth app information endpoint for MCP."""
            try:
                app_info = {
                    "name": self.config.server_name,
                    "version": self.config.server_version,
                    "provider": self.provider.config.provider_name,
                    "authorization_endpoint": self.config.get_authorization_endpoint(),
                    "token_endpoint": self.config.get_token_endpoint(),
                    "scopes": self.provider.get_supported_scopes(),
                    "pkce_supported": self.config.enable_pkce,
                }
                return JSONResponse(content=app_info)
            except Exception as e:
                logger.error(f"Failed to get OAuth app info: {e}")
                raise HTTPException(
                    status_code=500, detail="Failed to get OAuth app info"
                )

        logger.info(
            f"OAuth endpoints registered successfully for provider: {self.provider.config.provider_name}"
        )

    def get_authentication_middleware(self) -> OAuthAuthenticationMiddleware:
        """Get OAuth authentication middleware.

        Returns:
            Configured authentication middleware
        """
        return OAuthAuthenticationMiddleware(
            app=None,  # Will be set when middleware is applied
            oauth_base_url=self.config.get_base_url(),
        )

    def cleanup_expired_entries(self) -> None:
        """Clean up expired OAuth flow entries."""
        self.oauth_flow.cleanup_expired_entries()

    async def _parse_token_request(
        self, request: Request
    ) -> tuple[str | None, str | None]:
        """Parse token exchange request body."""
        content_type = request.headers.get("content-type", "")

        if "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            code = form_data.get("code")
            code_verifier = form_data.get("code_verifier")
        elif "application/json" in content_type:
            json_data = await request.json()
            code = json_data.get("code")
            code_verifier = json_data.get("code_verifier")
        else:
            # Try query parameters as fallback
            code = request.query_params.get("code")
            code_verifier = request.query_params.get("code_verifier")

        return code, code_verifier

    async def _extract_refresh_token(self, request: Request) -> str | None:
        """Extract refresh token from request."""
        # Try query parameters first
        refresh_token = request.query_params.get("refresh_token")
        if refresh_token:
            return refresh_token

        # Try form data
        try:
            form_data = await request.form()
            return form_data.get("refresh_token")
        except:
            pass

        # Try JSON body
        try:
            json_data = await request.json()
            return json_data.get("refresh_token")
        except:
            pass

        return None

    async def _extract_token_parameter(
        self, request: Request, param_name: str
    ) -> str | None:
        """Extract token parameter from request."""
        # Try query parameters first
        token = request.query_params.get(param_name)
        if token:
            return token

        # Try form data
        try:
            form_data = await request.form()
            return form_data.get(param_name)
        except:
            pass

        # Try JSON body
        try:
            json_data = await request.json()
            return json_data.get(param_name)
        except:
            pass

        return None

    def _create_cors_response(
        self, content: dict[str, Any], status_code: int = 200
    ) -> JSONResponse:
        """Create JSON response with CORS headers."""
        response = JSONResponse(content=content, status_code=status_code)
        self._add_cors_headers(response.headers)
        return response

    def _add_cors_headers(self, headers: dict[str, str]) -> None:
        """Add CORS headers to response."""
        headers["Access-Control-Allow-Origin"] = ", ".join(self.config.cors_origins)
        headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_headers)
