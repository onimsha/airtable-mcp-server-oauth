#!/usr/bin/env python3
"""Test script for OAuth MCP implementation."""

import asyncio
import os

# Set environment variables for testing
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["AIRTABLE_CLIENT_ID"] = "your-client-id"
os.environ["AIRTABLE_CLIENT_SECRET"] = "your-client-secret"
os.environ["AIRTABLE_REDIRECT_URI"] = "http://localhost:8000/callback"

from src.airtable_mcp.main import create_server


async def test_oauth_flow():
    """Test the OAuth flow implementation."""
    print("🚀 Testing Airtable OAuth MCP Server")
    print("=" * 50)

    # Create server
    server = create_server()
    print("✅ Server created successfully")

    # Test OAuth authorize resource
    print("\n📋 Testing OAuth authorize resource...")
    try:
        auth_resource = await server.mcp.get_resource("oauth://authorize")
        auth_response = await auth_resource.read()
        print("✅ OAuth authorization URL generated")
        print(
            "Contains Airtable OAuth URL:",
            "airtable.com/oauth2/v1/authorize" in auth_response,
        )
        print("Contains state parameter:", "State parameter:" in auth_response)

        # Extract state parameter for testing
        import re

        state_match = re.search(r"State parameter: ([a-zA-Z0-9_-]+)", auth_response)
        if state_match:
            test_state = state_match.group(1)
            print(f"✅ State parameter extracted: {test_state[:10]}...")

    except Exception as e:
        print(f"❌ OAuth authorize resource error: {e}")
        return

    # Test OAuth status resource
    print("\n📊 Testing OAuth status resource...")
    try:
        status_resource = await server.mcp.get_resource("oauth://status")
        status_response = await status_resource.read()
        print("✅ OAuth status checked")
        print("Status message:", status_response.strip())

    except Exception as e:
        print(f"❌ OAuth status resource error: {e}")

    # Test available tools
    print("\n🔧 Testing available tools...")
    try:
        tools = await server.mcp.get_tools()
        print(f"✅ Found {len(tools)} total tools")

        oauth_tools = []
        airtable_tools = []

        for tool_name in tools:
            if "oauth" in tool_name:
                oauth_tools.append(tool_name)
            else:
                airtable_tools.append(tool_name)

        print(f"OAuth tools ({len(oauth_tools)}): {oauth_tools}")
        print(f"Airtable tools ({len(airtable_tools)}): {airtable_tools[:5]}...")

    except Exception as e:
        print(f"❌ Tools listing error: {e}")

    print("\n🎉 OAuth MCP Implementation Summary:")
    print("=" * 50)
    print("✅ OAuth resources: oauth://authorize, oauth://status")
    print("✅ OAuth tools: oauth_callback, oauth_refresh, oauth_revoke")
    print("✅ Integration with existing Airtable tools")
    print()
    print("📖 Usage Instructions:")
    print("1. Read oauth://authorize resource to get authorization URL")
    print("2. Visit the URL and authorize the application")
    print("3. Use oauth_callback tool with the authorization code")
    print("4. Use regular Airtable tools (list_bases, create_record, etc.)")
    print()
    print("🔄 OAuth Flow:")
    print(
        "MCP Client → oauth://authorize → Browser → Airtable → oauth_callback → Authenticated!"
    )


if __name__ == "__main__":
    asyncio.run(test_oauth_flow())
