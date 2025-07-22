"""Pydantic models for Airtable API responses."""

from typing import Any

from pydantic import BaseModel, Field


class AirtableBase(BaseModel):
    """Represents an Airtable base."""

    id: str
    name: str
    permission_level: str = Field(alias="permissionLevel")


class ListBasesResponse(BaseModel):
    """Response from listing Airtable bases."""

    bases: list[AirtableBase]


class FieldConfig(BaseModel):
    """Configuration for a field."""

    type: str
    options: dict[str, Any] | None = None


class AirtableField(BaseModel):
    """Represents an Airtable field."""

    id: str
    name: str
    type: str
    description: str | None = None
    options: dict[str, Any] | None = None


class AirtableTable(BaseModel):
    """Represents an Airtable table."""

    id: str
    name: str
    description: str | None = None
    primary_field_id: str = Field(alias="primaryFieldId")
    fields: list[AirtableField]
    views: list[dict[str, Any]] | None = None


class BaseSchemaResponse(BaseModel):
    """Response from getting base schema."""

    tables: list[AirtableTable]


class AirtableRecord(BaseModel):
    """Represents an Airtable record."""

    id: str
    fields: dict[str, Any]
    created_time: str | None = Field(alias="createdTime", default=None)


class ListRecordsResponse(BaseModel):
    """Response from listing records."""

    records: list[AirtableRecord]
    offset: str | None = None


class CreateRecordsRequest(BaseModel):
    """Request for creating records."""

    records: list[dict[str, dict[str, Any]]]
    typecast: bool | None = False


class CreateRecordsResponse(BaseModel):
    """Response from creating records."""

    records: list[AirtableRecord]


class UpdateRecordsRequest(BaseModel):
    """Request for updating records."""

    records: list[dict[str, Any]]
    typecast: bool | None = False


class UpdateRecordsResponse(BaseModel):
    """Response from updating records."""

    records: list[AirtableRecord]


class DeleteRecordsResponse(BaseModel):
    """Response from deleting records."""

    records: list[dict[str, Any]]


class ListRecordsOptions(BaseModel):
    """Options for listing records."""

    max_records: int | None = Field(alias="maxRecords", default=None)
    filter_by_formula: str | None = Field(alias="filterByFormula", default=None)
    view: str | None = None
    sort: list[dict[str, str]] | None = None
    fields: list[str] | None = None
    cell_format: str | None = Field(alias="cellFormat", default=None)
    time_zone: str | None = Field(alias="timeZone", default=None)
    user_locale: str | None = Field(alias="userLocale", default=None)
