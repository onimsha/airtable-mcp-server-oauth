"""Pytest configuration and shared fixtures."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_oauth_client():
    """Create a mock OAuth client for testing."""
    mock_client = MagicMock()
    mock_client.access_token = "test_access_token"
    mock_client.refresh_token = "test_refresh_token"
    mock_client.expires_at = 9999999999  # Far future
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
        "token_type": "Bearer",
    }
    return mock_response


@pytest.fixture
def mock_airtable_response():
    """Create a mock Airtable API response."""
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "records": [
            {
                "id": "rec123",
                "fields": {"Name": "Test Record", "Value": 42},
                "createdTime": "2025-01-01T00:00:00.000Z",
            }
        ]
    }
    return mock_response
