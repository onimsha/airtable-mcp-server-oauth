"""FastMCP server implementation for Airtable with OAuth 2.0 authentication using the reusable OAuth library."""

import logging
import os
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

# Import the new OAuth library
from mcp_oauth_lib import AuthContext, MCPOAuthServer, OAuthConfig
from mcp_oauth_lib.providers.airtable import (
    AirtableOAuthProvider,
    AirtableProviderConfig,
)

from ..api.client import AirtableClient
from ..api.exceptions import AirtableAPIError, AirtableAuthError
from ..api.models import ListRecordsOptions

logger = logging.getLogger(__name__)


class AirtableMCPServer:
    """FastMCP server for Airtable with OAuth 2.0 authentication.

    This server provides MCP tools for interacting with Airtable:
    - Base operations (list bases, get schema)
    - Record operations (CRUD, search)
    - Table operations (create, update)
    - Field operations (create, update)
    """

    def __init__(
        self,
        name: str = "airtable-oauth-mcp",
        version: str = "0.1.0",
        enable_oauth_endpoints: bool = True,
    ):
        """Initialize the Airtable MCP server.

        Args:
            name: Server name
            version: Server version
            enable_oauth_endpoints: Whether to enable OAuth endpoints for metadata discovery
        """
        self.mcp = FastMCP(name, version=version)
        self.enable_oauth_endpoints = enable_oauth_endpoints
        self.oauth_server: MCPOAuthServer | None = None
        self.server_host: str = "localhost"
        self.server_port: int = 8000

        # Initialize OAuth server if endpoints are enabled
        if enable_oauth_endpoints:
            self._initialize_oauth_server()

        # Register all MCP tools
        self._register_tools()

        # Register OAuth endpoints if enabled
        if enable_oauth_endpoints and self.oauth_server:
            self.oauth_server.register_oauth_endpoints(self.mcp)

    def _initialize_oauth_server(self) -> None:
        """Initialize the OAuth server using the reusable OAuth library."""
        try:
            # Get OAuth configuration from environment variables
            client_id = os.getenv("AIRTABLE_CLIENT_ID")
            client_secret = os.getenv("AIRTABLE_CLIENT_SECRET")
            redirect_uri = os.getenv(
                "AIRTABLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
            )
            scope = os.getenv(
                "AIRTABLE_SCOPE",
                "data.records:read data.records:write data.recordComments:read data.recordComments:write schema.bases:read schema.bases:write webhook:manage",
            )

            if not client_id or not client_secret:
                logger.warning(
                    "OAuth endpoints disabled: AIRTABLE_CLIENT_ID and AIRTABLE_CLIENT_SECRET must be set"
                )
                self.enable_oauth_endpoints = False
                return

            # Create provider configuration
            provider_config = AirtableProviderConfig(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
            )

            # Create OAuth server configuration
            oauth_config = OAuthConfig(
                server_name="airtable-oauth-mcp",
                server_version="0.1.0",
                host=self.server_host,
                port=self.server_port,
                # TODO: Add token manager support if needed
                # token_manager=token_manager
            )

            # Create provider and OAuth server
            provider = AirtableOAuthProvider(provider_config)
            self.oauth_server = MCPOAuthServer(oauth_config, provider)

            logger.info("OAuth server initialized successfully with Airtable provider")

        except Exception as e:
            logger.error(f"Failed to initialize OAuth server: {e}")
            self.enable_oauth_endpoints = False

    def _get_oauth_provider(self) -> AirtableOAuthProvider | None:
        """Get the Airtable OAuth provider instance.

        Returns:
            Airtable OAuth provider or None if OAuth is disabled
        """
        if self.oauth_server:
            return self.oauth_server.provider
        return None

    def _register_tools(self) -> None:
        """Register all MCP tools with FastMCP."""

        # Base operations
        @self.mcp.tool(description="List all accessible Airtable bases")
        async def list_bases() -> list[dict[str, Any]]:
            """List all accessible Airtable bases."""
            client = await self._get_authenticated_client()
            response = await client.list_bases()
            return [
                {
                    "id": base.id,
                    "name": base.name,
                    "permissionLevel": base.permission_level,
                }
                for base in response.bases
            ]

        @self.mcp.tool(description="List tables in a specific base")
        async def list_tables(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            detail_level: Annotated[
                Literal["tableIdentifiersOnly", "withFieldInfo"],
                Field(
                    description="Level of detail to include in response",
                    default="tableIdentifiersOnly",
                ),
            ] = "tableIdentifiersOnly",
        ) -> list[dict[str, Any]]:
            """List tables in a specific base with optional field information."""
            client = await self._get_authenticated_client()
            schema = await client.get_base_schema(base_id)

            if detail_level == "tableIdentifiersOnly":
                return [
                    {
                        "id": table.id,
                        "name": table.name,
                    }
                    for table in schema.tables
                ]
            else:  # withFieldInfo
                return [
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

        @self.mcp.tool(description="Get detailed information about a specific table")
        async def describe_table(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
        ) -> dict[str, Any]:
            """Get detailed information about a specific table including all fields."""
            client = await self._get_authenticated_client()
            schema = await client.get_base_schema(base_id)

            # Find the specific table
            table = next(
                (t for t in schema.tables if t.id == table_id or t.name == table_id),
                None,
            )

            if not table:
                raise AirtableAPIError(
                    f"Table '{table_id}' not found in base '{base_id}'"
                )

            return {
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

        # Record operations
        @self.mcp.tool(description="List records from a table with optional filtering")
        async def list_records(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            view: Annotated[str | None, Field(description="View name or ID")] = None,
            filter_by_formula: Annotated[
                str | None, Field(description="Airtable formula for filtering")
            ] = None,
            sort: Annotated[
                list[dict[str, str]] | None,
                Field(
                    description="Sort configuration - array of {field: string, direction: 'asc'|'desc'}"
                ),
            ] = None,
            fields: Annotated[
                str | list[str] | None,
                Field(
                    description="Specific fields to include (field name or array of field names)"
                ),
            ] = None,
        ) -> list[dict[str, Any]]:
            """List records from a table with optional filtering and pagination."""
            client = await self._get_authenticated_client()

            # Normalize fields parameter
            normalized_fields = None
            if fields is not None:
                if isinstance(fields, str):
                    # Check if it's a JSON-encoded array string
                    if fields.startswith("[") and fields.endswith("]"):
                        try:
                            import json

                            normalized_fields = json.loads(fields)
                        except (json.JSONDecodeError, ValueError):
                            # If JSON parsing fails, treat as single field name
                            normalized_fields = [fields]
                    else:
                        # Single field name
                        normalized_fields = [fields]
                else:
                    normalized_fields = fields

            options = ListRecordsOptions(
                view=view,
                sort=sort,
                fields=normalized_fields,
            )
            if filter_by_formula:
                options.filter_by_formula = filter_by_formula

            records = await client.list_records(base_id, table_id, options)

            return [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in records
            ]

        @self.mcp.tool(description="Get a specific record by ID")
        async def get_record(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            record_id: Annotated[str, Field(description="The record ID")],
        ) -> dict[str, Any]:
            """Get a specific record by ID."""
            client = await self._get_authenticated_client()
            record = await client.get_record(base_id, table_id, record_id)

            return {
                "id": record.id,
                "fields": record.fields,
                "createdTime": record.created_time,
            }

        @self.mcp.tool(description="Create a single record")
        async def create_record(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            fields: Annotated[
                dict[str, Any], Field(description="Field values for the new record")
            ],
            typecast: Annotated[
                bool, Field(description="Enable automatic data conversion")
            ] = False,
        ) -> dict[str, Any]:
            """Create a single record in a table."""
            client = await self._get_authenticated_client()

            records = await client.create_records(
                base_id,
                table_id,
                [{"fields": fields}],
                typecast,
            )

            record = records[0]
            return {
                "id": record.id,
                "fields": record.fields,
                "createdTime": record.created_time,
            }

        @self.mcp.tool(description="Create multiple records")
        async def create_records(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            records: Annotated[
                list[dict[str, Any]], Field(description="List of records to create")
            ],
            typecast: Annotated[
                bool, Field(description="Enable automatic data conversion")
            ] = False,
        ) -> list[dict[str, Any]]:
            """Create multiple records in a table."""
            client = await self._get_authenticated_client()

            created_records = await client.create_records(
                base_id,
                table_id,
                records,
                typecast,
            )

            return [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in created_records
            ]

        @self.mcp.tool(description="Update multiple records")
        async def update_records(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            records: Annotated[
                list[dict[str, Any]], Field(description="List of record updates")
            ],
            typecast: Annotated[
                bool, Field(description="Enable automatic data conversion")
            ] = False,
        ) -> list[dict[str, Any]]:
            """Update multiple records in a table."""
            client = await self._get_authenticated_client()

            updated_records = await client.update_records(
                base_id,
                table_id,
                records,
                typecast,
            )

            return [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in updated_records
            ]

        @self.mcp.tool(description="Delete multiple records")
        async def delete_records(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            record_ids: Annotated[
                list[str], Field(description="List of record IDs to delete")
            ],
        ) -> list[str]:
            """Delete multiple records from a table."""
            client = await self._get_authenticated_client()

            deleted_ids = await client.delete_records(
                base_id,
                table_id,
                record_ids,
            )

            return deleted_ids

        @self.mcp.tool(description="Search records using a formula filter")
        async def search_records(
            base_id: Annotated[str, Field(description="The Airtable base ID")],
            table_id: Annotated[str, Field(description="The table ID or name")],
            filter_by_formula: Annotated[
                str, Field(description="Airtable formula for filtering")
            ],
            view: Annotated[str | None, Field(description="View name or ID")] = None,
            fields: Annotated[
                str | list[str] | None,
                Field(
                    description="Specific fields to include (field name or array of field names)"
                ),
            ] = None,
        ) -> list[dict[str, Any]]:
            """Search records using a formula filter."""
            client = await self._get_authenticated_client()

            # Normalize fields parameter
            normalized_fields = None
            if fields is not None:
                if isinstance(fields, str):
                    # Check if it's a JSON-encoded array string
                    if fields.startswith("[") and fields.endswith("]"):
                        try:
                            import json

                            normalized_fields = json.loads(fields)
                        except (json.JSONDecodeError, ValueError):
                            # If JSON parsing fails, treat as single field name
                            normalized_fields = [fields]
                    else:
                        # Single field name
                        normalized_fields = [fields]
                else:
                    normalized_fields = fields

            options = ListRecordsOptions(
                view=view,
                fields=normalized_fields,
            )

            records = await client.search_records(
                base_id,
                table_id,
                filter_by_formula,
                options,
            )

            return [
                {
                    "id": record.id,
                    "fields": record.fields,
                    "createdTime": record.created_time,
                }
                for record in records
            ]

    async def _get_authenticated_client(self) -> AirtableClient:
        """Get an authenticated Airtable client using access token from context.

        Returns:
            Authenticated AirtableClient instance

        Raises:
            AirtableAuthError: If authentication fails
        """
        # Get access token from authentication context (set by middleware)
        access_token = AuthContext.require_access_token()

        try:
            # Use the OAuth provider
            provider = self._get_oauth_provider()
            if not provider:
                raise AirtableAuthError(
                    "OAuth provider not available - ensure OAuth endpoints are enabled and credentials are configured"
                )

            # Set the access token in the provider
            provider.access_token = access_token

            return AirtableClient(provider)

        except Exception as e:
            logger.error(f"Failed to create authenticated client: {e}")
            raise AirtableAuthError(f"Authentication failed: {e}") from e

    def run(
        self,
        transport: str = "stdio",
        host: str = "0.0.0.0",
        port: int = 8000,
        **kwargs,
    ) -> None:
        """Run the FastMCP server.

        Args:
            transport: Transport type ("stdio" or "http")
            host: Host to bind to (for HTTP transport)
            port: Port to bind to (for HTTP transport)
            **kwargs: Additional arguments passed to FastMCP.run()
        """
        # Store server configuration for OAuth endpoint URLs
        self.server_host = host if host != "0.0.0.0" else "localhost"
        self.server_port = port

        # Update OAuth server configuration
        if self.oauth_server and transport.lower() == "http":
            self.oauth_server.config.host = self.server_host
            self.oauth_server.config.port = port
            self.oauth_server.config.base_url = f"http://{self.server_host}:{port}"

        logger.info(f"Starting Airtable OAuth MCP Server with {transport} transport...")

        if transport.lower() == "http":
            logger.info(
                f"HTTP server will be available at: http://{self.server_host}:{port}"
            )

            # Add OAuth authentication middleware for HTTP transport
            middleware = kwargs.get("middleware", [])
            if self.enable_oauth_endpoints and self.oauth_server:
                from mcp_oauth_lib.auth.middleware import OAuthAuthenticationMiddleware

                # Middleware format for Starlette: (middleware_class, args, kwargs)
                middleware.append(
                    (
                        OAuthAuthenticationMiddleware,
                        [],
                        {"oauth_base_url": f"http://{self.server_host}:{port}"},
                    )
                )
                kwargs["middleware"] = middleware

            # Use FastMCP's built-in HTTP transport
            self.mcp.run(transport="http", host=host, port=port, **kwargs)
        else:
            # Default STDIO transport
            self.mcp.run(**kwargs)
