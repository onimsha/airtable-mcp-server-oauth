# Airtable OAuth 2.0 Flow Documentation

## Overview

The Airtable OAuth MCP Server implements a comprehensive OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) for secure Airtable API access. This document provides a detailed explanation of the OAuth flow implementation.

## OAuth 2.0 Flow Architecture

The server follows the standard OAuth 2.0 Authorization Code flow with these key components:

- **Authorization Server**: The MCP server acts as an OAuth proxy
- **Client**: MCP clients (Claude Desktop, etc.)
- **Resource Server**: Airtable API
- **Provider**: Airtable OAuth endpoints

## Detailed Flow Steps

### Step 1: Authorization Initiation

1. Client requests OAuth metadata from `GET /.well-known/oauth-authorization-server`
2. MCP server returns OAuth configuration including authorization and token endpoints
3. Client initiates flow by redirecting to `GET /auth/authorize` with:
   - `client_id`: Application's Airtable client ID
   - `response_type=code`: Authorization code flow
   - `scope`: Airtable permissions (data.records:read/write, schema.bases:read/write, etc.)
   - `state`: CSRF protection token
   - `code_challenge` & `code_challenge_method=S256`: PKCE parameters

### Step 2: User Authorization at Airtable

1. MCP server redirects user to Airtable's authorization URL
2. User authenticates with Airtable and grants permissions
3. Airtable redirects back to MCP server's callback: `/auth/callback`

### Step 3: Authorization Code Exchange

1. Callback handler receives authorization `code` and `state`
2. Server validates state parameter for CSRF protection
3. Exchanges code for tokens using `exchange_code_for_tokens()`:
   - Sends POST to `https://airtable.com/oauth2/v1/token`
   - Includes `code_verifier` for PKCE validation
   - Receives `access_token`, `refresh_token`, and `expires_in`

### Step 4: Token Management

1. Access tokens stored with expiration tracking
2. Automatic refresh using `refresh_access_token()` when expired
3. 5-minute expiry margin for proactive refresh

## Security Features

### PKCE (Proof Key for Code Exchange)

Airtable has stricter PKCE requirements than RFC 7636:

- **Code verifier**: 43-128 characters
- **Character set**: `a-zA-Z0-9.-_` (excludes `~`)
- **Methods**: S256 (SHA256) and plain
- **Required**: For all flows

### State Validation

- CSRF protection via `state` parameter
- Server validates state matches between authorization and callback

### Token Security

- Bearer token authentication in API requests
- Automatic token refresh before expiration
- Secure token storage during session

## Airtable-Specific Implementation

### OAuth Endpoints

- **Authorization**: `https://airtable.com/oauth2/v1/authorize`
- **Token**: `https://airtable.com/oauth2/v1/token`

### Supported Scopes

- `data.records:read`: Read record data
- `data.records:write`: Write record data
- `data.recordComments:read`: Read record comments
- `data.recordComments:write`: Write record comments
- `schema.bases:read`: Read base schema
- `schema.bases:write`: Write base schema
- `webhook:manage`: Manage webhooks

### Token Limitations

- **No introspection endpoint**: Returns local token info only
- **No revocation endpoint**: Clears local tokens only

## MCP Integration

### Authentication Middleware

- Intercepts HTTP requests to extract Bearer tokens
- Sets OAuth context for MCP tool calls
- Returns OAuth endpoint info in 401 responses

### API Client Integration

- `AirtableClient` automatically uses valid tokens
- Calls `ensure_valid_token()` before API requests
- Handles token refresh transparently

## Flow Sequence Diagram

```
Client → MCP Server → Airtable
   ↓         ↓          ↓
1. Get OAuth metadata
2. Request /auth/authorize → Redirect to Airtable
3. User authorizes → Callback with code
4. Exchange code for tokens ← Token response
5. Store tokens & redirect client
6. Use Bearer token for API calls
```

## OAuth Endpoints

The MCP server provides these OAuth endpoints:

### Discovery & Metadata
- `GET /.well-known/oauth-authorization-server` - RFC 8414 OAuth metadata
- `GET /.well-known/oauth-protected-resource` - Protected resource metadata
- `GET /.well-known/oauth-authorization-server/mcp` - MCP-specific metadata

### Authorization Flow
- `GET /auth/authorize` - Initiates OAuth flow, redirects to Airtable
- `GET /auth/callback` - Handles callback from Airtable with authorization code
- `POST /token` - Exchanges authorization code for access tokens

### Token Management
- `POST /oauth/refresh` - Refreshes access tokens
- `POST /oauth/introspect` - Introspects token validity
- `POST /oauth/revoke` - Revokes tokens

### Client Registration
- `POST /oauth/register` - Dynamic client registration (RFC 7591)

## Code References

### Key Implementation Files

- **Main Provider**: `src/mcp_oauth_lib/providers/airtable.py` - Airtable OAuth provider implementation
- **Base Provider**: `src/mcp_oauth_lib/providers/base.py` - Abstract OAuth provider interface
- **OAuth Server**: `src/mcp_oauth_lib/core/server.py` - Core OAuth server with FastAPI endpoints
- **OAuth Flow**: `src/mcp_oauth_lib/core/flow.py` - OAuth 2.0 flow logic with PKCE
- **Auth Middleware**: `src/mcp_oauth_lib/auth/middleware.py` - Authentication middleware
- **MCP Server**: `src/airtable_mcp/mcp/server.py` - MCP server integration
- **API Client**: `src/airtable_mcp/api/client.py` - Airtable API client with OAuth
- **Main Entry**: `src/airtable_mcp/main.py` - Server entry point

### Key Classes

- `AirtableOAuthProvider` - Handles Airtable-specific OAuth operations
- `MCPOAuthServer` - Provides OAuth endpoints and flow management
- `OAuthFlow` - Implements OAuth 2.0 authorization code flow with PKCE
- `AirtableMCPServer` - Integrates MCP with OAuth functionality
- `OAuthAuthenticationMiddleware` - Handles token extraction and validation

## Standards Compliance

This implementation follows these OAuth 2.0 and related standards:

- **RFC 6749**: OAuth 2.0 Authorization Framework
- **RFC 7636**: Proof Key for Code Exchange (PKCE)
- **RFC 8414**: OAuth 2.0 Authorization Server Metadata
- **RFC 7591**: OAuth 2.0 Dynamic Client Registration

The implementation ensures secure, standards-compliant OAuth 2.0 authentication while providing seamless integration with MCP clients and Airtable's API.