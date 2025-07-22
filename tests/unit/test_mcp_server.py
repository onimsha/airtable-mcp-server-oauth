"""Unit tests for MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from airtable_mcp.mcp.server import AirtableMCPServer


class TestAirtableMCPServer:
    """Test cases for AirtableMCPServer."""

    @pytest.fixture
    def mock_oauth_provider(self):
        """Create a mock OAuth provider."""
        provider = MagicMock()
        provider.access_token = "test_access_token"
        provider.ensure_valid_token = AsyncMock(return_value=True)
        return provider

    @pytest.fixture
    def server(self, mock_oauth_provider):
        """Create a server instance for testing."""
        server = AirtableMCPServer()
        # Mock the OAuth provider on the server instance
        server.oauth_provider = mock_oauth_provider
        return server

    @pytest.mark.asyncio
    async def test_list_bases_success(self, server):
        """Test successful list bases tool."""
        mock_bases_response = {
            "bases": [
                {"id": "app123", "name": "Test Base", "permissionLevel": "create"}
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_bases.return_value = mock_bases_response
            mock_get_client.return_value = mock_client

            result = await server.list_bases()

            assert result == mock_bases_response
            mock_client.list_bases.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tables_success(self, server):
        """Test successful list tables tool."""
        mock_schema_response = {
            "tables": [
                {"id": "tbl123", "name": "Test Table", "primaryFieldId": "fld123"}
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_schema_response
            mock_get_client.return_value = mock_client

            result = await server.list_tables(base_id="app123")

            assert "tables" in result
            assert len(result["tables"]) == 1
            mock_client.get_base_schema.assert_called_once_with("app123")

    @pytest.mark.asyncio
    async def test_list_tables_with_detail_level(self, server):
        """Test list tables with detail level."""
        mock_schema_response = {
            "tables": [
                {
                    "id": "tbl123",
                    "name": "Test Table",
                    "primaryFieldId": "fld123",
                    "fields": [
                        {"id": "fld123", "name": "Primary", "type": "singleLineText"}
                    ],
                    "views": [{"id": "viw123", "name": "Grid view", "type": "grid"}],
                }
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_schema_response
            mock_get_client.return_value = mock_client

            result = await server.list_tables(base_id="app123", detail_level="full")

            assert "tables" in result
            table = result["tables"][0]
            assert "fields" in table
            assert "views" in table

    @pytest.mark.asyncio
    async def test_describe_table_success(self, server):
        """Test successful describe table tool."""
        mock_schema_response = {
            "tables": [
                {
                    "id": "tbl123",
                    "name": "Test Table",
                    "fields": [
                        {"id": "fld123", "name": "Primary", "type": "singleLineText"}
                    ],
                    "views": [{"id": "viw123", "name": "Grid view", "type": "grid"}],
                }
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_schema_response
            mock_get_client.return_value = mock_client

            result = await server.describe_table(base_id="app123", table_id="tbl123")

            assert result["id"] == "tbl123"
            assert result["name"] == "Test Table"
            assert "fields" in result
            assert "views" in result

    @pytest.mark.asyncio
    async def test_describe_table_not_found(self, server):
        """Test describe table when table not found."""
        mock_schema_response = {"tables": []}

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_schema_response
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="Table with ID 'tbl123' not found"):
                await server.describe_table(base_id="app123", table_id="tbl123")

    @pytest.mark.asyncio
    async def test_list_records_success(self, server, mock_airtable_response):
        """Test successful list records tool."""
        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_records.return_value = (
                mock_airtable_response.json.return_value
            )
            mock_get_client.return_value = mock_client

            result = await server.list_records(base_id="app123", table_id="tbl123")

            assert "records" in result
            mock_client.list_records.assert_called_once_with(
                base_id="app123",
                table_id="tbl123",
                view=None,
                fields=None,
                sort=None,
                filter_by_formula=None,
            )

    @pytest.mark.asyncio
    async def test_list_records_with_parameters(self, server, mock_airtable_response):
        """Test list records with all parameters."""
        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.list_records.return_value = (
                mock_airtable_response.json.return_value
            )
            mock_get_client.return_value = mock_client

            await server.list_records(
                base_id="app123",
                table_id="tbl123",
                view="Grid view",
                filter_by_formula="{Status} = 'Active'",
                sort=[{"field": "Name", "direction": "asc"}],
                fields=["Name", "Value"],
            )

            mock_client.list_records.assert_called_once_with(
                base_id="app123",
                table_id="tbl123",
                view="Grid view",
                fields=["Name", "Value"],
                sort=[{"field": "Name", "direction": "asc"}],
                filter_by_formula="{Status} = 'Active'",
            )

    @pytest.mark.asyncio
    async def test_get_record_success(self, server):
        """Test successful get record tool."""
        mock_record = {
            "id": "rec123",
            "fields": {"Name": "Test Record"},
            "createdTime": "2025-01-01T00:00:00.000Z",
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_record.return_value = mock_record
            mock_get_client.return_value = mock_client

            result = await server.get_record(
                base_id="app123", table_id="tbl123", record_id="rec123"
            )

            assert result == mock_record
            mock_client.get_record.assert_called_once_with("app123", "tbl123", "rec123")

    @pytest.mark.asyncio
    async def test_create_record_success(self, server):
        """Test successful create record tool."""
        mock_record = {
            "id": "rec456",
            "fields": {"Name": "New Record"},
            "createdTime": "2025-01-01T00:00:00.000Z",
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_record.return_value = mock_record
            mock_get_client.return_value = mock_client

            result = await server.create_record(
                base_id="app123",
                table_id="tbl123",
                fields={"Name": "New Record"},
                typecast=True,
            )

            assert result == mock_record
            mock_client.create_record.assert_called_once_with(
                base_id="app123",
                table_id="tbl123",
                fields={"Name": "New Record"},
                typecast=True,
            )

    @pytest.mark.asyncio
    async def test_create_records_success(self, server):
        """Test successful create records tool."""
        mock_response = {
            "records": [
                {"id": "rec456", "fields": {"Name": "Record 1"}},
                {"id": "rec789", "fields": {"Name": "Record 2"}},
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_records.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await server.create_records(
                base_id="app123",
                table_id="tbl123",
                records=[
                    {"fields": {"Name": "Record 1"}},
                    {"fields": {"Name": "Record 2"}},
                ],
            )

            assert result == mock_response
            mock_client.create_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_records_success(self, server):
        """Test successful update records tool."""
        mock_response = {
            "records": [
                {"id": "rec123", "fields": {"Name": "Updated Record"}},
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.update_records.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await server.update_records(
                base_id="app123",
                table_id="tbl123",
                records=[
                    {"id": "rec123", "fields": {"Name": "Updated Record"}},
                ],
            )

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_delete_records_success(self, server):
        """Test successful delete records tool."""
        mock_response = {
            "records": [
                {"id": "rec123", "deleted": True},
            ]
        }

        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.delete_records.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await server.delete_records(
                base_id="app123", table_id="tbl123", record_ids=["rec123"]
            )

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_search_records_success(self, server, mock_airtable_response):
        """Test successful search records tool."""
        with patch.object(server, "_get_authenticated_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_records.return_value = (
                mock_airtable_response.json.return_value
            )
            mock_get_client.return_value = mock_client

            result = await server.search_records(
                base_id="app123",
                table_id="tbl123",
                filter_by_formula="{Name} = 'Test'",
                view="Grid view",
                fields=["Name"],
            )

            assert "records" in result
            mock_client.search_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_authenticated_client_success(self, server, mock_oauth_provider):
        """Test successful authenticated client creation."""
        mock_oauth_provider.ensure_valid_token.return_value = True
        mock_oauth_provider.access_token = "test_token"

        with patch("airtable_mcp.mcp.server.AirtableClient") as mock_client_class:
            client = await server._get_authenticated_client()

            mock_client_class.assert_called_once_with(oauth_handler=mock_oauth_provider)
            assert client is not None

    @pytest.mark.asyncio
    async def test_get_authenticated_client_auth_failure(
        self, server, mock_oauth_provider
    ):
        """Test authenticated client creation with auth failure."""
        mock_oauth_provider.ensure_valid_token.return_value = False

        with pytest.raises(Exception, match="Authentication failed"):
            await server._get_authenticated_client()
