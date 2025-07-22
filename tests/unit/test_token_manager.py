"""Unit tests for Token Manager."""

from unittest.mock import MagicMock, patch

import pytest
from google.cloud.exceptions import GoogleCloudError

from airtable_mcp.oauth.handler import AirtableOAuthHandler
from airtable_mcp.oauth.token_manager import TokenManager


class TestTokenManager:
    """Test cases for TokenManager."""

    def test_initialization(self):
        """Test token manager initialization."""
        manager = TokenManager("test-project", "test-collection")

        assert manager.project_id == "test-project"
        assert manager.collection_name == "test-collection"
        assert manager._db is None

    def test_initialization_default_collection(self):
        """Test token manager initialization with default collection name."""
        manager = TokenManager("test-project")

        assert manager.project_id == "test-project"
        assert manager.collection_name == "airtable_oauth_tokens"

    @patch("airtable_oauth_mcp.oauth.token_manager.firestore.Client")
    def test_db_property_creates_client(self, mock_firestore_client):
        """Test that db property creates Firestore client."""
        manager = TokenManager("test-project")

        # Access db property
        db = manager.db

        mock_firestore_client.assert_called_once_with(project="test-project")
        assert db == mock_firestore_client.return_value
        assert manager._db == mock_firestore_client.return_value

    @patch("airtable_oauth_mcp.oauth.token_manager.firestore.Client")
    def test_db_property_reuses_client(self, mock_firestore_client):
        """Test that db property reuses existing client."""
        manager = TokenManager("test-project")

        # Access db property twice
        db1 = manager.db
        db2 = manager.db

        # Should only create client once
        mock_firestore_client.assert_called_once()
        assert db1 == db2

    @pytest.mark.asyncio
    async def test_save_tokens_success(self, mock_firestore_client):
        """Test successful token saving."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        oauth_handler = AirtableOAuthHandler(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        oauth_handler.access_token = "access_token"
        oauth_handler.refresh_token = "refresh_token"
        oauth_handler.expires_at = 1234567890.0

        # Mock Firestore operations
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        result = await manager.save_tokens("user123", oauth_handler)

        assert result is True
        mock_firestore_client.collection.assert_called_once_with(
            "airtable_oauth_tokens"
        )
        mock_firestore_client.collection.return_value.document.assert_called_once_with(
            "user123"
        )

        # Verify the data that was saved
        mock_doc_ref.set.assert_called_once()
        saved_data = mock_doc_ref.set.call_args[0][0]
        assert saved_data["access_token"] == "access_token"
        assert saved_data["refresh_token"] == "refresh_token"
        assert saved_data["expires_at"] == 1234567890.0
        assert saved_data["client_id"] == "test_id"
        assert "created_at" in saved_data
        assert "updated_at" in saved_data

    @pytest.mark.asyncio
    async def test_save_tokens_google_cloud_error(self, mock_firestore_client):
        """Test token saving with Google Cloud error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        oauth_handler = AirtableOAuthHandler(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        # Mock Firestore error
        mock_firestore_client.collection.return_value.document.return_value.set.side_effect = GoogleCloudError(
            "Firestore error"
        )

        result = await manager.save_tokens("user123", oauth_handler)

        assert result is False

    @pytest.mark.asyncio
    async def test_save_tokens_general_error(self, mock_firestore_client):
        """Test token saving with general error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        oauth_handler = AirtableOAuthHandler(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )

        # Mock general error
        mock_firestore_client.collection.return_value.document.return_value.set.side_effect = Exception(
            "General error"
        )

        result = await manager.save_tokens("user123", oauth_handler)

        assert result is False

    @pytest.mark.asyncio
    async def test_load_tokens_success(self, mock_firestore_client):
        """Test successful token loading."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock Firestore document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "expires_at": 1234567890.0,
            "client_id": "test_id",
        }
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = await manager.load_tokens("user123")

        assert result is not None
        assert result["access_token"] == "access_token"
        assert result["refresh_token"] == "refresh_token"
        assert result["expires_at"] == 1234567890.0
        assert result["client_id"] == "test_id"

        mock_firestore_client.collection.assert_called_once_with(
            "airtable_oauth_tokens"
        )
        mock_firestore_client.collection.return_value.document.assert_called_once_with(
            "user123"
        )

    @pytest.mark.asyncio
    async def test_load_tokens_not_found(self, mock_firestore_client):
        """Test token loading when document doesn't exist."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock non-existent document
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        result = await manager.load_tokens("user123")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_tokens_google_cloud_error(self, mock_firestore_client):
        """Test token loading with Google Cloud error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock Firestore error
        mock_firestore_client.collection.return_value.document.return_value.get.side_effect = GoogleCloudError(
            "Firestore error"
        )

        result = await manager.load_tokens("user123")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_oauth_handler_no_existing_tokens(self, mock_firestore_client):
        """Test creating OAuth handler without existing tokens."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock no existing document
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        handler = await manager.create_oauth_handler(
            "user123", "client_id", "client_secret", "http://localhost:8000/callback"
        )

        assert handler is not None
        assert handler.client_id == "client_id"
        assert handler.client_secret == "client_secret"
        assert handler.redirect_uri == "http://localhost:8000/callback"
        assert handler.access_token is None
        assert handler.refresh_token is None

    @pytest.mark.asyncio
    async def test_create_oauth_handler_with_existing_tokens(
        self, mock_firestore_client
    ):
        """Test creating OAuth handler with existing tokens."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock existing document with tokens
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "access_token": "existing_access_token",
            "refresh_token": "existing_refresh_token",
            "expires_at": 1234567890.0,
        }
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        handler = await manager.create_oauth_handler(
            "user123", "client_id", "client_secret", "http://localhost:8000/callback"
        )

        assert handler is not None
        assert handler.client_id == "client_id"
        assert handler.access_token == "existing_access_token"
        assert handler.refresh_token == "existing_refresh_token"
        assert handler.expires_at == 1234567890.0

    @pytest.mark.asyncio
    async def test_create_oauth_handler_with_custom_scope(self, mock_firestore_client):
        """Test creating OAuth handler with custom scope."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock no existing document
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

        handler = await manager.create_oauth_handler(
            "user123",
            "client_id",
            "client_secret",
            "http://localhost:8000/callback",
            "custom:scope",
        )

        assert handler is not None
        assert handler.scope == "custom:scope"

    @pytest.mark.asyncio
    async def test_delete_tokens_success(self, mock_firestore_client):
        """Test successful token deletion."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        result = await manager.delete_tokens("user123")

        assert result is True
        mock_firestore_client.collection.assert_called_once_with(
            "airtable_oauth_tokens"
        )
        mock_firestore_client.collection.return_value.document.assert_called_once_with(
            "user123"
        )
        mock_doc_ref.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_tokens_google_cloud_error(self, mock_firestore_client):
        """Test token deletion with Google Cloud error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock Firestore error
        mock_firestore_client.collection.return_value.document.return_value.delete.side_effect = GoogleCloudError(
            "Firestore error"
        )

        result = await manager.delete_tokens("user123")

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(self, mock_firestore_client):
        """Test successful cleanup of expired tokens."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock query results
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        mock_docs = [mock_doc1, mock_doc2]

        mock_query = MagicMock()
        mock_query.stream.return_value = mock_docs
        mock_firestore_client.collection.return_value.where.return_value = mock_query

        result = await manager.cleanup_expired_tokens(30)

        assert result == 2
        mock_doc1.reference.delete.assert_called_once()
        mock_doc2.reference.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_expired(self, mock_firestore_client):
        """Test cleanup with no expired tokens."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock empty query results
        mock_query = MagicMock()
        mock_query.stream.return_value = []
        mock_firestore_client.collection.return_value.where.return_value = mock_query

        result = await manager.cleanup_expired_tokens(30)

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_google_cloud_error(
        self, mock_firestore_client
    ):
        """Test cleanup with Google Cloud error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock Firestore error
        mock_firestore_client.collection.return_value.where.side_effect = (
            GoogleCloudError("Firestore error")
        )

        result = await manager.cleanup_expired_tokens(30)

        assert result == 0

    @pytest.mark.asyncio
    async def test_update_token_usage_success(self, mock_firestore_client):
        """Test successful token usage update."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        result = await manager.update_token_usage("user123")

        assert result is True
        mock_firestore_client.collection.assert_called_once_with(
            "airtable_oauth_tokens"
        )
        mock_firestore_client.collection.return_value.document.assert_called_once_with(
            "user123"
        )
        mock_doc_ref.update.assert_called_once()

        # Verify updated_at was set
        update_call = mock_doc_ref.update.call_args[0][0]
        assert "updated_at" in update_call
        assert isinstance(update_call["updated_at"], float)

    @pytest.mark.asyncio
    async def test_update_token_usage_google_cloud_error(self, mock_firestore_client):
        """Test token usage update with Google Cloud error."""
        manager = TokenManager("test-project")
        manager._db = mock_firestore_client

        # Mock Firestore error
        mock_firestore_client.collection.return_value.document.return_value.update.side_effect = GoogleCloudError(
            "Firestore error"
        )

        result = await manager.update_token_usage("user123")

        assert result is False
