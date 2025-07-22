"""Unit tests for OAuth handler."""

import time
import urllib.parse
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from airtable_mcp.oauth.handler import AirtableOAuthHandler, AUTHORIZE_URL, TOKEN_URL


class TestAirtableOAuthHandler:
    """Test cases for AirtableOAuthHandler."""

    def test_initialization(self):
        """Test OAuth handler initialization."""
        handler = AirtableOAuthHandler(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        
        assert handler.client_id == "test_id"
        assert handler.client_secret == "test_secret"
        assert handler.redirect_uri == "http://localhost:8000/callback"
        assert handler.access_token is None
        assert handler.refresh_token is None
        assert handler.expires_at is None

    def test_get_authorization_url(self, oauth_handler):
        """Test authorization URL generation."""
        state = "test_state_123"
        url = oauth_handler.get_authorization_url(state)
        
        # Parse the URL to verify components
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        assert parsed.scheme == "https"
        assert parsed.netloc == "airtable.com"
        assert parsed.path == "/oauth2/v1/authorize"
        
        assert query_params["client_id"][0] == "test_client_id"
        assert query_params["redirect_uri"][0] == "http://localhost:8000/oauth/callback"
        assert query_params["response_type"][0] == "code"
        assert query_params["scope"][0] == "data.records:read data.records:write"
        assert query_params["state"][0] == state

    def test_is_token_expired_no_token(self, oauth_handler):
        """Test token expiry check when no token exists."""
        assert oauth_handler.is_token_expired is True

    def test_is_token_expired_no_expiry(self, oauth_handler):
        """Test token expiry check when no expiry time exists."""
        oauth_handler.access_token = "test_token"
        assert oauth_handler.is_token_expired is True

    def test_is_token_expired_valid_token(self, oauth_handler):
        """Test token expiry check with valid token."""
        oauth_handler.access_token = "test_token"
        oauth_handler.expires_at = time.time() + 3600  # 1 hour from now
        assert oauth_handler.is_token_expired is False

    def test_is_token_expired_expired_token(self, oauth_handler):
        """Test token expiry check with expired token."""
        oauth_handler.access_token = "test_token"
        oauth_handler.expires_at = time.time() - 3600  # 1 hour ago
        assert oauth_handler.is_token_expired is True

    def test_is_token_expired_soon_to_expire(self, oauth_handler):
        """Test token expiry check with token expiring soon."""
        oauth_handler.access_token = "test_token"
        oauth_handler.expires_at = time.time() + 200  # 200 seconds from now (less than 5 min margin)
        assert oauth_handler.is_token_expired is True

    def test_get_auth_headers_no_token(self, oauth_handler):
        """Test getting auth headers when no token exists."""
        with pytest.raises(ValueError, match="No access token available"):
            oauth_handler.get_auth_headers()

    def test_get_auth_headers_with_token(self, oauth_handler_with_tokens):
        """Test getting auth headers with valid token."""
        headers = oauth_handler_with_tokens.get_auth_headers()
        assert headers == {"Authorization": "Bearer test_access_token"}

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, oauth_handler, mock_httpx_response):
        """Test successful token exchange."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_httpx_response
            
            result = await oauth_handler.exchange_code_for_tokens("test_code")
            
            assert result is True
            assert oauth_handler.access_token == "new_access_token"
            assert oauth_handler.refresh_token == "new_refresh_token"
            assert oauth_handler.expires_at is not None
            
            # Verify the request was made correctly
            mock_context.post.assert_called_once_with(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uri": "http://localhost:8000/oauth/callback",
                    "code": "test_code",
                }
            )

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_http_error(self, oauth_handler):
        """Test token exchange with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock failed response
            mock_response = AsyncMock()
            mock_response.is_success = False
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_context.post.return_value = mock_response
            
            result = await oauth_handler.exchange_code_for_tokens("test_code")
            
            assert result is False
            assert oauth_handler.access_token is None
            assert oauth_handler.refresh_token is None

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_missing_access_token(self, oauth_handler):
        """Test token exchange with missing access token in response."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock response without access token
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.json.return_value = {"refresh_token": "token"}
            mock_context.post.return_value = mock_response
            
            result = await oauth_handler.exchange_code_for_tokens("test_code")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_missing_refresh_token(self, oauth_handler):
        """Test token exchange with missing refresh token in response."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock response without refresh token
            mock_response = AsyncMock()
            mock_response.is_success = True
            mock_response.json.return_value = {"access_token": "token"}
            mock_context.post.return_value = mock_response
            
            result = await oauth_handler.exchange_code_for_tokens("test_code")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_network_error(self, oauth_handler):
        """Test token exchange with network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.side_effect = httpx.RequestError("Network error")
            
            result = await oauth_handler.exchange_code_for_tokens("test_code")
            
            assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, oauth_handler_with_tokens, mock_httpx_response):
        """Test successful token refresh."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_httpx_response
            
            result = await oauth_handler_with_tokens.refresh_access_token()
            
            assert result is True
            assert oauth_handler_with_tokens.access_token == "new_access_token"
            assert oauth_handler_with_tokens.refresh_token == "new_refresh_token"
            
            # Verify the request was made correctly
            mock_context.post.assert_called_once_with(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "refresh_token": "test_refresh_token",
                }
            )

    @pytest.mark.asyncio
    async def test_refresh_access_token_no_refresh_token(self, oauth_handler):
        """Test token refresh without refresh token."""
        result = await oauth_handler.refresh_access_token()
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_http_error(self, oauth_handler_with_tokens):
        """Test token refresh with HTTP error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock failed response
            mock_response = AsyncMock()
            mock_response.is_success = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_context.post.return_value = mock_response
            
            result = await oauth_handler_with_tokens.refresh_access_token()
            assert result is False

    @pytest.mark.asyncio
    async def test_refresh_access_token_network_error(self, oauth_handler_with_tokens):
        """Test token refresh with network error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.side_effect = httpx.RequestError("Network error")
            
            result = await oauth_handler_with_tokens.refresh_access_token()
            assert result is False

    @pytest.mark.asyncio
    async def test_ensure_valid_token_valid(self, oauth_handler_with_tokens):
        """Test ensure valid token with already valid token."""
        result = await oauth_handler_with_tokens.ensure_valid_token()
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_needs_refresh(self, oauth_handler_with_tokens, mock_httpx_response):
        """Test ensure valid token that needs refresh."""
        # Make token expired
        oauth_handler_with_tokens.expires_at = time.time() - 3600
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_httpx_response
            
            result = await oauth_handler_with_tokens.ensure_valid_token()
            assert result is True

    @pytest.mark.asyncio
    async def test_ensure_valid_token_refresh_fails(self, oauth_handler_with_tokens):
        """Test ensure valid token when refresh fails."""
        # Make token expired
        oauth_handler_with_tokens.expires_at = time.time() - 3600
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            
            # Mock failed refresh
            mock_response = AsyncMock()
            mock_response.is_success = False
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_context.post.return_value = mock_response
            
            result = await oauth_handler_with_tokens.ensure_valid_token()
            assert result is False