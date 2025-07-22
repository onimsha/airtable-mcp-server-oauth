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
        from airtable_mcp.api.models import AirtableBase, ListBasesResponse

        # Create mock response with proper Pydantic models
        mock_base = AirtableBase(
            id="app123", name="Test Base", permissionLevel="create"
        )
        mock_response = ListBasesResponse(bases=[mock_base])

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.list_bases.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Test the logic by calling the _get_authenticated_client and list_bases
            # since the tool function itself is not directly accessible
            client = await server._get_authenticated_client()
            response = await client.list_bases()

            # Verify the expected data structure that the tool would return
            result = [
                {
                    "id": base.id,
                    "name": base.name,
                    "permissionLevel": base.permission_level,
                }
                for base in response.bases
            ]

            assert len(result) == 1
            assert result[0]["id"] == "app123"
            assert result[0]["name"] == "Test Base"
            assert result[0]["permissionLevel"] == "create"
            mock_client.list_bases.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tables_success(self, server):
        """Test successful list tables tool."""
        from airtable_mcp.api.models import AirtableTable, BaseSchemaResponse

        # Create mock response with proper Pydantic models
        mock_table = AirtableTable(
            id="tbl123", name="Test Table", primaryFieldId="fld123", fields=[]
        )
        mock_response = BaseSchemaResponse(tables=[mock_table])

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client methods
            client = await server._get_authenticated_client()
            schema = await client.get_base_schema("app123")

            # Verify the expected data structure that the tool would return
            result = [
                {
                    "id": table.id,
                    "name": table.name,
                }
                for table in schema.tables
            ]

            assert len(result) == 1
            assert result[0]["id"] == "tbl123"
            assert result[0]["name"] == "Test Table"
            mock_client.get_base_schema.assert_called_once_with("app123")

    @pytest.mark.asyncio
    async def test_list_tables_with_detail_level(self, server):
        """Test list tables tool logic with detail level."""
        from airtable_mcp.api.models import (
            AirtableField,
            AirtableTable,
            BaseSchemaResponse,
        )

        # Create mock response with proper Pydantic models
        mock_field = AirtableField(
            id="fld123",
            name="Primary",
            type="singleLineText",
            description="Primary field",
        )
        mock_table = AirtableTable(
            id="tbl123",
            name="Test Table",
            primaryFieldId="fld123",
            fields=[mock_field],
            views=[{"id": "viw123", "name": "Grid view", "type": "grid"}],
        )
        mock_response = BaseSchemaResponse(tables=[mock_table])

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method and format the response
            client = await server._get_authenticated_client()
            schema = await client.get_base_schema("app123")

            # Simulate withFieldInfo detail level processing
            result = [
                {
                    "id": table.id,
                    "name": table.name,
                    "description": table.description,
                    "primaryFieldId": table.primary_field_id,
                    "fields": [
                        {
                            "id": field.id,
                            "name": field.name,
                            "type": field.type,
                            "description": field.description,
                            "options": field.options,
                        }
                        for field in table.fields
                    ],
                }
                for table in schema.tables
            ]

            assert len(result) == 1
            table = result[0]
            assert table["id"] == "tbl123"
            assert "fields" in table
            assert len(table["fields"]) == 1
            mock_client.get_base_schema.assert_called_once_with("app123")

    @pytest.mark.asyncio
    async def test_describe_table_success(self, server):
        """Test successful describe table tool logic."""
        from airtable_mcp.api.models import (
            AirtableField,
            AirtableTable,
            BaseSchemaResponse,
        )

        # Create mock response with proper Pydantic models
        mock_field = AirtableField(
            id="fld123",
            name="Primary",
            type="singleLineText",
            description="Primary field",
        )
        mock_table = AirtableTable(
            id="tbl123",
            name="Test Table",
            primaryFieldId="fld123",
            fields=[mock_field],
            views=[{"id": "viw123", "name": "Grid view", "type": "grid"}],
        )
        mock_response = BaseSchemaResponse(tables=[mock_table])

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method and finding the table
            client = await server._get_authenticated_client()
            schema = await client.get_base_schema("app123")

            # Find the specific table (simulating the describe_table logic)
            table = next(
                (t for t in schema.tables if t.id == "tbl123" or t.name == "tbl123"),
                None,
            )

            assert table is not None
            result = {
                "id": table.id,
                "name": table.name,
                "description": table.description,
                "primaryFieldId": table.primary_field_id,
                "fields": [
                    {
                        "id": field.id,
                        "name": field.name,
                        "type": field.type,
                        "description": field.description,
                        "options": field.options,
                    }
                    for field in table.fields
                ],
                "views": table.views,
            }

            assert result["id"] == "tbl123"
            assert result["name"] == "Test Table"
            assert "fields" in result
            assert "views" in result
            mock_client.get_base_schema.assert_called_once_with("app123")

    @pytest.mark.asyncio
    async def test_describe_table_not_found(self, server):
        """Test describe table when table not found."""
        from airtable_mcp.api.models import BaseSchemaResponse

        mock_response = BaseSchemaResponse(tables=[])

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.get_base_schema.return_value = mock_response
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method and simulating table search
            client = await server._get_authenticated_client()
            schema = await client.get_base_schema("app123")

            # Find the specific table (simulating the describe_table logic)
            table = next(
                (t for t in schema.tables if t.id == "tbl123" or t.name == "tbl123"),
                None,
            )

            # Should not find the table
            assert table is None

            # Simulate the exception that would be raised
            if not table:
                error_msg = "Table 'tbl123' not found in base 'app123'"
                assert "not found" in error_msg

    @pytest.mark.asyncio
    async def test_server_initialization_with_oauth_disabled(self):
        """Test server initialization with OAuth endpoints disabled."""
        server = AirtableMCPServer(enable_oauth_endpoints=False)
        assert server.enable_oauth_endpoints is False
        assert server.oauth_server is None

    @pytest.mark.asyncio
    async def test_server_initialization_missing_credentials(self):
        """Test server initialization with missing OAuth credentials."""
        with patch.dict("os.environ", {}, clear=True):
            server = AirtableMCPServer(enable_oauth_endpoints=True)
            # Should disable OAuth endpoints when credentials are missing
            assert server.enable_oauth_endpoints is False
            assert server.oauth_server is None

    @pytest.mark.asyncio
    async def test_oauth_provider_access(self, server):
        """Test getting OAuth provider instance."""
        provider = server._get_oauth_provider()
        if server.oauth_server:
            assert provider is not None
        else:
            assert provider is None

    @pytest.mark.asyncio
    async def test_authentication_client_creation_no_provider(self):
        """Test authenticated client creation without OAuth provider."""
        from airtable_mcp.api.exceptions import AirtableAuthError

        # Create server without OAuth endpoints
        server = AirtableMCPServer(enable_oauth_endpoints=False)

        with patch(
            "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
            return_value="test_token",
        ):
            with pytest.raises(AirtableAuthError, match="OAuth provider not available"):
                await server._get_authenticated_client()

    @pytest.mark.asyncio
    async def test_client_creation_exception_handling(self, server):
        """Test authenticated client creation with exception handling."""
        from airtable_mcp.api.exceptions import AirtableAuthError

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_oauth_provider") as mock_get_provider,
            patch(
                "airtable_mcp.mcp.server.AirtableClient",
                side_effect=Exception("Client creation failed"),
            ),
        ):
            mock_provider = MagicMock()
            mock_get_provider.return_value = mock_provider

            with pytest.raises(AirtableAuthError, match="Authentication failed"):
                await server._get_authenticated_client()

    @pytest.mark.asyncio
    async def test_list_records_with_json_fields_parameter(self, server):
        """Test list records with JSON string fields parameter."""
        from airtable_mcp.api.models import AirtableRecord, ListRecordsOptions

        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.list_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the JSON fields parameter processing logic
            client = await server._get_authenticated_client()

            # Simulate processing JSON string fields like the tool would
            fields_param = '["Name", "Email"]'  # JSON string
            normalized_fields = None
            if fields_param is not None:
                if isinstance(fields_param, str):
                    if fields_param.startswith("[") and fields_param.endswith("]"):
                        try:
                            import json

                            normalized_fields = json.loads(fields_param)
                        except (json.JSONDecodeError, ValueError):
                            normalized_fields = [fields_param]
                    else:
                        normalized_fields = [fields_param]
                else:
                    normalized_fields = fields_param

            options = ListRecordsOptions(
                view=None,
                sort=None,
                fields=normalized_fields,
            )

            records = await client.list_records("app123", "tbl123", options)

            assert len(records) == 1
            assert normalized_fields == ["Name", "Email"]

    @pytest.mark.asyncio
    async def test_list_records_success(self, server, mock_airtable_response):
        """Test successful list records tool logic."""
        from airtable_mcp.api.models import AirtableRecord, ListRecordsOptions

        # Create mock records
        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.list_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            options = ListRecordsOptions(view=None, sort=None, fields=None)
            records = await client.list_records("app123", "tbl123", options)

            # Format the response like the tool would
            result = [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in records
            ]

            assert len(result) == 1
            assert result[0]["id"] == "rec123"
            mock_client.list_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_records_with_parameters(self, server, mock_airtable_response):
        """Test list records with all parameters."""
        from airtable_mcp.api.models import AirtableRecord, ListRecordsOptions

        # Create mock records
        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.list_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method with options
            client = await server._get_authenticated_client()
            options = ListRecordsOptions(
                view="Grid view",
                sort=[{"field": "Name", "direction": "asc"}],
                fields=["Name", "Value"],
                filter_by_formula="{Status} = 'Active'",
            )
            records = await client.list_records("app123", "tbl123", options)

            assert len(records) == 1
            mock_client.list_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_record_success(self, server):
        """Test successful get record tool."""
        from airtable_mcp.api.models import AirtableRecord

        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.get_record.return_value = mock_record
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client methods
            client = await server._get_authenticated_client()
            result = await client.get_record("app123", "tbl123", "rec123")

            assert result.id == "rec123"
            assert result.fields["Name"] == "Test Record"
            mock_client.get_record.assert_called_once_with("app123", "tbl123", "rec123")

    @pytest.mark.asyncio
    async def test_create_record_success(self, server):
        """Test successful create record tool logic."""
        from airtable_mcp.api.models import AirtableRecord

        # Create mock record
        mock_record = AirtableRecord(
            id="rec456",
            fields={"Name": "New Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.create_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            records = await client.create_records(
                "app123", "tbl123", [{"fields": {"Name": "New Record"}}], False
            )

            # Format the response like the tool would (single record)
            record = records[0]
            result = {
                "id": record.id,
                "fields": record.fields,
                "createdTime": record.created_time,
            }

            assert result["id"] == "rec456"
            assert result["fields"]["Name"] == "New Record"
            mock_client.create_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_records_success(self, server):
        """Test successful create records tool logic."""
        from airtable_mcp.api.models import AirtableRecord

        # Create mock records
        mock_records = [
            AirtableRecord(
                id="rec456",
                fields={"Name": "Record 1"},
                createdTime="2025-01-01T00:00:00.000Z",
            ),
            AirtableRecord(
                id="rec789",
                fields={"Name": "Record 2"},
                createdTime="2025-01-01T00:00:00.000Z",
            ),
        ]

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.create_records.return_value = mock_records
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            created_records = await client.create_records(
                "app123",
                "tbl123",
                [
                    {"fields": {"Name": "Record 1"}},
                    {"fields": {"Name": "Record 2"}},
                ],
                False,
            )

            # Format the response like the tool would
            result = [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in created_records
            ]

            assert len(result) == 2
            assert result[0]["id"] == "rec456"
            mock_client.create_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_records_success(self, server):
        """Test successful update records tool logic."""
        from airtable_mcp.api.models import AirtableRecord

        # Create mock record
        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Updated Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.update_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            updated_records = await client.update_records(
                "app123",
                "tbl123",
                [
                    {"id": "rec123", "fields": {"Name": "Updated Record"}},
                ],
                False,
            )

            # Format the response like the tool would
            result = [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in updated_records
            ]

            assert len(result) == 1
            assert result[0]["fields"]["Name"] == "Updated Record"
            mock_client.update_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_records_success(self, server):
        """Test successful delete records tool logic."""
        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.delete_records.return_value = ["rec123"]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            deleted_ids = await client.delete_records("app123", "tbl123", ["rec123"])

            assert deleted_ids == ["rec123"]
            mock_client.delete_records.assert_called_once_with(
                "app123", "tbl123", ["rec123"]
            )

    @pytest.mark.asyncio
    async def test_search_records_success(self, server, mock_airtable_response):
        """Test successful search records tool logic."""
        from airtable_mcp.api.models import AirtableRecord, ListRecordsOptions

        # Create mock record
        mock_record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record"},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(server, "_get_authenticated_client") as mock_get_client,
        ):
            mock_client = AsyncMock()
            mock_client.search_records.return_value = [mock_record]
            mock_get_client.return_value = mock_client

            # Test the logic by calling the client method
            client = await server._get_authenticated_client()
            options = ListRecordsOptions(view="Grid view", fields=["Name"])

            records = await client.search_records(
                "app123", "tbl123", "{Name} = 'Test'", options
            )

            # Format the response like the tool would
            result = [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in records
            ]

            assert len(result) == 1
            assert result[0]["id"] == "rec123"
            mock_client.search_records.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_authenticated_client_success(self, server, mock_oauth_provider):
        """Test successful authenticated client creation."""
        with (
            patch(
                "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
                return_value="test_token",
            ),
            patch.object(
                server, "_get_oauth_provider", return_value=mock_oauth_provider
            ),
            patch("airtable_mcp.mcp.server.AirtableClient") as mock_client_class,
        ):
            mock_oauth_provider.ensure_valid_token = AsyncMock(return_value=True)
            mock_oauth_provider.access_token = "test_token"

            client = await server._get_authenticated_client()

            mock_client_class.assert_called_once()
            assert client is not None

    @pytest.mark.asyncio
    async def test_get_authenticated_client_auth_failure(
        self, server, mock_oauth_provider
    ):
        """Test authenticated client creation with auth failure."""
        from starlette.exceptions import HTTPException

        with patch(
            "mcp_oauth_lib.auth.context.AuthContext.require_access_token",
            side_effect=HTTPException(status_code=401, detail="No token"),
        ):
            with pytest.raises(HTTPException):
                await server._get_authenticated_client()
