# Tool registration & discovery
from typing import Any, Callable, Dict, List, Optional, Type
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
        pass

    def register_from_function(
        self, func: Callable, category: ToolCategory = ToolCategory.CUSTOM
    ) -> bool:
        """Register a tool from a decorated function."""
        pass

    def register_class(
        self, tool_class: Type, category: ToolCategory = ToolCategory.CUSTOM
    ) -> bool:
        """Register all methods of a class as tools."""
        pass

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        pass

    def update_tool(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update tool definition."""
        pass

    # ==================== Discovery ====================

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        pass

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler by name."""
        pass

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        pass

    def get_enabled_tools(self) -> List[ToolDefinition]:
        """Get all enabled tools."""
        pass

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Get tools by category."""
        pass

    def search_tools(self, query: str) -> List[ToolDefinition]:
        """Search tools by name or description."""
        pass

    def list_tool_names(self) -> List[str]:
        """List all tool names."""
        pass

    def has_tool(self, name: str) -> bool:
        """Check if tool is registered."""
        pass

    # ==================== Tool Management ====================

    def enable_tool(self, name: str) -> bool:
        """Enable a tool."""
        pass

    def disable_tool(self, name: str) -> bool:
        """Disable a tool."""
        pass

    def set_rate_limit(self, name: str, limit: int) -> bool:
        """Set rate limit for a tool."""
        pass

    def set_timeout(self, name: str, timeout: int) -> bool:
        """Set timeout for a tool."""
        pass

    # ==================== Schema Generation ====================

    def get_openai_schema(self, name: str) -> Dict[str, Any]:
        """Get OpenAI function calling schema for tool."""
        pass

    def get_all_openai_schemas(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get OpenAI schemas for all tools."""
        pass

    def get_anthropic_schema(self, name: str) -> Dict[str, Any]:
        """Get Anthropic tool schema for tool."""
        pass

    def get_all_anthropic_schemas(
        self, enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get Anthropic schemas for all tools."""
        pass

    def get_json_schema(self, name: str) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        pass

    # ==================== Validation ====================

    def validate_input(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool inputs. Returns validation result."""
        pass

    def validate_output(self, name: str, output: Any) -> bool:
        """Validate tool output."""
        pass

    def get_required_params(self, name: str) -> List[str]:
        """Get required parameters for tool."""
        pass

    def get_optional_params(self, name: str) -> List[str]:
        """Get optional parameters for tool."""
        pass

    # ==================== Bulk Operations ====================

    def register_bulk(
        self, tools: List[Tuple[ToolDefinition, Callable]]
    ) -> Dict[str, bool]:
        """Register multiple tools."""
        pass

    def disable_category(self, category: ToolCategory) -> int:
        """Disable all tools in category. Returns count."""
        pass

    def enable_category(self, category: ToolCategory) -> int:
        """Enable all tools in category. Returns count."""
        pass

    def clear(self) -> None:
        """Clear all tools from registry."""
        pass

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        pass

    def get_category_counts(self) -> Dict[ToolCategory, int]:
        """Get tool counts by category."""
        pass

    # ==================== Export/Import ====================

    def export_definitions(self) -> List[Dict[str, Any]]:
        """Export all tool definitions."""
        pass

    def import_definitions(self, definitions: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Import tool definitions."""
        pass

    def to_documentation(self, format: str = "markdown") -> str:
        """Generate documentation for all tools."""
        pass
