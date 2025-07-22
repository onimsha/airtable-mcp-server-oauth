# Airtable OAuth MCP Server

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A production-ready **Model Context Protocol (MCP) server** for Airtable with secure OAuth 2.0 authentication. This server enables AI assistants and applications to interact with Airtable bases through a standardized MCP interface, providing complete API coverage for all Airtable operations.

## 🚀 Features

### Core Functionality
- **🔐 OAuth 2.0 Authentication** - Secure token-based authentication with Airtable
- **📊 Complete Airtable API Coverage** - 10 comprehensive MCP tools covering all operations
- **⚡ FastMCP Framework** - Built on the high-performance FastMCP framework
- **☁️ Cloud-Ready** - Production-ready deployment support
- **🔄 Dual Transport** - Support for both STDIO and HTTP transport protocols

### Security & Reliability
- **🔑 Environment-based Configuration** - Secure credential management
- **✅ Type Safety** - Full type hints and validation with Pydantic
- **🧪 Comprehensive Testing** - Unit tests with pytest and coverage reporting
- **📝 Code Quality** - Linting with Ruff and type checking with MyPy

### Developer Experience
- **📚 Rich Documentation** - Comprehensive setup and usage guides
- **🔧 Easy Setup** - Simple installation with uv package manager
- **🎯 Typed Parameters** - Clear, typed tool parameters for better IDE support
- **🔍 Flexible Querying** - Advanced filtering, sorting, and search capabilities

## 📋 Prerequisites

- **Python 3.11+** - Latest Python version for optimal performance
- **uv** - Fast Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Airtable Developer Account** - To create OAuth applications ([sign up](https://airtable.com/developers))

## 🚀 Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/onimsha/airtable-mcp-server-oauth.git
cd airtable-mcp-server-oauth
uv sync
```

### 2. Airtable OAuth Setup

1. **Create an Airtable OAuth Application:**
   - Visit [Airtable Developer Hub](https://airtable.com/developers/web/api/oauth-reference)
   - Create a new OAuth integration
   - Note your `Client ID` and `Client Secret`
   - Set redirect URI to `http://localhost:8000/oauth/callback`

### 3. Environment Configuration

Copy the environment template and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Airtable OAuth Configuration
AIRTABLE_CLIENT_ID="your_airtable_client_id_here"
AIRTABLE_CLIENT_SECRET="your_airtable_client_secret_here"
AIRTABLE_REDIRECT_URI="http://localhost:8000/oauth/callback"

# Server Configuration
HOST="0.0.0.0"
PORT=8000
LOG_LEVEL="INFO"
```

### 4. Testing with MCP Inspector

Use the official MCP Inspector to test and interact with your server:

1. **Start the server:**
   ```bash
   uv run python -m airtable_mcp http
   ```

2. **Open MCP Inspector:**
   Visit [https://modelcontextprotocol.io/docs/tools/inspector](https://modelcontextprotocol.io/docs/tools/inspector)

3. **Connect to your server:**
   - Select "HTTP Streaming" transport
   - Enter the URL: `http://localhost:8000/mcp`
   - Click "Connect"

4. **Authenticate with Airtable:**
   - The server will guide you through OAuth authentication
   - Use the inspector to test available MCP tools

### 5. Run the Server

**STDIO Transport (default):**
```bash
uv run python -m airtable_mcp
# or
uv run airtable-oauth-mcp
```

**HTTP Transport:**
```bash
uv run python -m airtable_mcp http
# or with custom host/port
uv run python -m airtable_mcp http localhost 8001
```

**Additional Options:**
```bash
# Set log level
uv run python -m airtable_mcp --log-level DEBUG

# Show help
uv run python -m airtable_mcp --help

# Show version
uv run python -m airtable_mcp --version
```

The HTTP server will be available at `http://localhost:8000/` (or custom host:port) with OAuth endpoints for web integration.

## MCP Tools Available

The server provides 10 MCP tools for Airtable operations:

**Base Operations:**
- `list_bases()` - List all accessible bases
- `list_tables(base_id, detail_level?)` - List tables in a base
- `describe_table(base_id, table_id)` - Get detailed table schema

**Record Operations:**
- `list_records(base_id, table_id, view?, filter_by_formula?, sort?, fields?)` - List records with filtering
- `get_record(base_id, table_id, record_id)` - Get a specific record
- `create_record(base_id, table_id, fields, typecast?)` - Create a single record
- `create_records(base_id, table_id, records, typecast?)` - Create multiple records
- `update_records(base_id, table_id, records, typecast?)` - Update multiple records
- `delete_records(base_id, table_id, record_ids)` - Delete multiple records
- `search_records(base_id, table_id, filter_by_formula, view?, fields?)` - Search records with formulas

All tools now use **typed parameters** instead of generic `args`, making them more transparent to MCP clients.

**Parameter Flexibility:**
- `fields` parameter accepts either a single field name (string) or array of field names
- `sort` parameter expects array of objects: `[{"field": "Name", "direction": "asc"}]`

## 💡 Usage Examples

### Basic Record Operations

```python
# List all records in a table
records = await client.call_tool("list_records", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY"
})

# Create a new record
new_record = await client.call_tool("create_record", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY",
    "fields": {
        "Name": "John Doe",
        "Email": "john@example.com",
        "Status": "Active"
    }
})

# Search records with filtering
filtered_records = await client.call_tool("search_records", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY",
    "filter_by_formula": "AND({Status} = 'Active', {Email} != '')",
    "fields": ["Name", "Email", "Status"]
})
```

### Advanced Querying

```python
# List records with sorting and filtering
records = await client.call_tool("list_records", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY",
    "view": "Grid view",
    "filter_by_formula": "{Priority} = 'High'",
    "sort": [
        {"field": "Created", "direction": "desc"},
        {"field": "Name", "direction": "asc"}
    ],
    "fields": ["Name", "Priority", "Created", "Status"]
})

# Batch operations
batch_create = await client.call_tool("create_records", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY",
    "records": [
        {"fields": {"Name": "Record 1", "Value": 100}},
        {"fields": {"Name": "Record 2", "Value": 200}},
        {"fields": {"Name": "Record 3", "Value": 300}}
    ],
    "typecast": True
})
```

### Schema Discovery

```python
# List all bases you have access to
bases = await client.call_tool("list_bases")

# Get detailed information about a specific table
table_info = await client.call_tool("describe_table", {
    "base_id": "appXXXXXXXXXXXXXX",
    "table_id": "tblYYYYYYYYYYYYYY"
})

# List all tables in a base
tables = await client.call_tool("list_tables", {
    "base_id": "appXXXXXXXXXXXXXX",
    "detail_level": "full"
})
```

## 🛠️ Development

### Getting Started

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/your-username/airtable-mcp-server-oauth.git
   cd airtable-mcp-server-oauth
   ```

2. **Setup Development Environment:**
   ```bash
   uv sync --all-extras
   ```

3. **Run Tests:**
   ```bash
   uv run pytest
   uv run pytest --cov=src/airtable_mcp --cov-report=html
   ```

### Code Quality

**Type Checking:**
```bash
uv run mypy src/
```

**Linting:**
```bash
uv run ruff check src/
uv run ruff format src/
```

**Pre-commit Hooks:**
```bash
pip install pre-commit
pre-commit install
```

### Testing

The project includes comprehensive test coverage:

- **Unit Tests:** Test individual components and functions
- **Integration Tests:** Test OAuth flow and Airtable API interactions
- **Coverage Reports:** Ensure >90% code coverage

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/airtable_mcp

# Run specific test files
uv run pytest tests/test_oauth.py
uv run pytest tests/test_tools.py
```

### Project Structure

```
src/airtable_mcp/
├── __init__.py          # Package initialization
├── main.py              # Entry point and CLI
├── server.py            # MCP server implementation
├── oauth/               # OAuth authentication
│   ├── __init__.py
│   ├── client.py        # OAuth client implementation
│   └── storage.py       # Token storage
├── tools/               # MCP tools implementation
│   ├── __init__.py
│   ├── base_ops.py      # Base operations
│   └── record_ops.py    # Record operations
└── utils/               # Utility functions
    ├── __init__.py
    ├── config.py        # Configuration management
    └── logging.py       # Logging setup
```

## ⚙️ Configuration

All configuration is handled through environment variables (loaded from `.env`):

### Required Variables
- `AIRTABLE_CLIENT_ID` - OAuth client ID from Airtable
- `AIRTABLE_CLIENT_SECRET` - OAuth client secret
- `AIRTABLE_REDIRECT_URI` - OAuth callback URL

### Optional Variables
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `MCP_SERVER_NAME` - Server name (optional)
- `MCP_SERVER_VERSION` - Server version (optional)

## 🤝 Contributing

We welcome contributions! Please see our contribution guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Ensure code quality** with our linting and formatting tools
4. **Update documentation** for any API changes
5. **Submit a pull request** with a clear description

### Contribution Areas
- 🐛 **Bug fixes** - Help us squash bugs
- ✨ **New features** - Add new Airtable API endpoints
- 📚 **Documentation** - Improve setup guides and examples
- 🧪 **Testing** - Increase test coverage
- 🚀 **Performance** - Optimize API calls and caching

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[FastMCP](https://github.com/jlowin/fastmcp)** - Excellent MCP framework
- **[Airtable](https://airtable.com/)** - Powerful database platform
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Standard for AI tool integration

## 📚 Documentation

### Additional Resources
- [OAuth2 flow documentation](docs/airtable-oauth2-flow-documentation.md)
- [Dynamic client registration](docs/dynamic-client-registration.md)
- [Airtable API Reference](https://airtable.com/developers/web/api/introduction)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/onimsha/airtable-mcp-server-oauth/issues)
- **Discussions:** [GitHub Discussions](https://github.com/onimsha/airtable-mcp-server-oauth/discussions)
- **Documentation:** [Project Wiki](https://github.com/onimsha/airtable-mcp-server-oauth/wiki)
