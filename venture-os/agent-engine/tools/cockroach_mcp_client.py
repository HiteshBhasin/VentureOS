from __future__ import annotations

import inspect
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI


MCP_SERVER_NAME = "cockroachdb-cloud"
mcp_clients: Dict[str, Any] = {}


def _resolve_config_path(config_path: Optional[str] = None) -> Path:
    """Resolve the MCP config file path from common project locations."""
    if config_path:
        path = Path(config_path)
        if path.exists():
            return path
        raise RuntimeError(f"Configured MCP config path not found: {path}")

    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / ".mcp.json",
        repo_root / "tools" / "mcp.json",
        repo_root / "mcp.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = ", ".join(p.as_posix() for p in candidates)
    raise RuntimeError(f"No MCP config file found. Checked: {searched}")


def _load_server_config(
    server_name: str = MCP_SERVER_NAME, config_path: Optional[str] = None
) -> Dict[str, Any]:
    """Load MCP server config from JSON file."""
    cfg_path = _resolve_config_path(config_path)
    with cfg_path.open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    servers = cfg.get("mcpServers") or cfg.get("mcpservers") or {}
    if not isinstance(servers, dict) or server_name not in servers:
        raise RuntimeError(
            f"MCP server '{server_name}' not found in {cfg_path.as_posix()}"
        )

    server_cfg = servers[server_name]
    if not isinstance(server_cfg, dict):
        raise RuntimeError(f"Invalid MCP server config for '{server_name}'")
    if not server_cfg.get("url"):
        raise RuntimeError(f"MCP server '{server_name}' config is missing url")
    return server_cfg


def _build_client(server_cfg: Dict[str, Any]) -> Any:
    """Create a fastmcp client in a version-compatible way."""
    try:
        from fastmcp import Client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "fastmcp is required for Cockroach MCP access. Install it in your "
            "agent-engine environment."
        ) from exc

    url = server_cfg["url"]
    headers = server_cfg.get("headers", {})

    sig = inspect.signature(Client)
    kwargs: Dict[str, Any] = {}
    if "transport" in sig.parameters:
        kwargs["transport"] = url
    elif "url" in sig.parameters:
        kwargs["url"] = url
    else:
        return Client(url)

    if "headers" in sig.parameters:
        kwargs["headers"] = headers
    return Client(**kwargs)


@asynccontextmanager
async def Lifespan(app: FastAPI):
    """FastAPI lifespan hook that opens and stores a shared Cockroach MCP client."""
    _ = app
    server_cfg = _load_server_config(MCP_SERVER_NAME)
    client = _build_client(server_cfg)
    async with client as session:
        mcp_clients["cockroachdb"] = session
        try:
            yield
        finally:
            mcp_clients.clear()


def get_cockroach_client() -> Any:
    """Get the active Cockroach MCP client from lifespan context."""
    client = mcp_clients.get("cockroachdb")
    if client is None:
        raise RuntimeError(
            "Cockroach MCP client is not initialized. Ensure FastAPI lifespan is active."
        )
    return client


async def list_cockroach_tools() -> Any:
    """List tools from the active Cockroach MCP session."""
    client = get_cockroach_client()
    list_tools = getattr(client, "list_tools", None)
    if not callable(list_tools):
        raise RuntimeError("MCP client does not expose list_tools")
    response = list_tools()
    if inspect.isawaitable(response):
        return await response
    return response


async def call_cockroach_tool(
    tool_name: str, arguments: Optional[Dict[str, Any]] = None
) -> Any:
    """Invoke one MCP tool on the active Cockroach MCP session."""
    client = get_cockroach_client()
    call_tool = getattr(client, "call_tool", None)
    if not callable(call_tool):
        raise RuntimeError("MCP client does not expose call_tool")

    args = arguments or {}
    try:
        response = call_tool(tool_name, args)
    except TypeError:
        response = call_tool(name=tool_name, arguments=args)

    if inspect.isawaitable(response):
        return await response
    return response
