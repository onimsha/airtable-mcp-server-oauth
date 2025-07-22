"""Unit tests for Airtable API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from airtable_mcp.api.client import AirtableClient
from airtable_mcp.api.exceptions import (
    AirtableAPIError,
    AirtableAuthError,
    AirtableRateLimitError,
)


class TestAirtableClient:
    """Test cases for AirtableClient."""

    @pytest.fixture
    def mock_oauth_handler(self):
        """Create a mock OAuth handler."""
        handler = MagicMock()
        handler.access_token = "test_access_token"
        handler.ensure_valid_token = AsyncMock(return_value=True)
        return handler

    @pytest.fixture
    def client(self, mock_oauth_handler):
        """Create a client instance for testing."""
        return AirtableClient(oauth_handler=mock_oauth_handler)

    def test_initialization(self, mock_oauth_handler):
        """Test client initialization."""
        client = AirtableClient(
            oauth_handler=mock_oauth_handler,
            base_url="https://custom.api.url",
            timeout=60,
            max_retries=5,
        )

        assert client.oauth_handler == mock_oauth_handler
        assert client.base_url == "https://custom.api.url"
        assert client.timeout == 60
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_make_request_success(self, client, mock_airtable_response):
        """Test successful API request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_airtable_response

            result = await client._make_request("GET", "/v0/bases")

            assert result == mock_airtable_response.json.return_value
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_auth_error(self, client):
        """Test API request with authentication error."""
        client.oauth_handler.ensure_valid_token.return_value = False

        with pytest.raises(AirtableAuthError):
            await client._make_request("GET", "/v0/bases")

    @pytest.mark.asyncio
    async def test_make_request_rate_limit(self, client):
        """Test API request with rate limit error."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 429
        mock_response.text = "Rate limited"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            with pytest.raises(AirtableRateLimitError):
                await client._make_request("GET", "/v0/bases")

    @pytest.mark.asyncio
    async def test_make_request_api_error(self, client):
        """Test API request with general API error."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            with pytest.raises(AirtableAPIError):
                await client._make_request("GET", "/v0/bases")

    @pytest.mark.asyncio
    async def test_make_request_with_retry(self, client):
        """Test API request with retry logic."""
        # First call fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.is_success = False
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server error"

        mock_response_success = MagicMock()
        mock_response_success.is_success = True
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = [
                mock_response_fail,
                mock_response_success,
            ]

            with patch("asyncio.sleep"):  # Mock sleep to speed up test
                result = await client._make_request("GET", "/v0/bases")

            assert result == {"result": "success"}
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_list_bases_success(self, client, mock_airtable_response):
        """Test successful list bases operation."""
        mock_airtable_response.json.return_value = {
            "bases": [
                {"id": "app123", "name": "Test Base", "permissionLevel": "create"}
            ]
        }

        with patch.object(
            client,
            "_make_request",
            return_value=mock_airtable_response.json.return_value,
        ):
            result = await client.list_bases()

            assert "bases" in result
            assert len(result["bases"]) == 1
            assert result["bases"][0]["id"] == "app123"

    @pytest.mark.asyncio
    async def test_get_base_schema_success(self, client, mock_airtable_response):
        """Test successful get base schema operation."""
        mock_airtable_response.json.return_value = {
            "tables": [{"id": "tbl123", "name": "Test Table", "fields": []}]
        }

        with patch.object(
            client,
            "_make_request",
            return_value=mock_airtable_response.json.return_value,
        ):
            result = await client.get_base_schema("app123")

            assert "tables" in result
            assert len(result["tables"]) == 1
            assert result["tables"][0]["id"] == "tbl123"

    @pytest.mark.asyncio
    async def test_list_records_success(self, client, mock_airtable_response):
        """Test successful list records operation."""
        with patch.object(
            client,
            "_make_request",
            return_value=mock_airtable_response.json.return_value,
        ):
            result = await client.list_records("app123", "tbl123")

            assert "records" in result
            assert len(result["records"]) == 1
            assert result["records"][0]["id"] == "rec123"

    @pytest.mark.asyncio
    async def test_list_records_with_options(self, client, mock_airtable_response):
        """Test list records with filtering options."""
        with patch.object(
            client,
            "_make_request",
            return_value=mock_airtable_response.json.return_value,
        ) as mock_request:
            await client.list_records(
                base_id="app123",
                table_id="tbl123",
                view="Grid view",
                fields=["Name", "Value"],
                sort=[{"field": "Name", "direction": "asc"}],
                filter_by_formula="{Status} = 'Active'",
            )

            # Verify the request was made with proper parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"  # method
            assert "/app123/tbl123" in call_args[0][1]  # endpoint
            assert call_args[1]["params"]["view"] == "Grid view"

    @pytest.mark.asyncio
    async def test_get_record_success(self, client):
        """Test successful get record operation."""
        mock_record = {
            "id": "rec123",
            "fields": {"Name": "Test Record"},
            "createdTime": "2025-01-01T00:00:00.000Z",
        }

        with patch.object(client, "_make_request", return_value=mock_record):
            result = await client.get_record("app123", "tbl123", "rec123")

            assert result["id"] == "rec123"
            assert result["fields"]["Name"] == "Test Record"

    @pytest.mark.asyncio
    async def test_create_record_success(self, client):
        """Test successful create record operation."""
        mock_response = {
            "id": "rec456",
            "fields": {"Name": "New Record"},
            "createdTime": "2025-01-01T00:00:00.000Z",
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.create_record(
                base_id="app123", table_id="tbl123", fields={"Name": "New Record"}
            )

            assert result["id"] == "rec456"
            assert result["fields"]["Name"] == "New Record"

    @pytest.mark.asyncio
    async def test_create_records_success(self, client):
        """Test successful create records operation."""
        mock_response = {
            "records": [
                {"id": "rec456", "fields": {"Name": "Record 1"}},
                {"id": "rec789", "fields": {"Name": "Record 2"}},
            ]
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.create_records(
                base_id="app123",
                table_id="tbl123",
                records=[
                    {"fields": {"Name": "Record 1"}},
                    {"fields": {"Name": "Record 2"}},
                ],
            )

            assert len(result["records"]) == 2
            assert result["records"][0]["id"] == "rec456"

    @pytest.mark.asyncio
    async def test_update_records_success(self, client):
        """Test successful update records operation."""
        mock_response = {
            "records": [
                {"id": "rec123", "fields": {"Name": "Updated Record"}},
            ]
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.update_records(
                base_id="app123",
                table_id="tbl123",
                records=[
                    {"id": "rec123", "fields": {"Name": "Updated Record"}},
                ],
            )

            assert len(result["records"]) == 1
            assert result["records"][0]["fields"]["Name"] == "Updated Record"

    @pytest.mark.asyncio
    async def test_delete_records_success(self, client):
        """Test successful delete records operation."""
        mock_response = {
            "records": [
                {"id": "rec123", "deleted": True},
            ]
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.delete_records(
                base_id="app123", table_id="tbl123", record_ids=["rec123"]
            )

            assert len(result["records"]) == 1
            assert result["records"][0]["deleted"] is True

    @pytest.mark.asyncio
    async def test_search_records_success(self, client, mock_airtable_response):
        """Test successful search records operation."""
        with patch.object(
            client,
            "_make_request",
            return_value=mock_airtable_response.json.return_value,
        ):
            result = await client.search_records(
                base_id="app123",
                table_id="tbl123",
                search_term="test",
                field_ids=["fld123"],
                max_records=10,
            )

            assert "records" in result
            assert len(result["records"]) == 1
