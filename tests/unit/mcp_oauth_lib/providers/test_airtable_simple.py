"""Simplified unit tests for Airtable OAuth provider focused on coverage."""

import time
from unittest.mock import MagicMock

import pytest

from mcp_oauth_lib.providers.airtable import (
    AIRTABLE_AUTHORIZE_URL,
    AIRTABLE_TOKEN_URL,
    AirtableOAuthProvider,
    AirtableProviderConfig,
)


class TestAirtableProviderConfig:
    """Test cases for AirtableProviderConfig."""

    def test_airtable_provider_config_defaults(self):
        """Test AirtableProviderConfig with default values."""
        config = AirtableProviderConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        assert config.provider_name == "airtable"
        assert config.client_id == "test_client"
        assert config.client_secret == "test_secret"
        assert config.redirect_uri == "http://localhost/callback"
        assert "data.records:read" in config.scope

    def test_get_authorization_url(self):
        """Test get_authorization_url method."""
        config = AirtableProviderConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        assert config.get_authorization_url() == AIRTABLE_AUTHORIZE_URL

    def test_get_token_url(self):
        """Test get_token_url method."""
        config = AirtableProviderConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        assert config.get_token_url() == AIRTABLE_TOKEN_URL

    def test_get_pkce_requirements(self):
        """Test get_pkce_requirements method."""
        config = AirtableProviderConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        requirements = config.get_pkce_requirements()

        assert requirements["min_length"] == 43
        assert requirements["max_length"] == 128
        assert requirements["required"] is True
        assert "S256" in requirements["methods_supported"]
        assert "~" not in requirements["character_set"]

    def test_get_supported_scopes(self):
        """Test get_supported_scopes method."""
        config = AirtableProviderConfig(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        scopes = config.get_supported_scopes()

        expected_scopes = [
            "data.records:read",
            "data.records:write",
            "data.recordComments:read",
            "data.recordComments:write",
            "schema.bases:read",
            "schema.bases:write",
            "webhook:manage",
        ]

        for scope in expected_scopes:
            assert scope in scopes


class TestAirtableOAuthProvider:
    """Test cases for AirtableOAuthProvider."""

    def setup_method(self):
        """Setup method to create test config and provider."""
        self.config = AirtableProviderConfig(
            client_id="test_client_123",
            client_secret="test_secret_456",
            redirect_uri="http://localhost:8000/callback",
        )
        self.provider = AirtableOAuthProvider(self.config)

    def test_provider_initialization(self):
        """Test provider initialization."""
        assert self.provider.config == self.config
        assert self.provider.access_token is None
        assert self.provider.refresh_token is None
        assert self.provider.expires_at is None
        assert self.provider._client is None

    def test_provider_initialization_with_tokens(self):
        """Test provider initialization and token setting."""
        self.provider.access_token = "test_access_token"
        self.provider.refresh_token = "test_refresh_token"
        self.provider.expires_at = time.time() + 3600

        assert self.provider.access_token == "test_access_token"
        assert self.provider.refresh_token == "test_refresh_token"
        assert self.provider.expires_at is not None

    def test_create_oauth2_client_no_token(self):
        """Test _create_oauth2_client without existing token."""
        client = self.provider._create_oauth2_client()

        assert client.client_id == self.config.client_id
        assert client.client_secret == self.config.client_secret
        assert client.token is None

    def test_create_oauth2_client_with_token(self):
        """Test _create_oauth2_client with existing token."""
        self.provider.access_token = "existing_token"
        self.provider.refresh_token = "existing_refresh"
        self.provider.expires_at = time.time() + 3600

        client = self.provider._create_oauth2_client()

        assert client.token is not None
        assert client.token["access_token"] == "existing_token"
        assert client.token["refresh_token"] == "existing_refresh"
        assert client.token["token_type"] == "Bearer"

    def test_client_property_creates_client(self):
        """Test that client property creates client when None."""
        assert self.provider._client is None

        client = self.provider.client

        assert self.provider._client is not None
        assert client is self.provider._client

    def test_client_property_reuses_existing(self):
        """Test that client property reuses existing client."""
        client1 = self.provider.client
        client2 = self.provider.client

        assert client1 is client2

    def test_is_token_expired_no_token(self):
        """Test is_token_expired when no token is set."""
        assert self.provider.is_token_expired is True

    def test_is_token_expired_no_expiry(self):
        """Test is_token_expired when token has no expiry."""
        self.provider.access_token = "test_token"
        # expires_at is None

        assert self.provider.is_token_expired is True

    def test_is_token_expired_future_expiry(self):
        """Test is_token_expired with future expiry."""
        self.provider.access_token = "test_token"
        self.provider.expires_at = time.time() + 3600  # 1 hour from now

        assert self.provider.is_token_expired is False

    def test_is_token_expired_past_expiry(self):
        """Test is_token_expired with past expiry."""
        self.provider.access_token = "test_token"
        self.provider.expires_at = time.time() - 3600  # 1 hour ago

        assert self.provider.is_token_expired is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_refresh_token(self):
        """Test ensure_valid_token with access token but no refresh token."""
        self.provider.access_token = "direct_access_token"
        # No refresh token

        result = await self.provider.ensure_valid_token()

        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_valid_token(self):
        """Test ensure_valid_token with valid token."""
        self.provider.access_token = "valid_token"
        self.provider.refresh_token = "refresh_token"
        self.provider.expires_at = time.time() + 3600  # Valid for 1 hour

        result = await self.provider.ensure_valid_token()

        assert result is True

    def test_get_authorization_url_basic(self):
        """Test get_authorization_url with basic parameters."""
        state = "test_state_123"

        mock_client = MagicMock()
        mock_client.create_authorization_url.return_value = ("https://test.url", state)
        self.provider._client = mock_client

        url = self.provider.get_authorization_url(state)

        assert url == "https://test.url"
        mock_client.create_authorization_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_introspect_token_with_token(self):
        """Test token introspection with active token."""
        self.provider.access_token = "active_token"
        self.provider.expires_at = time.time() + 3600

        result = await self.provider.introspect_token("active_token")

        assert result is not None
        assert result["active"] is True
        assert result["client_id"] == self.config.client_id
        assert result["scope"] == self.config.scope
        assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_introspect_token_no_token(self):
        """Test token introspection with no stored token."""
        # Provider has no access_token set
        result = await self.provider.introspect_token("some_token")

        # Should return token info but marked as inactive
        assert result is not None
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_revoke_token_success(self):
        """Test successful token revocation."""
        self.provider.access_token = "token_to_revoke"
        self.provider.refresh_token = "refresh_to_revoke"
        self.provider._client = MagicMock()

        result = await self.provider.revoke_token("token_to_revoke")

        assert result is True
        assert self.provider.access_token is None
        assert self.provider.refresh_token is None
        assert self.provider.expires_at is None
        assert self.provider._client.token is None

    def test_get_oauth_metadata(self):
        """Test OAuth metadata generation."""
        server_base_url = "https://oauth.example.com"

        metadata = self.provider.get_oauth_metadata(server_base_url)

        # Check required RFC 8414 fields
        assert metadata["issuer"] == server_base_url
        assert metadata["authorization_endpoint"] == f"{server_base_url}/auth/authorize"
        assert metadata["token_endpoint"] == f"{server_base_url}/token"
        assert metadata["response_types_supported"] == ["code"]

        # Check provider-specific fields
        assert metadata["provider"] == "airtable"
        assert metadata["provider_authorization_endpoint"] == AIRTABLE_AUTHORIZE_URL
        assert metadata["provider_token_endpoint"] == AIRTABLE_TOKEN_URL

    def test_get_auth_headers_with_token(self):
        """Test get_auth_headers with access token."""
        self.provider.access_token = "bearer_token_123"

        headers = self.provider.get_auth_headers()

        assert headers["Authorization"] == "Bearer bearer_token_123"

    def test_get_auth_headers_no_token(self):
        """Test get_auth_headers without access token."""
        with pytest.raises(ValueError, match="No access token available"):
            self.provider.get_auth_headers()

    def test_scope_validation(self):
        """Test scope validation functionality."""
        # Test valid scopes
        assert self.provider.validate_scope("data.records:read")
        assert self.provider.validate_scope("data.records:read data.records:write")

        # Test invalid scopes
        assert not self.provider.validate_scope("invalid.scope")
        assert not self.provider.validate_scope("data.records:read invalid.scope")

        # Test empty scope
        assert self.provider.validate_scope("")
