"""Pydantic schemas for MCP tool arguments and responses."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class BaseArgs(BaseModel):
    """Base arguments class for MCP tools."""

    pass


# ListBasesArgs removed - list_bases tool requires no arguments since OAuth middleware handles authentication


class ListTablesArgs(BaseArgs):
    """Arguments for list_tables tool."""

    base_id: str = Field(description="The Airtable base ID")
    detail_level: Literal["tableIdentifiersOnly", "withFieldInfo"] = Field(
        default="tableIdentifiersOnly",
        description="Level of detail to include in response",
    )


class DescribeTableArgs(BaseArgs):
    """Arguments for describe_table tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")


class ListRecordsArgs(BaseArgs):
    """Arguments for list_records tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    view: str | None = Field(default=None, description="View name or ID")
    max_records: int | None = Field(
        default=None, description="Maximum number of records to return"
    )
    filter_by_formula: str | None = Field(
        default=None, description="Airtable formula for filtering"
    )
    sort: list[dict[str, str]] | None = Field(
        default=None, description="Sort configuration"
    )
    fields: list[str] | None = Field(
        default=None, description="Specific fields to include"
    )


class GetRecordArgs(BaseArgs):
    """Arguments for get_record tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    record_id: str = Field(description="The record ID")


class CreateRecordArgs(BaseArgs):
    """Arguments for create_record tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    fields: dict[str, Any] = Field(description="Field values for the new record")
    typecast: bool | None = Field(
        default=False, description="Enable automatic data conversion"
    )


class CreateRecordsArgs(BaseArgs):
    """Arguments for create_records tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    records: list[dict[str, Any]] = Field(description="List of records to create")
    typecast: bool | None = Field(
        default=False, description="Enable automatic data conversion"
    )


class UpdateRecordsArgs(BaseArgs):
    """Arguments for update_records tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    records: list[dict[str, Any]] = Field(description="List of record updates")
    typecast: bool | None = Field(
        default=False, description="Enable automatic data conversion"
    )


class DeleteRecordsArgs(BaseArgs):
    """Arguments for delete_records tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    record_ids: list[str] = Field(description="List of record IDs to delete")


class SearchRecordsArgs(BaseArgs):
    """Arguments for search_records tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID or name")
    filter_by_formula: str = Field(description="Airtable formula for filtering")
    max_records: int | None = Field(
        default=None, description="Maximum number of records to return"
    )
    view: str | None = Field(default=None, description="View name or ID")
    fields: list[str] | None = Field(
        default=None, description="Specific fields to include"
    )


class CreateTableArgs(BaseModel):
    """Arguments for create_table tool."""

    base_id: str = Field(description="The Airtable base ID")
    name: str = Field(description="Name for the new table")
    description: str | None = Field(
        default=None, description="Description for the table"
    )
    fields: list[dict[str, Any]] = Field(description="Field definitions for the table")


class UpdateTableArgs(BaseModel):
    """Arguments for update_table tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID")
    name: str | None = Field(default=None, description="New name for the table")
    description: str | None = Field(
        default=None, description="New description for the table"
    )


class CreateFieldArgs(BaseModel):
    """Arguments for create_field tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID")
    name: str = Field(description="Name for the new field")
    type: str = Field(description="Field type")
    description: str | None = Field(
        default=None, description="Description for the field"
    )
    options: dict[str, Any] | None = Field(default=None, description="Field options")


class UpdateFieldArgs(BaseModel):
    """Arguments for update_field tool."""

    base_id: str = Field(description="The Airtable base ID")
    table_id: str = Field(description="The table ID")
    field_id: str = Field(description="The field ID")
    name: str | None = Field(default=None, description="New name for the field")
    description: str | None = Field(
        default=None, description="New description for the field"
    )
