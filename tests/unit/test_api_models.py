"""Unit tests for API models."""

from airtable_mcp.api.models import (
    AirtableBase,
    AirtableRecord,
    AirtableTable,
    CreateRecordsRequest,
    ListRecordsOptions,
    UpdateRecordsRequest,
)


class TestAirtableRecord:
    """Test cases for AirtableRecord model."""

    def test_record_creation_valid(self):
        """Test creating a valid record."""
        record = AirtableRecord(
            id="rec123",
            fields={"Name": "Test Record", "Value": 42},
            createdTime="2025-01-01T00:00:00.000Z",
        )

        assert record.id == "rec123"
        assert record.fields["Name"] == "Test Record"
        assert record.fields["Value"] == 42
        assert record.created_time == "2025-01-01T00:00:00.000Z"

    def test_record_creation_minimal(self):
        """Test creating a record with minimal required fields."""
        record = AirtableRecord(id="rec123", fields={"Name": "Test"})

        assert record.id == "rec123"
        assert record.fields == {"Name": "Test"}
        assert record.created_time is None


class TestListRecordsOptions:
    """Test cases for ListRecordsOptions model."""

    def test_list_records_options_empty(self):
        """Test creating empty list records options."""
        options = ListRecordsOptions()

        assert options.view is None
        assert options.fields is None
        assert options.sort is None
        assert options.filter_by_formula is None

    def test_list_records_options_full(self):
        """Test creating full list records options."""
        options = ListRecordsOptions(
            view="Grid view",
            fields=["Name", "Value"],
            sort=[{"field": "Name", "direction": "asc"}],
            filterByFormula="{Status} = 'Active'",
        )

        assert options.view == "Grid view"
        assert options.fields == ["Name", "Value"]
        assert len(options.sort) == 1
        assert options.sort[0]["field"] == "Name"
        assert options.filter_by_formula == "{Status} = 'Active'"


class TestCreateRecordsRequest:
    """Test cases for CreateRecordsRequest model."""

    def test_create_records_request_single(self):
        """Test creating request for single record."""
        request = CreateRecordsRequest(
            records=[{"fields": {"Name": "Test Record"}}], typecast=True
        )

        assert len(request.records) == 1
        assert request.records[0]["fields"]["Name"] == "Test Record"
        assert request.typecast is True

    def test_create_records_request_multiple(self):
        """Test creating request for multiple records."""
        request = CreateRecordsRequest(
            records=[
                {"fields": {"Name": "Record 1"}},
                {"fields": {"Name": "Record 2"}},
                {"fields": {"Name": "Record 3"}},
            ]
        )

        assert len(request.records) == 3
        assert request.typecast is False  # Default value


class TestUpdateRecordsRequest:
    """Test cases for UpdateRecordsRequest model."""

    def test_update_records_request_valid(self):
        """Test creating valid update request."""
        request = UpdateRecordsRequest(
            records=[{"id": "rec123", "fields": {"Name": "Updated Record"}}],
            typecast=True,
        )

        assert len(request.records) == 1
        assert request.records[0]["id"] == "rec123"
        assert request.typecast is True


class TestAirtableBase:
    """Test cases for AirtableBase model."""

    def test_base_creation(self):
        """Test creating base info."""
        base = AirtableBase(id="app123", name="Test Base", permissionLevel="create")

        assert base.id == "app123"
        assert base.name == "Test Base"
        assert base.permission_level == "create"


class TestAirtableTable:
    """Test cases for AirtableTable model."""

    def test_table_creation_minimal(self):
        """Test creating minimal table info."""
        table = AirtableTable(
            id="tbl123", name="Test Table", primaryFieldId="fld123", fields=[]
        )

        assert table.id == "tbl123"
        assert table.name == "Test Table"
        assert table.primary_field_id == "fld123"
        assert table.fields == []
        assert table.views is None

    def test_table_creation_full(self):
        """Test creating full table info."""
        from airtable_mcp.api.models import AirtableField

        field = AirtableField(id="fld123", name="Primary Field", type="singleLineText")

        table = AirtableTable(
            id="tbl123",
            name="Test Table",
            primaryFieldId="fld123",
            fields=[field],
            views=[{"id": "viw123", "name": "Grid view", "type": "grid"}],
        )

        assert table.id == "tbl123"
        assert len(table.fields) == 1
        assert len(table.views) == 1
        assert table.fields[0].name == "Primary Field"
        assert table.views[0]["name"] == "Grid view"
