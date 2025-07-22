"""OAuth flow implementation with dual PKCE validation."""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException

from ..providers.base import BaseOAuthProvider
from ..utils.pkce import generate_provider_compatible_pkce, validate_pkce, validate_code_verifier_format
from ..utils.state import generate_secure_state, is_entry_expired, cleanup_expired_entries
from .config import OAuthConfig

logger = logging.getLogger(__name__)


class OAuthFlow:
    """OAuth 2.0 authorization flow with dual PKCE validation."""
    
    def __init__(self, config: OAuthConfig, provider: BaseOAuthProvider):
        """Initialize OAuth flow.
        
        Args:
            config: OAuth server configuration
            provider: OAuth provider implementation
        """
        self.config = config
        self.provider = provider
        self._active_states: Dict[str, Dict[str, Any]] = {}
        self._active_codes: Dict[str, Dict[str, Any]] = {}
    
    def get_oauth_metadata(self) -> Dict[str, Any]:
        """Get OAuth metadata for discovery."""
        # Get base metadata from provider
        metadata = self.provider.get_oauth_metadata(self.config.get_base_url())
        
        # Add server-specific metadata
        metadata.update({
            "mcpVersion": self.config.mcp_version,
            "serverName": self.config.server_name,
            "serverVersion": self.config.server_version,
            "supportedFlows": ["authorization_code"],
            "authorizationFlowEndpoint": self.config.get_authorization_endpoint(),
            "tokenCallbackEndpoint": self.config.get_token_endpoint(),
            "metadataEndpoint": self.config.get_metadata_endpoint(),
            
            # Dynamic Client Registration
            "registration_endpoint": self.config.get_registration_endpoint(),
            "registration_endpoint_auth_methods_supported": ["bearer"],
            "client_registration_types_supported": ["dynamic"],
            
            # Provider-specific PKCE notes
            "pkce_notes": {
                "provider": self.provider.config.provider_name,
                "dual_validation": "Server validates client PKCE and uses provider-compatible PKCE with backend",
                "requirements": self.provider.get_pkce_requirements()
            }
        })
        
        return metadata
    
    async def initiate_authorization(self, request: Request, user_id: Optional[str] = None) -> RedirectResponse:
        """Initiate OAuth authorization flow with dual PKCE approach."""
        try:
            logger.debug(f"=== OAUTH INITIATE AUTHORIZATION ===")
            logger.debug(f"Request URL: {request.url}")
            logger.debug(f"Query params: {dict(request.query_params)}")
            
            # Extract PKCE parameters from client
            client_code_challenge = request.query_params.get("code_challenge")
            client_code_challenge_method = request.query_params.get("code_challenge_method")
            
            # Validate PKCE parameters
            if client_code_challenge and client_code_challenge_method:
                logger.debug(f"✅ CLIENT USING PKCE:")
                logger.debug(f"   - code_challenge: {client_code_challenge}")
                logger.debug(f"   - code_challenge_method: {client_code_challenge_method}")
                
                if client_code_challenge_method not in ["S256", "plain"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported PKCE code challenge method: {client_code_challenge_method}"
                    )
            elif client_code_challenge or client_code_challenge_method:
                raise HTTPException(
                    status_code=400,
                    detail="Both code_challenge and code_challenge_method must be provided together for PKCE"
                )
            
            # Generate state for CSRF protection
            state = generate_secure_state()
            
            # Generate provider-compatible PKCE pair
            provider_code_verifier = None
            provider_code_challenge = None
            provider_code_challenge_method = None
            
            if client_code_challenge and client_code_challenge_method:
                # Generate provider-compatible PKCE
                provider_requirements = self.provider.get_pkce_requirements()
                provider_code_verifier, provider_code_challenge = generate_provider_compatible_pkce(
                    provider_requirements, client_code_challenge_method
                )
                provider_code_challenge_method = client_code_challenge_method
                
                logger.debug(f"✅ Generated provider-compatible PKCE:")
                logger.debug(f"   - Client code_challenge: {client_code_challenge[:10]}...")
                logger.debug(f"   - Provider code_verifier: {provider_code_verifier[:10]}...")
                logger.debug(f"   - Provider code_challenge: {provider_code_challenge[:10]}...")
            
            # Store state information
            self._active_states[state] = {
                "created_at": time.time(),
                "user_id": user_id,
                "client_ip": request.client.host if request.client else None,
                # Client PKCE parameters
                "client_code_challenge": client_code_challenge,
                "client_code_challenge_method": client_code_challenge_method,
                # Provider PKCE parameters
                "provider_code_verifier": provider_code_verifier,
                "provider_code_challenge": provider_code_challenge,
                "provider_code_challenge_method": provider_code_challenge_method
            }
            
            # Store client redirect URI if provided
            client_redirect_uri = request.query_params.get('redirect_uri')
            if client_redirect_uri:
                self._active_states[state]['client_redirect_uri'] = client_redirect_uri
                logger.debug(f"Stored client redirect_uri: {client_redirect_uri}")
            
            # Get authorization URL using provider-compatible PKCE
            auth_url = self.provider.get_authorization_url(
                state=state,
                code_challenge=provider_code_challenge,
                code_challenge_method=provider_code_challenge_method
            )
            
            logger.debug(f"=== AUTHORIZATION URL GENERATED ===")
            logger.debug(f"Generated URL: {auth_url}")
            logger.debug(f"✅ Using provider-compatible PKCE with backend")
            
            logger.info(f"Initiating OAuth authorization for user_id={user_id}, state={state}")
            
            return RedirectResponse(url=auth_url, status_code=302)
            
        except Exception as e:
            logger.error(f"Failed to initiate authorization: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate OAuth authorization")
    
    async def handle_callback(
        self,
        request: Request,
        code: str,
        state: str,
        error: Optional[str] = None
    ) -> JSONResponse:
        """Handle OAuth callback from provider."""
        try:
            # Check for authorization errors
            if error:
                logger.error(f"Authorization error: {error}")
                return JSONResponse(
                    status_code=400,
                    content={"error": error, "error_description": "Authorization failed"}
                )
            
            # Validate and retrieve state information
            if state not in self._active_states:
                logger.error(f"Invalid or expired state: {state}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_state", "error_description": "Invalid or expired state parameter"}
                )
            
            state_info = self._active_states.pop(state)
            
            # Check state expiry
            if is_entry_expired(state_info, self.config.state_expiry_seconds):
                logger.error(f"Expired state: {state}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "expired_state", "error_description": "State parameter has expired"}
                )
            
            user_id = state_info.get("user_id")
            
            # Store authorization code for later token exchange
            auth_code_data = {
                "code": code,
                "state": state,
                "user_id": user_id,
                "created_at": time.time(),
                # Client PKCE parameters (for validation with client)
                "client_code_challenge": state_info.get("client_code_challenge"),
                "client_code_challenge_method": state_info.get("client_code_challenge_method"),
                # Provider PKCE parameters (for token exchange with provider)
                "provider_code_verifier": state_info.get("provider_code_verifier")
            }
            
            self._active_codes[code] = auth_code_data
            
            logger.info(f"✅ Authorization successful! Stored authorization code for token exchange.")
            
            # Handle client redirect if needed
            client_redirect_uri = state_info.get('client_redirect_uri')
            if client_redirect_uri:
                from urllib.parse import urlencode
                
                redirect_params = {'code': code, 'state': state}
                
                # Include client PKCE parameters if they were used
                if state_info.get("client_code_challenge"):
                    redirect_params['code_challenge'] = state_info["client_code_challenge"]
                    redirect_params['code_challenge_method'] = state_info["client_code_challenge_method"]
                
                redirect_url = f"{client_redirect_uri}?{urlencode(redirect_params)}"
                logger.info(f"Redirecting back to client with authorization code: {redirect_url}")
                
                return RedirectResponse(url=redirect_url, status_code=302)
            else:
                return JSONResponse(content={
                    "status": "authorization_successful",
                    "message": "Authorization code received. Use /token endpoint to exchange for access token.",
                    "code": code,
                    "state": state
                })
        
        except Exception as e:
            logger.error(f"Callback handling failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "callback_failed", "error_description": str(e)}
            )
    
    async def exchange_code_for_tokens(self, code: str, code_verifier: Optional[str] = None) -> JSONResponse:
        """Exchange authorization code for access tokens using dual PKCE validation."""
        try:
            logger.info(f"Token exchange request for code: {code[:10]}...")
            
            # Retrieve stored authorization code data
            if code not in self._active_codes:
                logger.error(f"❌ Invalid or expired authorization code: {code[:10]}...")
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}
                )
            
            auth_data = self._active_codes.pop(code)  # Remove after use
            
            # Check code expiry
            if is_entry_expired(auth_data, self.config.auth_code_expiry_seconds):
                logger.error(f"Expired authorization code: {code[:10]}...")
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_grant", "error_description": "Authorization code has expired"}
                )
            
            # Handle dual PKCE validation
            client_code_challenge = auth_data.get("client_code_challenge")
            client_code_challenge_method = auth_data.get("client_code_challenge_method")
            provider_code_verifier = auth_data.get("provider_code_verifier")
            
            if client_code_challenge and client_code_challenge_method:
                if not code_verifier:
                    logger.error("PKCE was used but code_verifier not provided")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "invalid_request", "error_description": "code_verifier required for PKCE flow"}
                    )
                
                logger.debug(f"Client code_verifier: {repr(code_verifier)}")
                logger.debug(f"Provider code_verifier: {repr(provider_code_verifier)}")
                
                # Validate client PKCE (accept any RFC 7636 compliant code_verifier)
                is_valid = validate_pkce(code_verifier, client_code_challenge, client_code_challenge_method)
                if not is_valid:
                    logger.error("Client PKCE validation failed")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "invalid_grant", "error_description": "PKCE validation failed"}
                    )
                logger.debug("✅ Client PKCE validation successful")
            
            # Exchange code for tokens using provider-compatible code_verifier
            success, token_data = await self.provider.exchange_code_for_tokens(
                code, provider_code_verifier, auth_data.get("state")
            )
            
            if not success or not token_data:
                logger.error("Token exchange with provider failed")
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_grant", "error_description": "Failed to exchange code for tokens"}
                )
            
            logger.info(f"✅ Token exchange successful for user_id={auth_data.get('user_id')}")
            return JSONResponse(content=token_data)
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "server_error", "error_description": str(e)}
            )
    
    def cleanup_expired_entries(self) -> None:
        """Clean up expired state and code entries."""
        states_cleaned = cleanup_expired_entries(self._active_states, self.config.state_expiry_seconds)
        codes_cleaned = cleanup_expired_entries(self._active_codes, self.config.auth_code_expiry_seconds)
        
        if states_cleaned + codes_cleaned > 0:
            logger.debug(f"Cleaned up {states_cleaned} expired states and {codes_cleaned} expired codes")