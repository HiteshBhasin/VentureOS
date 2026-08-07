"""Bedrock-facing MCP bridge.

This module exposes a small synchronous API that the orchestrator can register
as tools. Under the hood it talks to an MCP server via the fastmcp client.
"""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from threading import Thread
from typing import Any, Dict, Optional


class BedrockMCPTool:
	"""Bridge to list and invoke MCP tools for Bedrock-driven agents."""

	def __init__(self, config_path: Optional[str] = None) -> None:
		self._config_path_override = config_path

	def list_tools(self, server_name: str = "cockroachdb-cloud") -> Dict[str, Any]:
		"""List available MCP tools from a configured server."""
		tools = self._run(self._list_tools_async(server_name))
		return {
			"server": server_name,
			"tools": [self._to_jsonable(tool) for tool in tools],
			"count": len(tools),
		}

	def call_tool(
		self,
		tool_name: str,
		arguments: Optional[Dict[str, Any]] = None,
		server_name: str = "cockroachdb-cloud",
	) -> Dict[str, Any]:
		"""Invoke an MCP tool by name with JSON arguments."""
		args = arguments or {}
		result = self._run(self._call_tool_async(server_name, tool_name, args))
		return {
			"server": server_name,
			"tool": tool_name,
			"arguments": args,
			"result": self._to_jsonable(result),
		}

	async def _list_tools_async(self, server_name: str) -> Any:
		server_cfg = self._load_server_config(server_name)
		client = self._make_client(server_cfg)
		async with client as session:
			return await session.list_tools()

	async def _call_tool_async(
		self, server_name: str, tool_name: str, arguments: Dict[str, Any]
	) -> Any:
		server_cfg = self._load_server_config(server_name)
		client = self._make_client(server_cfg)
		async with client as session:
			call_tool = getattr(session, "call_tool", None)
			if not callable(call_tool):
				raise RuntimeError("MCP client does not expose call_tool")
			try:
				response = call_tool(tool_name, arguments)
			except TypeError:
				# Some client versions require named parameters.
				response = call_tool(name=tool_name, arguments=arguments)

			if inspect.isawaitable(response):
				return await response
			return response

	def _make_client(self, server_cfg: Dict[str, Any]) -> Any:
		try:
			from fastmcp import Client  # type: ignore[import-not-found]
		except ImportError as exc:
			raise ImportError(
				"fastmcp is required for MCP access. Install it in your "
				"agent-engine environment."
			) from exc

		url = server_cfg.get("url")
		headers = server_cfg.get("headers", {})
		if not url:
			raise RuntimeError("MCP server configuration is missing 'url'")

		# Keep compatibility across fastmcp versions by only passing
		# constructor arguments that are actually supported.
		sig = inspect.signature(Client)
		kwargs: Dict[str, Any] = {}
		if "transport" in sig.parameters:
			kwargs["transport"] = url
		elif "url" in sig.parameters:
			kwargs["url"] = url
		else:
			# Last-resort fallback for constructors that accept a positional URL.
			return Client(url)

		if "headers" in sig.parameters:
			kwargs["headers"] = headers
		return Client(**kwargs)

	def _load_server_config(self, server_name: str) -> Dict[str, Any]:
		cfg_path = self._resolve_config_path()
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
		return server_cfg

	def _resolve_config_path(self) -> Path:
		if self._config_path_override:
			path = Path(self._config_path_override)
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

	def _run(self, coro: Any) -> Any:
		try:
			asyncio.get_running_loop()
		except RuntimeError:
			return asyncio.run(coro)

		holder: Dict[str, Any] = {"result": None, "error": None}

		def _runner() -> None:
			try:
				holder["result"] = asyncio.run(coro)
			except Exception as exc:  # pragma: no cover - pass through only
				holder["error"] = exc

		thread = Thread(target=_runner, daemon=True)
		thread.start()
		thread.join()
		if holder["error"] is not None:
			raise holder["error"]
		return holder["result"]

	def _to_jsonable(self, value: Any) -> Any:
		if value is None or isinstance(value, (str, int, float, bool)):
			return value
		if isinstance(value, dict):
			return {str(k): self._to_jsonable(v) for k, v in value.items()}
		if isinstance(value, (list, tuple, set)):
			return [self._to_jsonable(v) for v in value]
		if hasattr(value, "model_dump") and callable(value.model_dump):
			return self._to_jsonable(value.model_dump())
		if hasattr(value, "dict") and callable(value.dict):
			return self._to_jsonable(value.dict())
		if hasattr(value, "__dict__"):
			return self._to_jsonable(vars(value))
		return str(value)
