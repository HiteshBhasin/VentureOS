# Tool registration & discovery
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum


class ToolCategory(Enum):
    """Categories of tools."""

    CODE = "code"
    FILE = "file"
    WEB = "web"
    DATA = "data"
    COMMUNICATION = "communication"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """Defines a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class ToolDefinition:
    """Defines a tool's metadata and schema."""

    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: str = "Any"
    returns_description: str = ""
    examples: List[Dict[str, Any]] = field(default_factory=list)
    requires_auth: bool = False
    rate_limit: Optional[int] = None
    timeout: int = 30
    enabled: bool = True


class ToolRegistry:
    """Registry for discovering and managing tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}

    # ==================== Registration ====================

    def register(self, definition: ToolDefinition, handler: Callable) -> bool:
        """Register a tool with its handler."""
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler
        cat = definition.category
        if cat not in self._categories:
            self._categories[cat] = []
        if definition.name not in self._categories[cat]:
            self._categories[cat].append(definition.name)
        return True

    def register_from_function(
        self, func: Callable, category: ToolCategory = ToolCategory.CUSTOM
    ) -> bool:
        """Register a tool from a decorated function."""
        import inspect

        sig = inspect.signature(func)
        params: List[ToolParameter] = []
        for pname, p in sig.parameters.items():
            if pname == "self":
                continue
            ann = p.annotation
            type_str = ann.__name__ if hasattr(ann, "__name__") else str(ann)
            params.append(
                ToolParameter(
                    name=pname,
                    type=type_str,
                    description=f"Parameter {pname}",
                    required=p.default is inspect.Parameter.empty,
                    default=None if p.default is inspect.Parameter.empty else p.default,
                )
            )
        definition = ToolDefinition(
            name=func.__name__,
            description=func.__doc__ or "",
            category=category,
            parameters=params,
        )
        return self.register(definition, func)

    def register_class(
        self, tool_class: Type, category: ToolCategory = ToolCategory.CUSTOM
    ) -> bool:
        """Register all methods of a class as tools."""
        import inspect

        instance = tool_class()
        for mname, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            if mname.startswith("_"):
                continue
            sig = inspect.signature(method)
            params: List[ToolParameter] = []
            for pname, p in sig.parameters.items():
                if pname == "self":
                    continue
                ann = p.annotation
                type_str = ann.__name__ if hasattr(ann, "__name__") else str(ann)
                params.append(
                    ToolParameter(
                        name=pname,
                        type=type_str,
                        description=f"Parameter {pname}",
                        required=p.default is inspect.Parameter.empty,
                        default=None if p.default is inspect.Parameter.empty else p.default,
                    )
                )
            definition = ToolDefinition(
                name=f"{tool_class.__name__}.{mname}",
                description=method.__doc__ or "",
                category=category,
                parameters=params,
            )
            self.register(definition, method)
        return True

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name not in self._tools:
            return False
        definition = self._tools.pop(name)
        self._handlers.pop(name, None)
        cat = definition.category
        if cat in self._categories and name in self._categories[cat]:
            self._categories[cat].remove(name)
        return True

    def update_tool(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update tool definition."""
        if name not in self._tools:
            return False
        tool = self._tools[name]
        for key, value in updates.items():
            if hasattr(tool, key):
                setattr(tool, key, value)
        return True

    # ==================== Discovery ====================

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler by name."""
        return self._handlers.get(name)

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_enabled_tools(self) -> List[ToolDefinition]:
        """Get all enabled tools."""
        return [t for t in self._tools.values() if t.enabled]

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Get tools by category."""
        names = self._categories.get(category, [])
        return [self._tools[n] for n in names if n in self._tools]

    def search_tools(self, query: str) -> List[ToolDefinition]:
        """Search tools by name or description."""
        q = query.lower()
        return [
            t
            for t in self._tools.values()
            if q in t.name.lower() or q in t.description.lower()
        ]

    def list_tool_names(self) -> List[str]:
        """List all tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    # ==================== Tool Management ====================

    def enable_tool(self, name: str) -> bool:
        """Enable a tool."""
        if name not in self._tools:
            return False
        self._tools[name].enabled = True
        return True

    def disable_tool(self, name: str) -> bool:
        """Disable a tool."""
        if name not in self._tools:
            return False
        self._tools[name].enabled = False
        return True

    def set_rate_limit(self, name: str, limit: int) -> bool:
        """Set rate limit for a tool."""
        if name not in self._tools:
            return False
        self._tools[name].rate_limit = limit
        return True

    def set_timeout(self, name: str, timeout: int) -> bool:
        """Set timeout for a tool."""
        if name not in self._tools:
            return False
        self._tools[name].timeout = timeout
        return True

    # ==================== Schema Generation ====================

    def get_openai_schema(self, name: str) -> Dict[str, Any]:
        """Get OpenAI function calling schema for tool."""
        tool = self._tools.get(name)
        if not tool:
            return {}
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in tool.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def get_all_openai_schemas(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get OpenAI schemas for all tools."""
        tools = self.get_enabled_tools() if enabled_only else self.get_all_tools()
        return [self.get_openai_schema(t.name) for t in tools]

    def get_anthropic_schema(self, name: str) -> Dict[str, Any]:
        """Get Anthropic tool schema for tool."""
        tool = self._tools.get(name)
        if not tool:
            return {}
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in tool.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def get_all_anthropic_schemas(
        self, enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get Anthropic schemas for all tools."""
        tools = self.get_enabled_tools() if enabled_only else self.get_all_tools()
        return [self.get_anthropic_schema(t.name) for t in tools]

    def get_json_schema(self, name: str) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        tool = self._tools.get(name)
        if not tool:
            return {}
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in tool.parameters:
            prop: Dict[str, Any] = {"type": p.type, "description": p.description}
            if p.default is not None:
                prop["default"] = p.default
            if p.enum:
                prop["enum"] = p.enum
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": tool.name,
            "description": tool.description,
            "type": "object",
            "properties": properties,
            "required": required,
        }

    # ==================== Validation ====================

    def validate_input(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool inputs. Returns validation result."""
        tool = self._tools.get(name)
        if not tool:
            return {"valid": False, "errors": [f"Tool '{name}' not found"]}
        errors: List[str] = []
        for p in tool.parameters:
            if p.required and p.name not in inputs:
                errors.append(f"Missing required parameter: {p.name}")
            if p.name in inputs and p.enum and inputs[p.name] not in p.enum:
                errors.append(f"Parameter '{p.name}' must be one of {p.enum}")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_output(self, name: str, output: Any) -> bool:
        """Validate tool output."""
        return output is not None

    def get_required_params(self, name: str) -> List[str]:
        """Get required parameters for tool."""
        tool = self._tools.get(name)
        return [p.name for p in tool.parameters if p.required] if tool else []

    def get_optional_params(self, name: str) -> List[str]:
        """Get optional parameters for tool."""
        tool = self._tools.get(name)
        return [p.name for p in tool.parameters if not p.required] if tool else []

    # ==================== Bulk Operations ====================

    def register_bulk(
        self, tools: List[Tuple[ToolDefinition, Callable]]
    ) -> Dict[str, bool]:
        """Register multiple tools."""
        return {defn.name: self.register(defn, handler) for defn, handler in tools}

    def disable_category(self, category: ToolCategory) -> int:
        """Disable all tools in category. Returns count."""
        count = 0
        for name in self._categories.get(category, []):
            if name in self._tools and self._tools[name].enabled:
                self._tools[name].enabled = False
                count += 1
        return count

    def enable_category(self, category: ToolCategory) -> int:
        """Enable all tools in category. Returns count."""
        count = 0
        for name in self._categories.get(category, []):
            if name in self._tools and not self._tools[name].enabled:
                self._tools[name].enabled = True
                count += 1
        return count

    def clear(self) -> None:
        """Clear all tools from registry."""
        self._tools.clear()
        self._handlers.clear()
        self._categories.clear()

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": sum(1 for t in self._tools.values() if t.enabled),
            "disabled_tools": sum(1 for t in self._tools.values() if not t.enabled),
            "categories": {cat.value: count for cat, count in self.get_category_counts().items()},
        }

    def get_category_counts(self) -> Dict[ToolCategory, int]:
        """Get tool counts by category."""
        return {cat: len(names) for cat, names in self._categories.items()}

    # ==================== Export/Import ====================

    def export_definitions(self) -> List[Dict[str, Any]]:
        """Export all tool definitions."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                        "default": p.default,
                        "enum": p.enum,
                    }
                    for p in t.parameters
                ],
                "returns": t.returns,
                "returns_description": t.returns_description,
                "requires_auth": t.requires_auth,
                "rate_limit": t.rate_limit,
                "timeout": t.timeout,
                "enabled": t.enabled,
            }
            for t in self._tools.values()
        ]

    def import_definitions(self, definitions: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Import tool definitions (registers with a no-op handler)."""
        results: Dict[str, bool] = {}
        for defn in definitions:
            try:
                params = [
                    ToolParameter(
                        name=p["name"],
                        type=p.get("type", "Any"),
                        description=p.get("description", ""),
                        required=p.get("required", True),
                        default=p.get("default"),
                        enum=p.get("enum"),
                    )
                    for p in defn.get("parameters", [])
                ]
                tool = ToolDefinition(
                    name=defn["name"],
                    description=defn.get("description", ""),
                    category=ToolCategory(defn.get("category", "custom")),
                    parameters=params,
                    returns=defn.get("returns", "Any"),
                    returns_description=defn.get("returns_description", ""),
                    requires_auth=defn.get("requires_auth", False),
                    rate_limit=defn.get("rate_limit"),
                    timeout=defn.get("timeout", 30),
                    enabled=defn.get("enabled", True),
                )
                self._tools[tool.name] = tool
                if tool.category not in self._categories:
                    self._categories[tool.category] = []
                if tool.name not in self._categories[tool.category]:
                    self._categories[tool.category].append(tool.name)
                results[tool.name] = True
            except Exception:
                results[defn.get("name", "unknown")] = False
        return results

    def to_documentation(self, format: str = "markdown") -> str:
        """Generate documentation for all tools."""
        lines: List[str] = []
        if format == "markdown":
            lines.append("# Tool Documentation\n")
            for cat, names in self._categories.items():
                lines.append(f"## {cat.value.title()}\n")
                for name in names:
                    tool = self._tools.get(name)
                    if not tool:
                        continue
                    status = "[enabled]" if tool.enabled else "[disabled]"
                    lines.append(f"### {status} `{tool.name}`\n")
                    lines.append(f"{tool.description}\n")
                    if tool.parameters:
                        lines.append("**Parameters:**\n")
                        for p in tool.parameters:
                            req = "required" if p.required else f"optional, default: `{p.default}`"
                            lines.append(f"- `{p.name}` ({p.type}, {req}): {p.description}")
                    lines.append("")
        else:
            for tool in self._tools.values():
                lines.append(f"{tool.name}: {tool.description}")
        return "\n".join(lines)
