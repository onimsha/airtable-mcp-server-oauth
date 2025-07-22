"""Pydantic models for Airtable API responses."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AirtableBase(BaseModel):
    """Represents an Airtable base."""
    id: str
    name: str
    permission_level: str = Field(alias="permissionLevel")


class ListBasesResponse(BaseModel):
    """Response from listing Airtable bases."""
    bases: List[AirtableBase]


class FieldConfig(BaseModel):
    """Configuration for a field."""
    type: str
    options: Optional[Dict[str, Any]] = None


class AirtableField(BaseModel):
    """Represents an Airtable field."""
    id: str
    name: str
    type: str
    description: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class AirtableTable(BaseModel):
    """Represents an Airtable table."""
    id: str
    name: str
    description: Optional[str] = None
    primary_field_id: str = Field(alias="primaryFieldId")
    fields: List[AirtableField]
    views: Optional[List[Dict[str, Any]]] = None


class BaseSchemaResponse(BaseModel):
    """Response from getting base schema."""
    tables: List[AirtableTable]


class AirtableRecord(BaseModel):
    """Represents an Airtable record."""
    id: str
    fields: Dict[str, Any]
    created_time: Optional[str] = Field(alias="createdTime", default=None)


class ListRecordsResponse(BaseModel):
    """Response from listing records."""
    records: List[AirtableRecord]
    offset: Optional[str] = None


class CreateRecordsRequest(BaseModel):
    """Request for creating records."""
    records: List[Dict[str, Dict[str, Any]]]
    typecast: Optional[bool] = False


class CreateRecordsResponse(BaseModel):
    """Response from creating records."""
    records: List[AirtableRecord]


class UpdateRecordsRequest(BaseModel):
    """Request for updating records."""
    records: List[Dict[str, Any]]
    typecast: Optional[bool] = False


class UpdateRecordsResponse(BaseModel):
    """Response from updating records."""
    records: List[AirtableRecord]


class DeleteRecordsResponse(BaseModel):
    """Response from deleting records."""
    records: List[Dict[str, Any]]


class ListRecordsOptions(BaseModel):
    """Options for listing records."""
    max_records: Optional[int] = Field(alias="maxRecords", default=None)
    filter_by_formula: Optional[str] = Field(alias="filterByFormula", default=None)
    view: Optional[str] = None
    sort: Optional[List[Dict[str, str]]] = None
    fields: Optional[List[str]] = None
    cell_format: Optional[str] = Field(alias="cellFormat", default=None)
    time_zone: Optional[str] = Field(alias="timeZone", default=None)
    user_locale: Optional[str] = Field(alias="userLocale", default=None)