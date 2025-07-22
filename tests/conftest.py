"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from airtable_mcp.oauth.handler import AirtableOAuthHandler


@pytest.fixture
def oauth_handler():
    """Create an OAuth handler instance for testing."""
    return AirtableOAuthHandler(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/oauth/callback",
        scope="data.records:read data.records:write",
    )


@pytest.fixture
def oauth_handler_with_tokens():
    """Create an OAuth handler with tokens for testing."""
    handler = AirtableOAuthHandler(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/oauth/callback",
        scope="data.records:read data.records:write",
    )
    handler.access_token = "test_access_token"
    handler.refresh_token = "test_refresh_token"
    handler.expires_at = 9999999999  # Far future
    return handler


@pytest.fixture
def mock_firestore_client():
    """Create a mock Firestore client."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
    return mock_client


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }
    return mock_response