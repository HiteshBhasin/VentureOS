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
        for rule in self.get_rules(task_type):
            if rule.field:
                value = inputs.get(rule.field)
                if value:
                    validator_func = self._custom_validators.get(rule.validator)
                    if validator_func:
                        result = validator_func(value, **rule.params)
                        if not result.is_valid:
                            return ValidationResult(
                                is_valid=False,
                                errors=[rule.message],
                                warnings=[],
                                field_errors={rule.field: [rule.message]},
                            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_task_output(self, task_type: str, output: Any) -> ValidationResult:
        """Validate output from a task."""
        for rule in self.get_rules(task_type):
            if rule.field:
                value = output.get(rule.field) if isinstance(output, dict) else None
                if value:
                    validator_func = self._custom_validators.get(rule.validator)
                    if validator_func:
                        result = validator_func(value, **rule.params)
                        if not result.is_valid:
                            return ValidationResult(
                                is_valid=False,
                                errors=[rule.message],
                                warnings=[],
                                field_errors={rule.field: [rule.message]},
                            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_task_dependencies(
        self, task: Dict[str, Any], available_tasks: List[str]
    ) -> ValidationResult:
        """Validate task dependencies exist."""
        for key, value in task.items():
            if key == "dependencies" and isinstance(value, list):
                for dep in value:
                    if dep not in available_tasks:
                        return ValidationResult(
                            is_valid=False,
                            errors=[f"Dependency '{dep}' does not exist"],
                            warnings=[],
                            field_errors={
                                "dependencies": [f"missing_dependency_{dep}"]
                            },
                        )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    # ==================== Agent Guardrails ====================

    # Required fields for agent configuration
    REQUIRED_AGENT_CONFIG_FIELDS = {"agent_type", "name"}

    # Valid agent states
    VALID_AGENT_STATES = {
        "idle",
        "running",
        "paused",
        "completed",
        "failed",
        "terminated",
    }

    # Output requirements per agent type
    AGENT_OUTPUT_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
        "coding": {"required_fields": ["code", "language"], "max_output_size": 100000},
        "research": {
            "required_fields": ["findings", "sources"],
            "max_output_size": 50000,
        },
        "review": {"required_fields": ["feedback", "score"], "max_output_size": 20000},
        "runtime": {
            "required_fields": ["result", "exit_code"],
            "max_output_size": 10000,
        },
    }

    def validate_agent_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Guardrail: Validate agent configuration before agent initialization."""
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Check required config fields
        for field in self.REQUIRED_AGENT_CONFIG_FIELDS:
            if field not in config:
                errors.append(f"Missing required config field: {field}")
                field_errors.setdefault(field, []).append("required")

        # Validate agent_type
        if "agent_type" in config:
            if config["agent_type"] not in self.VALID_AGENT_TYPES:
                errors.append(
                    f"Invalid agent_type '{config['agent_type']}'. "
                    f"Must be one of: {', '.join(self.VALID_AGENT_TYPES)}"
                )
                field_errors.setdefault("agent_type", []).append("invalid_value")

        # Validate timeout if present
        if "timeout" in config:
            if (
                not isinstance(config["timeout"], (int, float))
                or config["timeout"] <= 0
            ):
                errors.append("Config 'timeout' must be a positive number")
                field_errors.setdefault("timeout", []).append("invalid_value")

        # Validate max_retries if present
        if "max_retries" in config:
            if not isinstance(config["max_retries"], int) or config["max_retries"] < 0:
                errors.append("Config 'max_retries' must be a non-negative integer")
                field_errors.setdefault("max_retries", []).append("invalid_value")

        # Validate memory_limit if present
        if "memory_limit" in config:
            if (
                not isinstance(config["memory_limit"], int)
                or config["memory_limit"] <= 0
            ):
                warnings.append(
                    "Config 'memory_limit' should be a positive integer (bytes)"
                )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_agent_input(
        self, agent_type: str, input_data: Any
    ) -> ValidationResult:
        """Guardrail: Validate input before passing to an agent."""
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Validate agent_type is known
        if agent_type not in self.VALID_AGENT_TYPES:
            errors.append(f"Unknown agent_type: {agent_type}")
            field_errors.setdefault("agent_type", []).append("invalid_value")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
            )

        # Input must not be None
        if input_data is None:
            errors.append("Agent input cannot be None")
            field_errors.setdefault("input", []).append("null_value")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
            )

        # If input is a dict, validate based on agent type
        if isinstance(input_data, dict):
            # Check for task/prompt field
            if "task" not in input_data and "prompt" not in input_data:
                warnings.append("Input should contain 'task' or 'prompt' field")

            # Agent-specific input validation
            if agent_type == "coding":
                if "language" in input_data and not isinstance(
                    input_data["language"], str
                ):
                    errors.append("Field 'language' must be a string")
                    field_errors.setdefault("language", []).append("invalid_type")

            elif agent_type == "research":
                if "query" not in input_data and "topic" not in input_data:
                    warnings.append(
                        "Research agent input should contain 'query' or 'topic'"
                    )

            elif agent_type == "review":
                if "content" not in input_data and "code" not in input_data:
                    warnings.append(
                        "Review agent input should contain 'content' or 'code' to review"
                    )

        # Check for potentially unsafe content (basic guardrail)
        input_str = str(input_data)
        if len(input_str) > 100000:
            errors.append("Input size exceeds maximum allowed (100KB)")
            field_errors.setdefault("input", []).append("size_exceeded")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_agent_output(self, agent_type: str, output: Any) -> ValidationResult:
        """Guardrail: Validate agent output before returning to caller."""
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Validate agent_type is known
        if agent_type not in self.VALID_AGENT_TYPES:
            errors.append(f"Unknown agent_type: {agent_type}")
            field_errors.setdefault("agent_type", []).append("invalid_value")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
            )

        # Output should not be None for most cases
        if output is None:
            warnings.append("Agent output is None - may indicate incomplete execution")

        # Get output requirements for this agent type
        requirements = self.AGENT_OUTPUT_REQUIREMENTS.get(agent_type, {})
        required_fields = requirements.get("required_fields", [])
        max_size = requirements.get("max_output_size", 50000)

        # Check output size
        output_str = str(output)
        if len(output_str) > max_size:
            errors.append(
                f"Output size exceeds maximum allowed for {agent_type} ({max_size} bytes)"
            )
            field_errors.setdefault("output", []).append("size_exceeded")

        # If output is a dict, check required fields
        if isinstance(output, dict):
            for field in required_fields:
                if field not in output:
                    if self.level == ValidationLevel.STRICT:
                        errors.append(f"Missing required output field: {field}")
                        field_errors.setdefault(field, []).append("required")
                    else:
                        warnings.append(f"Missing expected output field: {field}")

            # Check for error indicators in output
            if output.get("error") or output.get("status") == "error":
                warnings.append("Output contains error status")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_agent_state(
        self, state: str, valid_states: Optional[List[str]] = None
    ) -> ValidationResult:
        """Guardrail: Validate agent state transitions."""
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Use provided valid_states or default
        allowed_states = set(valid_states) if valid_states else self.VALID_AGENT_STATES

        if not state:
            errors.append("Agent state cannot be empty")
            field_errors.setdefault("state", []).append("empty")
        elif state not in allowed_states:
            errors.append(
                f"Invalid agent state '{state}'. Must be one of: {', '.join(allowed_states)}"
            )
            field_errors.setdefault("state", []).append("invalid_value")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

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
        self.level = level
        pass

    def get_level(self) -> ValidationLevel:
        """Get current validation level."""
        return self.level

    def merge_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Merge multiple validation results."""
        result = ValidationResult(
            is_valid=True, errors=[], warnings=[], field_errors={}
        )
        for r in results:
            if not r.is_valid:
                result.is_valid = False
            result.errors.extend(r.errors)
            result.warnings.extend(r.warnings)
            for field, errs in r.field_errors.items():
                result.field_errors.setdefault(field, []).extend(errs)
        return result

    def format_errors(self, result: ValidationResult) -> str:
        """Format validation errors as string."""
        return "\n".join(rerr for rerr in result.errors)
