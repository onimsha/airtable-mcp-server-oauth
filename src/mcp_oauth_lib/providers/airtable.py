"""Airtable OAuth provider implementation."""

import logging
import time
from dataclasses import dataclass
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc6749.errors import OAuth2Error

from ..core.config import ProviderConfig
from .base import BaseOAuthProvider

logger = logging.getLogger(__name__)

# Airtable OAuth endpoints
AIRTABLE_AUTHORIZE_URL = "https://airtable.com/oauth2/v1/authorize"
AIRTABLE_TOKEN_URL = "https://airtable.com/oauth2/v1/token"
TOKEN_EXPIRY_MARGIN = 300  # 5 minutes in seconds


@dataclass
class AirtableProviderConfig(ProviderConfig):
    """Airtable-specific OAuth configuration."""

    provider_name: str = "airtable"
    scope: str = "data.records:read data.records:write data.recordComments:read data.recordComments:write schema.bases:read schema.bases:write webhook:manage"

    def get_authorization_url(self) -> str:
        return AIRTABLE_AUTHORIZE_URL

    def get_token_url(self) -> str:
        return AIRTABLE_TOKEN_URL

    def get_pkce_requirements(self) -> dict[str, Any]:
        """Airtable has stricter PKCE requirements than RFC 7636."""
        return {
            "min_length": 43,
            "max_length": 128,
            "character_set": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_",
            "methods_supported": ["S256", "plain"],
            "required": True,
            "note": "Airtable does not allow ~ character (stricter than RFC 7636)",
        }

    def get_supported_scopes(self) -> list[str]:
        return [
            "data.records:read",
            "data.records:write",
            "data.recordComments:read",
            "data.recordComments:write",
            "schema.bases:read",
            "schema.bases:write",
            "webhook:manage",
        ]


class AirtableOAuthProvider(BaseOAuthProvider):
    """Airtable OAuth 2.0 provider implementation."""

    def __init__(self, config: AirtableProviderConfig):
        super().__init__(config)
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.expires_at: float | None = None
        self._client: AsyncOAuth2Client | None = None

    def _create_oauth2_client(self) -> AsyncOAuth2Client:
        """Create and configure the OAuth2 client."""
        client = AsyncOAuth2Client(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            token_endpoint=self.config.get_token_url(),
            token_endpoint_auth_method="client_secret_basic",
        )

        # Set current token if available
        if self.access_token:
            token = {
                "access_token": self.access_token,
                "token_type": "Bearer",
                "expires_at": self.expires_at,
            }
            if self.refresh_token:
                token["refresh_token"] = self.refresh_token

            client.token = token

        return client

    @property
    def client(self) -> AsyncOAuth2Client:
        """Get or create the OAuth2 client."""
        if self._client is None:
            self._client = self._create_oauth2_client()
        return self._client

    @property
    def is_token_expired(self) -> bool:
        """Check if the access token is expired or will expire soon."""
        if not self.access_token or not self.expires_at:
            return True

        # Consider the token expired if it will expire within the margin
        return time.time() + TOKEN_EXPIRY_MARGIN >= self.expires_at

    async def ensure_valid_token(self) -> bool:
        """Ensure the access token is valid, refreshing if necessary.

        Returns:
            True if the token is valid (or was refreshed successfully), False otherwise.
        """
        # If we have an access token but no refresh token, assume the access token is valid
        # This handles the case where an access token is directly provided for MCP tool calls
        if self.access_token and not self.refresh_token:
            logger.debug(
                "Access token provided without refresh token - assuming valid for direct usage"
            )
            return True

        if not self.is_token_expired:
            return True

        # Try to refresh the token if we have a refresh token
        if self.refresh_token:
            success, token_data = await self.refresh_access_token(self.refresh_token)
            if success and token_data:
                # Update our stored tokens
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                if "expires_in" in token_data:
                    self.expires_at = time.time() + token_data["expires_in"]
                return True

        logger.warning(
            "Unable to ensure valid token - no refresh token available or refresh failed"
        )
        return False

    def get_authorization_url(
        self,
        state: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        **kwargs,
    ) -> str:
        """Get authorization URL for Airtable OAuth flow."""
        auth_params = {
            "redirect_uri": self.config.redirect_uri,
            "scope": self.config.scope,
            "state": state,
        }

        # Add PKCE parameters if provided
        if code_challenge and code_challenge_method:
            auth_params["code_challenge"] = code_challenge
            auth_params["code_challenge_method"] = code_challenge_method

        # Add any additional parameters
        auth_params.update(kwargs)

        return self.client.create_authorization_url(
            self.config.get_authorization_url(), **auth_params
        )[0]  # create_authorization_url returns (url, state)

    async def exchange_code_for_tokens(
        self, code: str, code_verifier: str | None = None, state: str | None = None
    ) -> tuple[bool, dict[str, Any] | None]:
        """Exchange authorization code for access tokens."""
        try:
            logger.info("Exchanging authorization code for tokens with Airtable")

            # Prepare token request parameters
            token_params = {
                "authorization_response": None,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
            }

            # Add PKCE code verifier if provided
            if code_verifier:
                token_params["code_verifier"] = code_verifier

            # Use Authlib's OAuth2 client to fetch the token
            token = await self.client.fetch_token(
                self.config.get_token_url(), **token_params
            )

            # Update our instance with the new tokens
            self.access_token = token.get("access_token")
            self.refresh_token = token.get("refresh_token")

            # Calculate expires_at from expires_in
            expires_in = token.get("expires_in")
            if expires_in:
                self.expires_at = time.time() + expires_in

            logger.info(
                f"✅ OAuth token exchange successful! Access token expires in {expires_in}s."
            )
            return True, token

        except OAuth2Error as e:
            logger.error(f"OAuth2 error during token exchange: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return False, None

    async def refresh_access_token(
        self, refresh_token: str
    ) -> tuple[bool, dict[str, Any] | None]:
        """Refresh the access token using the refresh token."""
        try:
            logger.debug("Refreshing access token with Airtable...")

            # Use Authlib's refresh token functionality
            token = await self.client.refresh_token(
                self.config.get_token_url(), refresh_token=refresh_token
            )

            # Update our instance with the new tokens
            self.access_token = token.get("access_token")

            # Refresh token might also be rotated
            if "refresh_token" in token:
                self.refresh_token = token["refresh_token"]

            # Calculate expires_at from expires_in
            expires_in = token.get("expires_in")
            if expires_in:
                self.expires_at = time.time() + expires_in

            # Update the client's token
            self._client = None  # Force recreation with new token

            logger.info("✅ Access token refreshed successfully")
            return True, token

        except OAuth2Error as e:
            logger.error(f"OAuth2 error during token refresh: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return False, None

    async def introspect_token(self, token: str) -> dict[str, Any] | None:
        """Introspect a token (Airtable doesn't provide introspection endpoint)."""
        # Airtable doesn't provide a token introspection endpoint,
        # so return basic information based on our stored data
        target_token = token or self.access_token
        if not target_token:
            return None

        return {
            "active": not self.is_token_expired,
            "client_id": self.config.client_id,
            "scope": self.config.scope,
            "exp": self.expires_at,
            "token_type": "Bearer",
        }

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token (Airtable doesn't provide revocation endpoint)."""
        try:
            # Airtable doesn't provide a token revocation endpoint,
            # so simply clear the stored tokens
            self.access_token = None
            self.refresh_token = None
            self.expires_at = None

            # Clear client token
            if self._client:
                self._client.token = None

            logger.info("Tokens revoked successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def get_oauth_metadata(self, server_base_url: str) -> dict[str, Any]:
        """Get OAuth metadata for Airtable provider."""
        pkce_requirements = self.get_pkce_requirements()

        return {
            # RFC 8414 required fields
            "issuer": server_base_url,
            "authorization_endpoint": f"{server_base_url}/auth/authorize",
            "token_endpoint": f"{server_base_url}/token",
            "response_types_supported": ["code"],
            # Additional standard fields
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_post",
                "client_secret_basic",
                "none",
            ],
            "scopes_supported": self.get_supported_scopes(),
            "response_modes_supported": ["query"],
            # PKCE support
            "code_challenge_methods_supported": pkce_requirements["methods_supported"],
            # Airtable-specific metadata
            "provider": self.config.provider_name,
            "provider_authorization_endpoint": self.config.get_authorization_url(),
            "provider_token_endpoint": self.config.get_token_url(),
            "pkce_requirements": pkce_requirements,
            # MCP-specific fields (for backward compatibility)
            "authorizationEndpoint": f"{server_base_url}/auth/authorize",
            "tokenEndpoint": f"{server_base_url}/token",
            "scope": self.config.scope,
            "clientId": self.config.client_id,
            "redirectUri": self.config.redirect_uri,
            "responseType": "code",
            "grantType": "authorization_code",
            "tokenEndpointAuthMethod": "client_secret_basic",
            "codeChallengeMethod": "S256",
            "additionalParameters": {
                "access_type": "offline"  # Ensure refresh token is provided
            },
        }

    def get_auth_headers(self) -> dict[str, str]:
        """Get authorization headers for API requests."""
        if not self.access_token:
            raise ValueError("No access token available")

        return {"Authorization": f"Bearer {self.access_token}"}
