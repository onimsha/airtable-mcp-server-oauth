"""Unit tests for Airtable OAuth provider."""

import time
from unittest.mock import AsyncMock, patch

import pytest

from mcp_oauth_lib.providers.airtable import (
    AIRTABLE_AUTHORIZE_URL,
    AIRTABLE_TOKEN_URL,
    AirtableOAuthProvider,
    AirtableProviderConfig,
)


class TestAirtableProviderConfig:
    """Test cases for AirtableProviderConfig."""

    def test_initialization(self):
        """Test provider config initialization."""
        config = AirtableProviderConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.redirect_uri == "http://localhost:8000/callback"
        assert config.provider_name == "airtable"
        assert "data.records:read" in config.scope

    def test_get_authorization_url(self):
        """Test authorization URL getter."""
        config = AirtableProviderConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        assert config.get_authorization_url() == AIRTABLE_AUTHORIZE_URL

    def test_get_token_url(self):
        """Test token URL getter."""
        config = AirtableProviderConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        assert config.get_token_url() == AIRTABLE_TOKEN_URL

    def test_get_pkce_requirements(self):
        """Test PKCE requirements."""
        config = AirtableProviderConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        requirements = config.get_pkce_requirements()

        assert requirements["min_length"] == 43
        assert requirements["max_length"] == 128
        assert requirements["required"] is True
        assert "S256" in requirements["methods_supported"]

    def test_get_supported_scopes(self):
        """Test supported scopes."""
        config = AirtableProviderConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        scopes = config.get_supported_scopes()

        assert "data.records:read" in scopes
        assert "data.records:write" in scopes
        assert "schema.bases:read" in scopes


class TestAirtableOAuthProvider:
    """Test cases for AirtableOAuthProvider."""

    @pytest.fixture
    def provider_config(self):
        """Create a provider config for testing."""
        return AirtableProviderConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback",
        )

    @pytest.fixture
    def provider(self, provider_config):
        """Create a provider instance for testing."""
        return AirtableOAuthProvider(provider_config)

    def test_initialization(self, provider, provider_config):
        """Test provider initialization."""
        assert provider.config == provider_config
        assert provider._access_token is None
        assert provider._refresh_token is None
        assert provider._expires_at is None

    def test_access_token_property(self, provider):
        """Test access token property."""
        assert provider.access_token is None

        provider._access_token = "test_token"
        assert provider.access_token == "test_token"

    def test_is_token_expired_no_token(self, provider):
        """Test token expiry check when no token exists."""
        assert provider.is_token_expired() is True

    def test_is_token_expired_no_expiry(self, provider):
        """Test token expiry check when no expiry time exists."""
        provider._access_token = "test_token"
        assert provider.is_token_expired() is True

    def test_is_token_expired_valid_token(self, provider):
        """Test token expiry check with valid token."""
        provider._access_token = "test_token"
        provider._expires_at = time.time() + 3600  # 1 hour from now
        assert provider.is_token_expired() is False

    def test_is_token_expired_expired_token(self, provider):
        """Test token expiry check with expired token."""
        provider._access_token = "test_token"
        provider._expires_at = time.time() - 3600  # 1 hour ago
        assert provider.is_token_expired() is True

    def test_is_token_expired_soon_to_expire(self, provider):
        """Test token expiry check with token expiring soon."""
        provider._access_token = "test_token"
        provider._expires_at = time.time() + 200  # 200 seconds from now
        assert provider.is_token_expired() is True

    def test_generate_authorization_url(self, provider):
        """Test authorization URL generation."""
        state = "test_state"
        code_verifier = "test_verifier"
        code_challenge = "test_challenge"

        url = provider.generate_authorization_url(state, code_verifier, code_challenge)

        assert AIRTABLE_AUTHORIZE_URL in url
        assert "client_id=test_client_id" in url
        assert "state=test_state" in url
        assert "code_challenge=test_challenge" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, provider):
        """Test successful token exchange."""
        mock_token_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.fetch_token.return_value = mock_token_response

            result = await provider.exchange_code_for_tokens(
                "test_code", "test_verifier"
            )

            assert result is True
            assert provider.access_token == "new_access_token"
            assert provider._refresh_token == "new_refresh_token"
            assert provider._expires_at is not None

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_failure(self, provider):
        """Test failed token exchange."""
        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.fetch_token.side_effect = Exception("OAuth error")

            result = await provider.exchange_code_for_tokens(
                "test_code", "test_verifier"
            )

            assert result is False
            assert provider.access_token is None

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, provider):
        """Test successful token refresh."""
        provider._refresh_token = "test_refresh_token"

        mock_token_response = {
            "access_token": "refreshed_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.refresh_token.return_value = mock_token_response

            result = await provider.refresh_access_token()

            assert result is True
            assert provider.access_token == "refreshed_access_token"

    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token(self, provider):
        """Test token refresh without refresh token."""
        result = await provider.refresh_access_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_failure(self, provider):
        """Test failed token refresh."""
        provider._refresh_token = "test_refresh_token"

        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.refresh_token.side_effect = Exception("Refresh error")

            result = await provider.refresh_access_token()
            assert result is False

    @pytest.mark.asyncio
    async def test_ensure_valid_token_valid(self, provider):
        """Test ensure valid token with already valid token."""
        provider._access_token = "test_token"
        provider._expires_at = time.time() + 3600

        result = await provider.ensure_valid_token()
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_needs_refresh(self, provider):
        """Test ensure valid token that needs refresh."""
        provider._access_token = "test_token"
        provider._refresh_token = "test_refresh_token"
        provider._expires_at = time.time() - 3600  # Expired

        mock_token_response = {
            "access_token": "refreshed_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.refresh_token.return_value = mock_token_response

            result = await provider.ensure_valid_token()
            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_refresh_fails(self, provider):
        """Test ensure valid token when refresh fails."""
        provider._access_token = "test_token"
        provider._refresh_token = "test_refresh_token"
        provider._expires_at = time.time() - 3600  # Expired

        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.refresh_token.side_effect = Exception("Refresh error")

            result = await provider.ensure_valid_token()
            assert result is False
