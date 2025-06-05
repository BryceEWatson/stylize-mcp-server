"""
E2E MCP client for testing MCP tools.
"""
import asyncio
import base64
import json
from typing import Any

from fastmcp import Client as FastMCPClient


class E2EMCPClient:
    """MCP client for E2E testing."""

    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url
        self.client: FastMCPClient | None = None
        self.connected = False

    async def connect(self):
        """Connect to MCP server."""
        if not self.connected:
            self.client = FastMCPClient(self.mcp_url)
            await self.client.connect()
            self.connected = True

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.connected and self.client:
            await self.client.disconnect()
            self.connected = False
            self.client = None

    async def ensure_connected(self):
        """Ensure client is connected."""
        if not self.connected:
            await self.connect()

    # MCP tool wrappers
    async def start_trial_session(self) -> dict[str, Any]:
        """Start trial session via MCP."""
        await self.ensure_connected()
        result = await self.client.call_tool("start_trial_session", {})
        return json.loads(result)

    async def check_trial_status(self, session_id: str) -> dict[str, Any]:
        """Check trial status via MCP."""
        await self.ensure_connected()
        result = await self.client.call_tool("check_trial_status", {"session_id": session_id})
        return json.loads(result)

    async def stylize_image(
        self,
        image_base64: str,
        style_id: str | None = None,
        user_prompt: str | None = None,
        session_id: str | None = None,
        api_key: str | None = None,
        project_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Stylize image via MCP."""
        await self.ensure_connected()

        args = {"image_base64": image_base64}

        if style_id:
            args["style_id"] = style_id
        if user_prompt:
            args["user_prompt"] = user_prompt
        if session_id:
            args["session_id"] = session_id
        if api_key:
            args["api_key"] = api_key
        if project_context:
            args["project_context"] = project_context

        result = await self.client.call_tool("stylize_image", args)
        return json.loads(result)

    async def generate_image_from_text(
        self,
        prompt: str,
        style_id: str,
        session_id: str | None = None,
        api_key: str | None = None,
        project_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate image from text via MCP."""
        await self.ensure_connected()

        args = {
            "prompt": prompt,
            "style_id": style_id
        }

        if session_id:
            args["session_id"] = session_id
        if api_key:
            args["api_key"] = api_key
        if project_context:
            args["project_context"] = project_context

        result = await self.client.call_tool("generate_image_from_text", args)
        return json.loads(result)

    async def list_styles(self) -> dict[str, Any]:
        """List styles via MCP."""
        await self.ensure_connected()
        result = await self.client.call_tool("list_styles", {})
        return json.loads(result)

    async def get_style_details(self, style_id: str) -> dict[str, Any]:
        """Get style details via MCP."""
        await self.ensure_connected()
        result = await self.client.call_tool("get_style_details", {"style_id": style_id})
        return json.loads(result)

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of available MCP tools."""
        await self.ensure_connected()
        return await self.client.list_tools()

    async def get_available_resources(self) -> list[dict[str, Any]]:
        """Get list of available MCP resources."""
        await self.ensure_connected()
        return await self.client.list_resources()

    # Utility methods for testing
    async def test_connection(self) -> bool:
        """Test MCP connection."""
        try:
            await self.ensure_connected()
            tools = await self.get_available_tools()
            return len(tools) > 0
        except Exception:
            return False

    async def convert_image_to_base64(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    async def measure_tool_response_time(self, tool_name: str, args: dict[str, Any]) -> tuple:
        """Measure response time for a tool call."""
        import time

        await self.ensure_connected()
        start_time = time.time()

        try:
            result = await self.client.call_tool(tool_name, args)
            end_time = time.time()
            response_time = end_time - start_time
            return result, response_time, None
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return None, response_time, str(e)

    async def test_concurrent_requests(
        self,
        tool_name: str,
        args_list: list[dict[str, Any]],
        max_concurrent: int = 5
    ) -> list[tuple]:
        """Test concurrent tool requests."""
        await self.ensure_connected()

        semaphore = asyncio.Semaphore(max_concurrent)

        async def call_with_semaphore(args):
            async with semaphore:
                return await self.measure_tool_response_time(tool_name, args)

        tasks = [call_with_semaphore(args) for args in args_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    # Error simulation for testing error handling
    async def call_tool_with_timeout(
        self,
        tool_name: str,
        args: dict[str, Any],
        timeout_seconds: float = 30.0
    ) -> dict[str, Any]:
        """Call tool with timeout for testing timeout scenarios."""
        await self.ensure_connected()

        try:
            result = await asyncio.wait_for(
                self.client.call_tool(tool_name, args),
                timeout=timeout_seconds
            )
            return {"success": True, "result": json.loads(result), "error": None}
        except asyncio.TimeoutError:
            return {"success": False, "result": None, "error": "timeout"}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    async def validate_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """Validate tool schema and parameters."""
        await self.ensure_connected()
        tools = await self.get_available_tools()

        for tool in tools:
            if tool.get("name") == tool_name:
                return {
                    "found": True,
                    "schema": tool.get("inputSchema", {}),
                    "description": tool.get("description", "")
                }

        return {"found": False, "schema": None, "description": None}
