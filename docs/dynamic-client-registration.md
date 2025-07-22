# OAuth 2.0 Dynamic Client Registration (RFC 7591)

This document describes the implementation of OAuth 2.0 Dynamic Client Registration (RFC 7591) for the Airtable OAuth MCP server.

## Overview

Dynamic Client Registration allows OAuth clients to be registered programmatically with the authorization server, eliminating the need for manual client configuration. This implementation follows RFC 7591 standards and integrates with the existing OAuth 2.0 flow.

## Features

- **Programmatic Client Registration**: Register OAuth clients via API
- **Full CRUD Operations**: Create, read, update, and delete registered clients
- **Metadata Validation**: Comprehensive validation of client metadata according to RFC 7591
- **Access Control**: Optional registration access token for securing client registration
- **Standards Compliance**: Follows RFC 7591 specification
- **Integration**: Seamlessly integrated with existing OAuth 2.0 flow and MCP server

## API Endpoints

### Client Registration

**POST** `/oauth/register`

Register a new OAuth client dynamically.

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <registration_access_token> (optional)
```

**Request Body:**
```json
{
  "client_name": "My MCP Application",
  "redirect_uris": ["http://localhost:3000/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "data.records:read data.records:write",
  "token_endpoint_auth_method": "client_secret_post",
  "contacts": ["admin@example.com"],
  "client_uri": "https://myapp.example.com",
  "logo_uri": "https://myapp.example.com/logo.png",
  "policy_uri": "https://myapp.example.com/policy",
  "tos_uri": "https://myapp.example.com/terms"
}
```

**Response (201 Created):**
```json
{
  "client_id": "airtable_mcp_HyNVkbAPMzniJRdtxNro7A",
  "client_secret": "ZGVmYXVsdCBzZWNyZXQgdmFsdWU",
  "client_id_issued_at": 1642694400,
  "client_secret_expires_at": 0,
  "client_name": "My MCP Application",
  "redirect_uris": ["http://localhost:3000/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "data.records:read data.records:write",
  "token_endpoint_auth_method": "client_secret_post",
  "contacts": ["admin@example.com"],
  "client_uri": "https://myapp.example.com",
  "logo_uri": "https://myapp.example.com/logo.png",
  "policy_uri": "https://myapp.example.com/policy",
  "tos_uri": "https://myapp.example.com/terms"
}
```

### Client Configuration Management

**GET** `/oauth/register/{client_id}`

Retrieve client configuration.

**PUT** `/oauth/register/{client_id}`

Update client configuration.

**DELETE** `/oauth/register/{client_id}`

Delete client registration.

## Configuration

### Environment Variables

```bash
# Optional: Require access token for client registration
export AIRTABLE_REGISTRATION_ACCESS_TOKEN="your-registration-token"

# Standard OAuth configuration
export AIRTABLE_CLIENT_ID="your-airtable-client-id"
export AIRTABLE_CLIENT_SECRET="your-airtable-client-secret"
```

### Server Configuration

```python
from airtable_mcp.mcp.server import AirtableMCPServer

# Enable OAuth endpoints (includes dynamic client registration)
server = AirtableMCPServer(enable_oauth_endpoints=True)
```

## Client Metadata Fields

### Required Fields

None. All fields are optional according to RFC 7591, with sensible defaults provided.

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `client_name` | string | Human-readable client name | - |
| `redirect_uris` | array | List of valid redirect URIs | - |
| `grant_types` | array | OAuth grant types | `["authorization_code"]` |
| `response_types` | array | OAuth response types | `["code"]` |
| `scope` | string | Requested scope | `"data.records:read"` |
| `token_endpoint_auth_method` | string | Client authentication method | `"client_secret_post"` |
| `contacts` | array | Contact email addresses | - |
| `logo_uri` | string | Client logo URL | - |
| `client_uri` | string | Client information URL | - |
| `policy_uri` | string | Privacy policy URL | - |
| `tos_uri` | string | Terms of service URL | - |
| `software_id` | string | Software identifier | - |
| `software_version` | string | Software version | - |

### Supported Values

**Grant Types:**
- `authorization_code`
- `refresh_token`

**Response Types:**
- `code`

**Token Endpoint Auth Methods:**
- `client_secret_basic`
- `client_secret_post`

**Scopes:**
- `data.records:read`
- `data.records:write`
- `data.recordComments:read`
- `data.recordComments:write`
- `schema.bases:read`
- `schema.bases:write`
- `webhook:manage`

## Usage Examples

### Basic Client Registration

```bash
curl -X POST http://localhost:8000/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "My MCP App",
    "redirect_uris": ["http://localhost:3000/callback"]
  }'
```

### With Registration Access Token

```bash
curl -X POST http://localhost:8000/oauth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-registration-token" \
  -d '{
    "client_name": "Secure MCP App",
    "redirect_uris": ["https://myapp.com/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "scope": "data.records:read data.records:write"
  }'
```

### Update Client Configuration

```bash
curl -X PUT http://localhost:8000/oauth/register/client_id_here \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-registration-token" \
  -d '{
    "client_name": "Updated App Name",
    "redirect_uris": ["https://myapp.com/new-callback"]
  }'
```

### Delete Client

```bash
curl -X DELETE http://localhost:8000/oauth/register/client_id_here \
  -H "Authorization: Bearer your-registration-token"
```

## Metadata Discovery

Dynamic client registration information is included in the OAuth authorization server metadata:

```bash
curl http://localhost:8000/.well-known/oauth-authorization-server
```

**Response includes:**
```json
{
  "registration_endpoint": "http://localhost:8000/oauth/register",
  "registration_endpoint_auth_methods_supported": ["bearer"],
  "client_registration_types_supported": ["dynamic"],
  "token_endpoint_auth_methods_supported": [
    "client_secret_basic",
    "client_secret_post"
  ]
}
```

## Security Considerations

### Access Control

- **Registration Access Token**: Use `AIRTABLE_REGISTRATION_ACCESS_TOKEN` to require authentication for client registration
- **CORS Support**: All endpoints include CORS headers for cross-origin requests
- **Input Validation**: Comprehensive validation of all client metadata fields

### Client Credentials

- **Client IDs**: Generated with format `airtable_mcp_{random_string}`
- **Client Secrets**: 32-byte URL-safe random strings
- **Expiration**: Client secrets never expire by default (configurable)

### Storage

- **In-Memory**: Current implementation uses in-memory storage
- **Production**: Consider implementing persistent storage (database, file system)
- **Encryption**: Store client secrets securely in production environments

## Error Handling

### Client Registration Errors

**400 Bad Request:**
```json
{
  "detail": "redirect_uris must be an array"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or missing registration access token"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

### Client Management Errors

**404 Not Found:**
```json
{
  "detail": "Client not found"
}
```

## Integration with OAuth Flow

1. **Client Registration**: Register client using dynamic registration API
2. **Authorization**: Use registered `client_id` in OAuth authorization flow
3. **Token Exchange**: Authenticate using registered client credentials
4. **API Access**: Use access tokens with Airtable MCP tools

## Implementation Details

### Architecture

```
┌─────────────────────────┐
│   MCP Server            │
│  ┌─────────────────────┐│
│  │ OAuth Endpoints     ││
│  └─────────────────────┘│
│  ┌─────────────────────┐│
│  │ Client Registration ││
│  │ - DynamicClientReg  ││
│  │ - ClientStorage     ││
│  │ - AirtableClientReg ││
│  │   Endpoint          ││
│  └─────────────────────┘│
└─────────────────────────┘
```

### Key Classes

- **`DynamicClientRegistration`**: Main handler for registration endpoints
- **`AirtableClientRegistrationEndpoint`**: RFC 7591 endpoint implementation
- **`ClientStorage`**: In-memory storage for registered clients
- **`RegisteredClient`**: Data model for OAuth clients

## Future Enhancements

- **Persistent Storage**: Database backend for client storage
- **Client Authentication**: Support for additional authentication methods
- **Software Statements**: Support for signed software statements
- **Client Metadata Policies**: Configurable validation policies
- **Rate Limiting**: Prevent abuse of registration endpoints
- **Audit Logging**: Track client registration activities

## Related Specifications

- [RFC 7591 - OAuth 2.0 Dynamic Client Registration Protocol](https://tools.ietf.org/html/rfc7591)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://tools.ietf.org/html/rfc8414)