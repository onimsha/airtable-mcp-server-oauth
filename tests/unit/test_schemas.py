"""Unit tests for MCP schemas."""

import pytest
from pydantic import ValidationError

from airtable_mcp.mcp.schemas import (
    BaseArgs,
    CreateFieldArgs,
    CreateRecordArgs,
    CreateRecordsArgs,
    CreateTableArgs,
    DeleteRecordsArgs,
    DescribeTableArgs,
    GetRecordArgs,
    ListRecordsArgs,
    ListTablesArgs,
    SearchRecordsArgs,
    UpdateFieldArgs,
    UpdateRecordsArgs,
    UpdateTableArgs,
)


class TestBaseArgs:
    """Test cases for BaseArgs."""

    def test_base_args_creation(self):
        """Test BaseArgs can be created."""
        args = BaseArgs()
        assert isinstance(args, BaseArgs)

    def test_base_args_dict(self):
        """Test BaseArgs dict conversion."""
        args = BaseArgs()
        assert args.model_dump() == {}


class TestListTablesArgs:
    """Test cases for ListTablesArgs."""

    def test_list_tables_args_required(self):
        """Test ListTablesArgs with required fields."""
        args = ListTablesArgs(base_id="app123")
        assert args.base_id == "app123"
        assert args.detail_level == "tableIdentifiersOnly"

    def test_list_tables_args_with_detail_level(self):
        """Test ListTablesArgs with custom detail level."""
        args = ListTablesArgs(base_id="app123", detail_level="withFieldInfo")
        assert args.base_id == "app123"
        assert args.detail_level == "withFieldInfo"

    def test_list_tables_args_invalid_detail_level(self):
        """Test ListTablesArgs with invalid detail level."""
        with pytest.raises(ValidationError):
            ListTablesArgs(base_id="app123", detail_level="invalid")

    def test_list_tables_args_missing_base_id(self):
        """Test ListTablesArgs missing required base_id."""
        with pytest.raises(ValidationError):
            ListTablesArgs()


class TestDescribeTableArgs:
    """Test cases for DescribeTableArgs."""

    def test_describe_table_args_valid(self):
        """Test DescribeTableArgs with valid data."""
        args = DescribeTableArgs(base_id="app123", table_id="tbl456")
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"

    def test_describe_table_args_missing_fields(self):
        """Test DescribeTableArgs with missing required fields."""
        with pytest.raises(ValidationError):
            DescribeTableArgs(base_id="app123")

        with pytest.raises(ValidationError):
            DescribeTableArgs(table_id="tbl456")


class TestListRecordsArgs:
    """Test cases for ListRecordsArgs."""

    def test_list_records_args_minimal(self):
        """Test ListRecordsArgs with minimal required fields."""
        args = ListRecordsArgs(base_id="app123", table_id="tbl456")
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.view is None
        assert args.max_records is None
        assert args.filter_by_formula is None
        assert args.sort is None
        assert args.fields is None

    def test_list_records_args_complete(self):
        """Test ListRecordsArgs with all fields."""
        args = ListRecordsArgs(
            base_id="app123",
            table_id="tbl456",
            view="Grid view",
            max_records=100,
            filter_by_formula="{Status} = 'Active'",
            sort=[{"field": "Name", "direction": "asc"}],
            fields=["Name", "Status"],
        )
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.view == "Grid view"
        assert args.max_records == 100
        assert args.filter_by_formula == "{Status} = 'Active'"
        assert args.sort == [{"field": "Name", "direction": "asc"}]
        assert args.fields == ["Name", "Status"]

    def test_list_records_args_validation(self):
        """Test ListRecordsArgs validation."""
        # Invalid max_records type
        with pytest.raises(ValidationError):
            ListRecordsArgs(base_id="app123", table_id="tbl456", max_records="invalid")

        # Invalid fields type
        with pytest.raises(ValidationError):
            ListRecordsArgs(base_id="app123", table_id="tbl456", fields="invalid")


class TestGetRecordArgs:
    """Test cases for GetRecordArgs."""

    def test_get_record_args_valid(self):
        """Test GetRecordArgs with valid data."""
        args = GetRecordArgs(base_id="app123", table_id="tbl456", record_id="rec789")
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.record_id == "rec789"

    def test_get_record_args_missing_fields(self):
        """Test GetRecordArgs with missing required fields."""
        with pytest.raises(ValidationError):
            GetRecordArgs(base_id="app123", table_id="tbl456")


class TestCreateRecordArgs:
    """Test cases for CreateRecordArgs."""

    def test_create_record_args_minimal(self):
        """Test CreateRecordArgs with minimal fields."""
        args = CreateRecordArgs(
            base_id="app123", table_id="tbl456", fields={"Name": "Test Record"}
        )
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.fields == {"Name": "Test Record"}
        assert args.typecast is False

    def test_create_record_args_with_typecast(self):
        """Test CreateRecordArgs with typecast enabled."""
        args = CreateRecordArgs(
            base_id="app123",
            table_id="tbl456",
            fields={"Name": "Test Record"},
            typecast=True,
        )
        assert args.typecast is True

    def test_create_record_args_complex_fields(self):
        """Test CreateRecordArgs with complex field data."""
        complex_fields = {
            "Name": "Test Record",
            "Number": 42,
            "Date": "2025-01-01",
            "Attachments": [{"url": "https://example.com/file.pdf"}],
            "Multiselect": ["Option1", "Option2"],
        }
        args = CreateRecordArgs(
            base_id="app123", table_id="tbl456", fields=complex_fields
        )
        assert args.fields == complex_fields


class TestCreateRecordsArgs:
    """Test cases for CreateRecordsArgs."""

    def test_create_records_args_minimal(self):
        """Test CreateRecordsArgs with minimal data."""
        records = [{"fields": {"Name": "Record 1"}}, {"fields": {"Name": "Record 2"}}]
        args = CreateRecordsArgs(base_id="app123", table_id="tbl456", records=records)
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.records == records
        assert args.typecast is False

    def test_create_records_args_with_typecast(self):
        """Test CreateRecordsArgs with typecast."""
        records = [{"fields": {"Name": "Record 1"}}]
        args = CreateRecordsArgs(
            base_id="app123", table_id="tbl456", records=records, typecast=True
        )
        assert args.typecast is True

    def test_create_records_args_empty_list(self):
        """Test CreateRecordsArgs with empty records list."""
        args = CreateRecordsArgs(base_id="app123", table_id="tbl456", records=[])
        assert args.records == []


class TestUpdateRecordsArgs:
    """Test cases for UpdateRecordsArgs."""

    def test_update_records_args_valid(self):
        """Test UpdateRecordsArgs with valid data."""
        records = [{"id": "rec123", "fields": {"Name": "Updated Record"}}]
        args = UpdateRecordsArgs(base_id="app123", table_id="tbl456", records=records)
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.records == records
        assert args.typecast is False

    def test_update_records_args_with_typecast(self):
        """Test UpdateRecordsArgs with typecast."""
        records = [{"id": "rec123", "fields": {"Name": "Updated Record"}}]
        args = UpdateRecordsArgs(
            base_id="app123", table_id="tbl456", records=records, typecast=True
        )
        assert args.typecast is True


class TestDeleteRecordsArgs:
    """Test cases for DeleteRecordsArgs."""

    def test_delete_records_args_valid(self):
        """Test DeleteRecordsArgs with valid data."""
        record_ids = ["rec123", "rec456", "rec789"]
        args = DeleteRecordsArgs(
            base_id="app123", table_id="tbl456", record_ids=record_ids
        )
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.record_ids == record_ids

    def test_delete_records_args_single_record(self):
        """Test DeleteRecordsArgs with single record."""
        args = DeleteRecordsArgs(
            base_id="app123", table_id="tbl456", record_ids=["rec123"]
        )
        assert args.record_ids == ["rec123"]

    def test_delete_records_args_empty_list(self):
        """Test DeleteRecordsArgs with empty record list."""
        args = DeleteRecordsArgs(base_id="app123", table_id="tbl456", record_ids=[])
        assert args.record_ids == []


class TestSearchRecordsArgs:
    """Test cases for SearchRecordsArgs."""

    def test_search_records_args_minimal(self):
        """Test SearchRecordsArgs with minimal required fields."""
        args = SearchRecordsArgs(
            base_id="app123", table_id="tbl456", filter_by_formula="{Status} = 'Active'"
        )
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.filter_by_formula == "{Status} = 'Active'"
        assert args.max_records is None
        assert args.view is None
        assert args.fields is None

    def test_search_records_args_complete(self):
        """Test SearchRecordsArgs with all fields."""
        args = SearchRecordsArgs(
            base_id="app123",
            table_id="tbl456",
            filter_by_formula="{Status} = 'Active'",
            max_records=50,
            view="Grid view",
            fields=["Name", "Status"],
        )
        assert args.max_records == 50
        assert args.view == "Grid view"
        assert args.fields == ["Name", "Status"]

    def test_search_records_args_missing_formula(self):
        """Test SearchRecordsArgs missing required filter formula."""
        with pytest.raises(ValidationError):
            SearchRecordsArgs(base_id="app123", table_id="tbl456")


class TestCreateTableArgs:
    """Test cases for CreateTableArgs."""

    def test_create_table_args_minimal(self):
        """Test CreateTableArgs with minimal fields."""
        fields = [{"name": "Primary Field", "type": "singleLineText"}]
        args = CreateTableArgs(base_id="app123", name="New Table", fields=fields)
        assert args.base_id == "app123"
        assert args.name == "New Table"
        assert args.description is None
        assert args.fields == fields

    def test_create_table_args_with_description(self):
        """Test CreateTableArgs with description."""
        fields = [{"name": "Primary Field", "type": "singleLineText"}]
        args = CreateTableArgs(
            base_id="app123",
            name="New Table",
            description="Test table description",
            fields=fields,
        )
        assert args.description == "Test table description"

    def test_create_table_args_complex_fields(self):
        """Test CreateTableArgs with complex field definitions."""
        fields = [
            {"name": "Name", "type": "singleLineText"},
            {"name": "Email", "type": "email"},
            {"name": "Phone", "type": "phoneNumber"},
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {"choices": ["Active", "Inactive"]},
            },
        ]
        args = CreateTableArgs(base_id="app123", name="Contact Table", fields=fields)
        assert len(args.fields) == 4
        assert args.fields[3]["options"]["choices"] == ["Active", "Inactive"]


class TestUpdateTableArgs:
    """Test cases for UpdateTableArgs."""

    def test_update_table_args_minimal(self):
        """Test UpdateTableArgs with minimal fields."""
        args = UpdateTableArgs(base_id="app123", table_id="tbl456")
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.name is None
        assert args.description is None

    def test_update_table_args_with_name(self):
        """Test UpdateTableArgs with new name."""
        args = UpdateTableArgs(
            base_id="app123", table_id="tbl456", name="Updated Table Name"
        )
        assert args.name == "Updated Table Name"

    def test_update_table_args_with_description(self):
        """Test UpdateTableArgs with new description."""
        args = UpdateTableArgs(
            base_id="app123", table_id="tbl456", description="Updated description"
        )
        assert args.description == "Updated description"

    def test_update_table_args_complete(self):
        """Test UpdateTableArgs with all fields."""
        args = UpdateTableArgs(
            base_id="app123",
            table_id="tbl456",
            name="New Name",
            description="New Description",
        )
        assert args.name == "New Name"
        assert args.description == "New Description"


class TestCreateFieldArgs:
    """Test cases for CreateFieldArgs."""

    def test_create_field_args_minimal(self):
        """Test CreateFieldArgs with minimal fields."""
        args = CreateFieldArgs(
            base_id="app123", table_id="tbl456", name="New Field", type="singleLineText"
        )
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.name == "New Field"
        assert args.type == "singleLineText"
        assert args.description is None
        assert args.options is None

    def test_create_field_args_with_description(self):
        """Test CreateFieldArgs with description."""
        args = CreateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            name="New Field",
            type="singleLineText",
            description="Field description",
        )
        assert args.description == "Field description"

    def test_create_field_args_with_options(self):
        """Test CreateFieldArgs with field options."""
        options = {"choices": ["Option 1", "Option 2", "Option 3"]}
        args = CreateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            name="Status Field",
            type="singleSelect",
            options=options,
        )
        assert args.options == options

    def test_create_field_args_complete(self):
        """Test CreateFieldArgs with all fields."""
        options = {"precision": 2}
        args = CreateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            name="Price",
            type="currency",
            description="Product price field",
            options=options,
        )
        assert args.name == "Price"
        assert args.type == "currency"
        assert args.description == "Product price field"
        assert args.options == options


class TestUpdateFieldArgs:
    """Test cases for UpdateFieldArgs."""

    def test_update_field_args_minimal(self):
        """Test UpdateFieldArgs with minimal fields."""
        args = UpdateFieldArgs(base_id="app123", table_id="tbl456", field_id="fld789")
        assert args.base_id == "app123"
        assert args.table_id == "tbl456"
        assert args.field_id == "fld789"
        assert args.name is None
        assert args.description is None

    def test_update_field_args_with_name(self):
        """Test UpdateFieldArgs with new name."""
        args = UpdateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            field_id="fld789",
            name="Updated Field Name",
        )
        assert args.name == "Updated Field Name"

    def test_update_field_args_with_description(self):
        """Test UpdateFieldArgs with new description."""
        args = UpdateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            field_id="fld789",
            description="Updated field description",
        )
        assert args.description == "Updated field description"

    def test_update_field_args_complete(self):
        """Test UpdateFieldArgs with all fields."""
        args = UpdateFieldArgs(
            base_id="app123",
            table_id="tbl456",
            field_id="fld789",
            name="New Field Name",
            description="New field description",
        )
        assert args.name == "New Field Name"
        assert args.description == "New field description"


class TestSchemaIntegration:
    """Integration tests for schema validation."""

    def test_all_schemas_inherit_from_base_model(self):
        """Test that all schema classes inherit from BaseModel."""
        from pydantic import BaseModel

        schema_classes = [
            BaseArgs,
            ListTablesArgs,
            DescribeTableArgs,
            ListRecordsArgs,
            GetRecordArgs,
            CreateRecordArgs,
            CreateRecordsArgs,
            UpdateRecordsArgs,
            DeleteRecordsArgs,
            SearchRecordsArgs,
            CreateTableArgs,
            UpdateTableArgs,
            CreateFieldArgs,
            UpdateFieldArgs,
        ]

        for schema_class in schema_classes:
            assert issubclass(schema_class, BaseModel)

    def test_schema_serialization(self):
        """Test that schemas can be serialized and deserialized."""
        args = ListRecordsArgs(
            base_id="app123", table_id="tbl456", fields=["Name", "Email"]
        )

        # Serialize to dict
        data = args.model_dump()
        assert isinstance(data, dict)
        assert data["base_id"] == "app123"

        # Deserialize from dict
        restored = ListRecordsArgs.model_validate(data)
        assert restored.base_id == args.base_id
        assert restored.table_id == args.table_id
        assert restored.fields == args.fields

    def test_schema_json_serialization(self):
        """Test JSON serialization of schemas."""
        args = CreateRecordArgs(
            base_id="app123",
            table_id="tbl456",
            fields={"Name": "Test", "Count": 42},
            typecast=True,
        )

        # Serialize to JSON
        json_str = args.model_dump_json()
        assert isinstance(json_str, str)
        assert "app123" in json_str

        # Deserialize from JSON
        restored = CreateRecordArgs.model_validate_json(json_str)
        assert restored.base_id == args.base_id
        assert restored.fields == args.fields
        assert restored.typecast == args.typecast
