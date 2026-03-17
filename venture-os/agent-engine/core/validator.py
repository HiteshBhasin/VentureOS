# Meta-Agent Validation
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Validation strictness levels."""

    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_errors: Dict[str, List[str]]


@dataclass
class ValidationRule:
    """Defines a validation rule."""

    name: str
    field: Optional[str]
    validator: str
    params: Dict[str, Any]
    message: str
    level: ValidationLevel = ValidationLevel.NORMAL


class Validator:
    """Validates tasks, configurations, and agent outputs."""

    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._custom_validators: Dict[str, Any] = {}

    # ==================== Task Validation ====================

    # Valid values for task fields
    VALID_STATUSES = {
        "pending",
        "ready",
        "running",
        "completed",
        "failed",
        "skipped",
        "cancelled",
    }
    VALID_AGENT_TYPES = {"coding", "research", "review", "runtime"}
    REQUIRED_TASK_FIELDS = {"id", "name", "status", "agent_type"}

    def validate_task(self, task: Dict[str, Any]) -> ValidationResult:
        """Validate a task definition.

        Expected task structure:
        {
            "id": str,           # Required - unique task identifier
            "name": str,         # Required - task name
            "description": str,  # Optional - task description
            "status": str,       # Required - one of VALID_STATUSES
            "dependencies": [],  # Optional - list of dependent task IDs
            "agent_type": str,   # Required - one of VALID_AGENT_TYPES
            "priority": int      # Optional - task priority (1-10)
        }
        """
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Check required fields
        for field in self.REQUIRED_TASK_FIELDS:
            if field not in task:
                errors.append(f"Missing required field: {field}")
                field_errors.setdefault(field, []).append("required")
            elif task[field] is None or task[field] == "":
                errors.append(f"Field '{field}' cannot be empty")
                field_errors.setdefault(field, []).append("empty")

        # Validate 'id' field
        if "id" in task and task["id"]:
            if not isinstance(task["id"], str):
                errors.append("Field 'id' must be a string")
                field_errors.setdefault("id", []).append("invalid_type")

        # Validate 'name' field
        if "name" in task and task["name"]:
            if not isinstance(task["name"], str):
                errors.append("Field 'name' must be a string")
                field_errors.setdefault("name", []).append("invalid_type")
            elif len(task["name"]) < 2:
                warnings.append("Task name is very short")

        # Validate 'status' field
        if "status" in task and task["status"]:
            if task["status"] not in self.VALID_STATUSES:
                errors.append(
                    f"Invalid status '{task['status']}'. Must be one of: {', '.join(self.VALID_STATUSES)}"
                )
                field_errors.setdefault("status", []).append("invalid_value")

        # Validate 'agent_type' field
        if "agent_type" in task and task["agent_type"]:
            if task["agent_type"] not in self.VALID_AGENT_TYPES:
                errors.append(
                    f"Invalid agent_type '{task['agent_type']}'. Must be one of: {', '.join(self.VALID_AGENT_TYPES)}"
                )
                field_errors.setdefault("agent_type", []).append("invalid_value")

        # Validate 'dependencies' field (optional)
        if "dependencies" in task:
            if not isinstance(task["dependencies"], list):
                errors.append("Field 'dependencies' must be a list")
                field_errors.setdefault("dependencies", []).append("invalid_type")
            else:
                for i, dep in enumerate(task["dependencies"]):
                    if not isinstance(dep, str):
                        errors.append(f"Dependency at index {i} must be a string")
                        field_errors.setdefault("dependencies", []).append(
                            f"invalid_item_{i}"
                        )

        # Validate 'priority' field (optional)
        if "priority" in task:
            if not isinstance(task["priority"], int):
                errors.append("Field 'priority' must be an integer")
                field_errors.setdefault("priority", []).append("invalid_type")
            elif not (1 <= task["priority"] <= 10):
                warnings.append(
                    f"Priority {task['priority']} is outside recommended range (1-10)"
                )

        # Validate 'description' field (optional)
        if "description" in task and task["description"]:
            if not isinstance(task["description"], str):
                errors.append("Field 'description' must be a string")
                field_errors.setdefault("description", []).append("invalid_type")

        # In LENIENT mode, convert some errors to warnings
        if self.level == ValidationLevel.LENIENT:
            # Move non-critical errors to warnings
            non_critical = [
                e
                for e in errors
                if "priority" in e.lower() or "description" in e.lower()
            ]
            errors = [e for e in errors if e not in non_critical]
            warnings.extend(non_critical)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_task_input(
        self, task_type: str, inputs: Dict[str, Any]
    ) -> ValidationResult:
        """Validate inputs for a specific task type."""
        pass

    def validate_task_output(self, task_type: str, output: Any) -> ValidationResult:
        """Validate output from a task."""
        pass

    def validate_task_dependencies(
        self, task: Dict[str, Any], available_tasks: List[str]
    ) -> ValidationResult:
        """Validate task dependencies exist."""
        pass

    # ==================== Agent Validation ====================

    def validate_agent_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate agent configuration."""
        pass

    def validate_agent_output(self, agent_type: str, output: Any) -> ValidationResult:
        """Validate agent output."""
        pass

    def validate_agent_state(
        self, state: str, valid_states: List[str]
    ) -> ValidationResult:
        """Validate agent state."""
        pass

    # ==================== Schema Validation ====================

    def validate_against_schema(
        self, data: Any, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate data against a JSON schema."""
        pass

    def validate_type(self, value: Any, expected_type: Type) -> bool:
        """Validate value is of expected type."""
        pass

    def validate_required_fields(
        self, data: Dict[str, Any], required: List[str]
    ) -> ValidationResult:
        """Validate required fields are present."""
        pass

    def validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, Type]
    ) -> ValidationResult:
        """Validate field types match expected."""
        pass

    # ==================== Data Validation ====================

    def validate_string(
        self,
        value: str,
        min_length: int = 0,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> ValidationResult:
        """Validate string value."""
        pass

    def validate_number(
        self,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> ValidationResult:
        """Validate numeric value."""
        pass

    def validate_list(
        self,
        value: List,
        min_items: int = 0,
        max_items: Optional[int] = None,
        item_type: Optional[Type] = None,
    ) -> ValidationResult:
        """Validate list value."""
        pass

    def validate_dict(
        self, value: Dict, required_keys: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate dictionary value."""
        pass

    def validate_enum(self, value: Any, allowed_values: List[Any]) -> ValidationResult:
        """Validate value is in allowed values."""
        pass

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL format."""
        pass

    def validate_email(self, email: str) -> ValidationResult:
        """Validate email format."""
        pass

    def validate_json(self, json_str: str) -> ValidationResult:
        """Validate JSON string."""
        pass

    # ==================== Business Rule Validation ====================

    def validate_budget_constraints(
        self, task: Dict[str, Any], budget: Dict[str, float]
    ) -> ValidationResult:
        """Validate task against budget constraints."""
        pass

    def validate_permissions(
        self, action: str, user_permissions: List[str]
    ) -> ValidationResult:
        """Validate action against permissions."""
        pass

    def validate_rate_limits(
        self, request_count: int, limit: int, period: str
    ) -> ValidationResult:
        """Validate against rate limits."""
        pass

    # ==================== Rule Management ====================

    def add_rule(self, entity_type: str, rule: ValidationRule) -> None:
        """Add a validation rule."""
        pass

    def remove_rule(self, entity_type: str, rule_name: str) -> bool:
        """Remove a validation rule."""
        pass

    def get_rules(self, entity_type: str) -> List[ValidationRule]:
        """Get validation rules for entity type."""
        pass

    def clear_rules(self, entity_type: Optional[str] = None) -> None:
        """Clear validation rules."""
        pass

    # ==================== Custom Validators ====================

    def register_validator(self, name: str, validator_func: Any) -> None:
        """Register a custom validator function."""
        pass

    def unregister_validator(self, name: str) -> bool:
        """Unregister a custom validator."""
        pass

    def run_custom_validator(self, name: str, value: Any, **kwargs) -> ValidationResult:
        """Run a custom validator."""
        pass

    # ==================== Batch Validation ====================

    def validate_batch(
        self, items: List[Dict[str, Any]], validator_name: str
    ) -> List[ValidationResult]:
        """Validate a batch of items."""
        pass

    def validate_all(
        self, data: Dict[str, Any], rules: List[ValidationRule]
    ) -> ValidationResult:
        """Validate data against multiple rules."""
        pass

    # ==================== Utilities ====================

    def set_level(self, level: ValidationLevel) -> None:
        """Set validation level."""
        pass

    def get_level(self) -> ValidationLevel:
        """Get current validation level."""
        pass

    def merge_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Merge multiple validation results."""
        pass

    def format_errors(self, result: ValidationResult) -> str:
        """Format validation errors as string."""
        pass
