# Airtable API Client Specification

## Overview

This document specifies all the methods that the Python Airtable API Client (`AirtableAPI`) must implement to achieve complete parity with the existing TypeScript `airtable-mcp-server`. This serves as both a specification and implementation tracking document.

## Implementation Status Legend

### Python Implementation Status
- ✅ **Implemented** - Method is fully implemented and tested in Python
- 🚧 **In Progress** - Method is being implemented in Python
- ❌ **Not Started** - Method needs to be implemented in Python
- 📋 **Planned** - Method is planned for future implementation in Python

### TypeScript Reference Status
- ✅ **Reference Available** - Method exists in TypeScript airtable-mcp-server
- ❌ **No Reference** - Method does not exist in TypeScript version

## Base Operations

### 1. List Bases
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `list_bases()`
**Description**: List all Airtable bases accessible to the authenticated user
**TypeScript Reference**: `listBases()` in `airtableService.ts:64-66`

```python
async def list_bases() -> Dict[str, Any]:
    """List all accessible Airtable bases

    Returns:
        Dict containing bases array with id, name, and permissionLevel for each base

    Example Response:
        {
            "bases": [
                {
                    "id": "appABC123",
                    "name": "My Base",
                    "permissionLevel": "create"
                }
            ]
        }
    """
```

**Endpoint**: `GET /v0/meta/bases`
**Authentication**: Bearer token required
**Rate Limits**: Standard Airtable limits apply

---

### 2. Get Base Schema
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `get_base_schema(base_id: str)`
**Description**: Get schema information for a specific base including tables, fields, and views
**TypeScript Reference**: `getBaseSchema(baseId)` in `airtableService.ts:68-70`

```python
async def get_base_schema(base_id: str) -> Dict[str, Any]:
    """Get schema information for a specific base

    Args:
        base_id: The Airtable base ID (e.g., "appABC123")

    Returns:
        Dict containing tables array with full schema information

    Example Response:
        {
            "tables": [
                {
                    "id": "tblXYZ789",
                    "name": "Table 1",
                    "description": "My table",
                    "primaryFieldId": "fldPQR456",
                    "fields": [...],
                    "views": [...]
                }
            ]
        }
    """
```

**Endpoint**: `GET /v0/meta/bases/{base_id}/tables`
**Authentication**: Bearer token required
**Rate Limits**: Standard Airtable limits apply

---

## Record Operations

### 3. List Records
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `list_records(base_id, table_id, ...options)`
**Description**: List records from a table with filtering, sorting, and pagination
**TypeScript Reference**: `listRecords(baseId, tableId, options)` in `airtableService.ts:72-107`

```python
async def list_records(
    base_id: str,
    table_id: str,
    view: Optional[str] = None,
    fields: Optional[List[str]] = None,
    max_records: Optional[int] = None,
    page_size: Optional[int] = None,
    sort: Optional[List[Dict[str, str]]] = None,
    filter_by_formula: Optional[str] = None
) -> Dict[str, Any]:
    """List records from a table

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        view: Specific view to retrieve records from
        fields: List of field names to retrieve
        max_records: Maximum number of records to return
        page_size: Number of records per page (for pagination)
        sort: List of sort specifications [{"field": "Name", "direction": "asc"}]
        filter_by_formula: Airtable formula to filter records

    Returns:
        Dict containing records array and optional offset for pagination
    """
```

**Endpoint**: `GET /v0/{base_id}/{table_id}`
**Features** (TypeScript Implementation):
- ✅ View filtering
- ✅ Field selection
- ✅ Record limits
- ✅ Pagination with offset
- ✅ Sorting (multiple fields)
- ✅ Formula-based filtering
- ✅ Automatic pagination handling

**Python Implementation**: ❌ All features need to be implemented

---

### 4. Get Record
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `get_record(base_id, table_id, record_id)`
**Description**: Get a specific record by ID
**TypeScript Reference**: `getRecord(baseId, tableId, recordId)` in `airtableService.ts:109-114`

```python
async def get_record(base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
    """Get a specific record

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        record_id: The specific record ID

    Returns:
        Dict containing record data with id and fields
    """
```

**Endpoint**: `GET /v0/{base_id}/{table_id}/{record_id}`

---

### 5. Create Records
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `create_records(base_id, table_id, records, typecast)`
**Description**: Create one or more records in a table
**TypeScript Reference**: `createRecord(baseId, tableId, fields)` in `airtableService.ts:116-125` (single record)

```python
async def create_records(
    base_id: str,
    table_id: str,
    records: List[Dict[str, Any]],
    typecast: bool = False
) -> Dict[str, Any]:
    """Create one or more records

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        records: List of record data to create (max 10 per request)
        typecast: Whether to automatically convert field types

    Returns:
        Dict containing created records array
    """
```

**Endpoint**: `POST /v0/{base_id}/{table_id}`
**Features** (TypeScript Implementation):
- ✅ Batch creation (up to 10 records)
- ✅ Typecast support
- ✅ Field validation

**Python Implementation**: ❌ All features need to be implemented

---

### 6. Update Records
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `update_records(base_id, table_id, records, typecast)`
**Description**: Update one or more records in a table
**TypeScript Reference**: `updateRecords(baseId, tableId, records)` in `airtableService.ts:127-141`

```python
async def update_records(
    base_id: str,
    table_id: str,
    records: List[Dict[str, Any]],
    typecast: bool = False
) -> Dict[str, Any]:
    """Update one or more records

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        records: List of record updates (must include id and fields)
        typecast: Whether to automatically convert field types

    Returns:
        Dict containing updated records array
    """
```

**Endpoint**: `PATCH /v0/{base_id}/{table_id}`
**Features** (TypeScript Implementation):
- ✅ Batch updates (up to 10 records)
- ✅ Partial field updates
- ✅ Typecast support

**Python Implementation**: ❌ All features need to be implemented

---

### 7. Delete Records
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `delete_records(base_id, table_id, record_ids)`
**Description**: Delete one or more records from a table
**TypeScript Reference**: `deleteRecords(baseId, tableId, recordIds)` in `airtableService.ts:143-153`

```python
async def delete_records(
    base_id: str,
    table_id: str,
    record_ids: List[str]
) -> Dict[str, Any]:
    """Delete one or more records

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        record_ids: List of record IDs to delete (max 10 per request)

    Returns:
        Dict containing deleted records with id and deleted status
    """
```

**Endpoint**: `DELETE /v0/{base_id}/{table_id}?records[]={id1}&records[]={id2}`
**Features** (TypeScript Implementation):
- ✅ Batch deletion (up to 10 records)
- ✅ Proper URL encoding

**Python Implementation**: ❌ All features need to be implemented

---

### 8. Search Records
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `search_records(base_id, table_id, search_term, ...options)`
**Description**: Search for records containing specific text in text-based fields
**TypeScript Reference**: `searchRecords(baseId, tableId, searchTerm, fieldIds?, maxRecords?, view?)` in `airtableService.ts:250-272`

```python
async def search_records(
    base_id: str,
    table_id: str,
    search_term: str,
    field_ids: Optional[List[str]] = None,
    max_records: Optional[int] = None,
    view: Optional[str] = None
) -> Dict[str, Any]:
    """Search for records containing specific text in specified fields

    Args:
        base_id: The Airtable base ID
        table_id: The table ID or name
        search_term: Text to search for in records
        field_ids: Specific field IDs to search in (optional)
        max_records: Maximum number of records to return
        view: Specific view to search within

    Returns:
        Dict containing matching records
    """
```

**Features** (TypeScript Implementation):
- ✅ Text field validation (only searches text-based fields)
- ✅ Field type checking (singleLineText, multilineText, richText, email, url, phoneNumber)
- ✅ Formula injection prevention (proper escaping)
- ✅ Dynamic field discovery if field_ids not provided
- ✅ View-based searching
- ✅ Record limiting

**Python Implementation**: ❌ All features need to be implemented

**Implementation Notes**:
- Uses `OR(FIND("term", {field1}), FIND("term", {field2}), ...)` formula
- Validates fields are searchable before building formula
- Escapes quotes and backslashes in search terms

---

## Table Operations

### 9. Create Table
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `create_table(base_id, name, fields, description)`
**Description**: Create a new table in a base
**TypeScript Reference**: `createTable(baseId, name, fields, description?)` in `airtableService.ts:155-164`

```python
async def create_table(
    base_id: str,
    name: str,
    fields: List[Dict[str, Any]],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new table in a base

    Args:
        base_id: The Airtable base ID
        name: Name for the new table (must be unique in base)
        fields: List of field definitions (at least one required)
        description: Optional description for the table

    Returns:
        Dict containing the created table information
    """
```

**Endpoint**: `POST /v0/meta/bases/{base_id}/tables`
**Features** (TypeScript Implementation):
- ✅ Field definition validation
- ✅ Primary field requirements
- ✅ Description support

**Python Implementation**: ❌ All features need to be implemented

**Field Requirements**:
- At least one field must be specified
- Primary (first) field must be: singleLineText, multilineText, date, phoneNumber, email, url, number, currency, percent, duration, formula, autonumber, or barcode

---

### 10. Update Table
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `update_table(base_id, table_id, name, description)`
**Description**: Update a table's name or description
**TypeScript Reference**: `updateTable(baseId, tableId, updates)` in `airtableService.ts:166-179`

```python
async def update_table(
    base_id: str,
    table_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update a table's name or description

    Args:
        base_id: The Airtable base ID
        table_id: The table ID to update
        name: New name for the table (optional)
        description: New description for the table (optional)

    Returns:
        Dict containing the updated table information
    """
```

**Endpoint**: `PATCH /v0/meta/bases/{base_id}/tables/{table_id}`
**Features** (TypeScript Implementation):
- ✅ Partial updates (name only, description only, or both)
- ✅ Validation for required parameters

**Python Implementation**: ❌ All features need to be implemented

---

## Field Operations

### 11. Create Field
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `create_field(base_id, table_id, field)`
**Description**: Create a new field in a table
**TypeScript Reference**: `createField(baseId, tableId, field)` in `airtableService.ts:181-190`

```python
async def create_field(
    base_id: str,
    table_id: str,
    field: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new field in a table

    Args:
        base_id: The Airtable base ID
        table_id: The table ID to add the field to
        field: Field definition (type, name, options, etc.)

    Returns:
        Dict containing the created field information
    """
```

**Endpoint**: `POST /v0/meta/bases/{base_id}/tables/{table_id}/fields`
**Features** (TypeScript Implementation):
- ✅ All Airtable field types support
- ✅ Field options validation
- ✅ Type-specific configuration

**Python Implementation**: ❌ All features need to be implemented

**Supported Field Types**:
- ✅ singleLineText, multilineText, richText
- ✅ email, url, phoneNumber
- ✅ number, currency, percent, duration
- ✅ checkbox, rating, singleSelect, multipleSelects
- ✅ date, dateTime, autoNumber, barcode
- ✅ multipleAttachments, multipleRecordLinks
- ✅ lookup, rollup, count, formula
- ✅ createdTime, createdBy, lastModifiedTime, lastModifiedBy
- ✅ button, aiText, externalSyncSource
- ✅ singleCollaborator, multipleCollaborators

---

### 12. Update Field
**Python Status**: ❌ Not Started
**TypeScript Status**: ✅ Reference Available
**Method**: `update_field(base_id, table_id, field_id, name, description)`
**Description**: Update a field's name or description
**TypeScript Reference**: `updateField(baseId, tableId, fieldId, updates)` in `airtableService.ts:192-206`

```python
async def update_field(
    base_id: str,
    table_id: str,
    field_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update a field's name or description

    Args:
        base_id: The Airtable base ID
        table_id: The table ID containing the field
        field_id: The field ID to update
        name: New name for the field (optional)
        description: New description for the field (optional)

    Returns:
        Dict containing the updated field information
    """
```

**Endpoint**: `PATCH /v0/meta/bases/{base_id}/tables/{table_id}/fields/{field_id}`
**Features** (TypeScript Implementation):
- ✅ Partial updates (name only, description only, or both)
- ✅ Field validation

**Python Implementation**: ❌ All features need to be implemented

---

## Error Handling

### Standard Error Responses
All methods implement consistent error handling:

```python
class AirtableError(Exception):
    """Custom exception for Airtable-related errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
```

**Common Error Scenarios** (TypeScript Implementation):
- ✅ 401 Unauthorized (invalid token)
- ✅ 403 Forbidden (insufficient permissions)
- ✅ 404 Not Found (base/table/record not found)
- ✅ 422 Unprocessable Entity (validation errors)
- ✅ 429 Too Many Requests (rate limiting)
- ✅ 500+ Server errors

**Python Implementation**: ❌ Error handling needs to be implemented

---

## Authentication

### OAuth 2.0 Support
All API client methods work with OAuth 2.0 access tokens:

```python
class AirtableAPI:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
```

**Features** (TypeScript Implementation):
- ✅ Bearer token authentication
- ✅ Automatic token inclusion in headers
- ✅ Token refresh handling (via TokenManager)
- ✅ Multi-user support

**Python Implementation**: ❌ OAuth authentication needs to be implemented

---

## Rate Limiting

### Implementation (TypeScript)
- ✅ Respects Airtable's rate limits (5 requests per second per base)
- ✅ Implements exponential backoff for retries
- ✅ Provides clear error messages for rate limit violations

### Python Implementation
- ❌ Rate limiting needs to be implemented
- ❌ Retry logic needs to be implemented

---

## Testing Coverage

### Unit Tests (TypeScript)
- ✅ All methods have individual unit tests
- ✅ Mock API responses for consistent testing
- ✅ Error condition testing
- ✅ Parameter validation testing

### Integration Tests (TypeScript)
- ✅ Real API integration tests (with test tokens)
- ✅ End-to-end workflow testing
- ✅ Authentication flow testing

### Python Testing
- ❌ Unit tests need to be written
- ❌ Integration tests need to be developed
- ❌ OAuth flow testing needs implementation

---

## Compliance with TypeScript Implementation

### Method Mapping
| TypeScript Method | Python Method | TypeScript Status | Python Status |
|------------------|---------------|-------------------|---------------|
| `listBases()` | `list_bases()` | ✅ Implemented | ❌ Not Started |
| `getBaseSchema(baseId)` | `get_base_schema(base_id)` | ✅ Implemented | ❌ Not Started |
| `listRecords(baseId, tableId, options)` | `list_records(base_id, table_id, ...)` | ✅ Implemented | ❌ Not Started |
| `getRecord(baseId, tableId, recordId)` | `get_record(base_id, table_id, record_id)` | ✅ Implemented | ❌ Not Started |
| `createRecord(baseId, tableId, fields)` | `create_records(base_id, table_id, [fields])` | ✅ Implemented | ❌ Not Started |
| `updateRecords(baseId, tableId, records)` | `update_records(base_id, table_id, records)` | ✅ Implemented | ❌ Not Started |
| `deleteRecords(baseId, tableId, recordIds)` | `delete_records(base_id, table_id, record_ids)` | ✅ Implemented | ❌ Not Started |
| `searchRecords(baseId, tableId, searchTerm, ...)` | `search_records(base_id, table_id, search_term, ...)` | ✅ Implemented | ❌ Not Started |
| `createTable(baseId, name, fields, description?)` | `create_table(base_id, name, fields, description)` | ✅ Implemented | ❌ Not Started |
| `updateTable(baseId, tableId, updates)` | `update_table(base_id, table_id, name, description)` | ✅ Implemented | ❌ Not Started |
| `createField(baseId, tableId, field)` | `create_field(base_id, table_id, field)` | ✅ Implemented | ❌ Not Started |
| `updateField(baseId, tableId, fieldId, updates)` | `update_field(base_id, table_id, field_id, name, description)` | ✅ Implemented | ❌ Not Started |

### Feature Parity Status

#### TypeScript Implementation (Complete)
- ✅ **100% API Coverage**: All 12 methods implemented
- ✅ **Parameter Compatibility**: Comprehensive parameter support
- ✅ **Response Format**: Proper response structures
- ✅ **Error Handling**: Complete error handling patterns
- ✅ **Validation Logic**: Full validation rules (especially for search)

#### Python Implementation (Pending)
- ❌ **0% API Coverage**: No methods implemented yet
- ❌ **Parameter Compatibility**: Parameters need to be implemented
- ❌ **Response Format**: Response formatting needs implementation
- ❌ **Error Handling**: Error handling needs to be built
- ❌ **Validation Logic**: Validation rules need to be ported

---

## Future Enhancements

### Planned Features
- 📋 **Webhook Support**: Listen for base changes
- 📋 **Batch Operations**: Higher-level batch operations
- 📋 **Schema Validation**: Pydantic models for all responses
- 📋 **Caching Layer**: Optional response caching
- 📋 **Retry Logic**: Built-in retry with exponential backoff

### Performance Optimizations
- 📋 **Connection Pooling**: Reuse HTTP connections
- 📋 **Async Improvements**: Further async optimizations
- 📋 **Compression**: Request/response compression support

---

## Version Compatibility

- **Python Version**: 3.11+
- **FastMCP Version**: 2.10.0+
- **Airtable API Version**: v0
- **OAuth Standard**: RFC 6749 (OAuth 2.0)

---

## Documentation Links

- [Airtable API Reference](https://airtable.com/developers/web/api/introduction)
- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Main Implementation Guide](./airtable-mcp-oauth-implementation-guide.md)
