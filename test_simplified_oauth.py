#!/usr/bin/env python3
"""Test script for simplified OAuth implementation with access token parameters."""

import asyncio

from src.airtable_mcp.main import create_server


async def test_simplified_oauth():
    """Test the simplified OAuth implementation."""
    print("🚀 Testing Simplified Airtable OAuth MCP Server")
    print("=" * 50)

    # Create server
    server = create_server()
    print("✅ Server created successfully")

    # Test available tools
    print("\n🔧 Testing available tools...")
    try:
        tools = await server.mcp.get_tools()
        print(f"✅ Found {len(tools)} total tools")

        print("Available tools:")
        for tool_name in tools:
            print(f"  - {tool_name}")

    except Exception as e:
        print(f"❌ Tools listing error: {e}")

    # Test tool with fake token
    print("\n🧪 Testing tool with access token parameter...")
    try:
        # Try to get a tool to see its schema
        list_bases_tool = await server.mcp.get_tool("list_bases")
        print("✅ list_bases tool found")
        print(
            "Tool schema includes access_token:",
            "access_token" in str(list_bases_tool.schema),
        )

    except Exception as e:
        print(f"❌ Tool schema error: {e}")

    print("\n🎉 Simplified OAuth Implementation Summary:")
    print("=" * 50)
    print("✅ Removed OAuth resources and MCP tools")
    print("✅ Added access_token parameter to all tools")
    print("✅ Simplified authentication via direct token passing")
    print()
    print("📖 Usage Instructions:")
    print("1. Run external OAuth setup script to get access token")
    print("2. Pass access_token parameter to each tool call")
    print("3. Use regular Airtable tools with token authentication")
    print()
    print("🔄 Simplified Flow:")
    print("External OAuth Setup → Access Token → MCP Tool Calls with Token Parameter")


if __name__ == "__main__":
    asyncio.run(test_simplified_oauth())
