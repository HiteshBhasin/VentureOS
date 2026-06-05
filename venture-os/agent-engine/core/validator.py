# Meta-Agent Validation
import json
import re
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

    # ==================== Generated Agent Code Validation ====================

    def validate_generated_agent_code(
        self,
        code: str,
        expected_class_name: str,
        capabilities: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Validate LLM-generated agent code before exec_module().

        Uses Python's ast module for structural checks and _DANGEROUS_PATTERNS
        from CodeExecutor for security scanning.

        Checks enforced:
          1. Valid Python syntax
          2. Security scan (no eval/exec/os.system/subprocess/socket/requests etc.)
          3. Class named expected_class_name exists
          4. Class inherits from BaseAgent
          5. execute_task method is defined
          6. execute_task routes on task.get("type") not another key
          7. Each capability has a corresponding method
        """
        import ast as _ast

        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        # Check 1 — Valid Python syntax
        try:
            tree = _ast.parse(code)
        except SyntaxError as exc:
            return ValidationResult(
                is_valid=False,
                errors=[f"Syntax error in generated code: {exc}"],
                warnings=[],
                field_errors={"syntax": ["parse_error"]},
            )

        # Check 2 — Security scan using _DANGEROUS_PATTERNS from CodeExecutor
        from tools.code_executor import CodeExecutor

        for pattern, description in CodeExecutor._DANGEROUS_PATTERNS.get("python", []):
            if re.search(pattern, code):
                errors.append(f"Security violation: {description}")
                field_errors.setdefault("security", []).append(description)

        # Fail immediately on security violations — do not proceed
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
            )

        # Check 3 — Class with expected name exists
        class_node: Optional[_ast.ClassDef] = None
        for node in _ast.walk(tree):
            if isinstance(node, _ast.ClassDef) and node.name == expected_class_name:
                class_node = node
                break

        if class_node is None:
            errors.append(
                f"Expected class '{expected_class_name}' not found in generated code"
            )
            field_errors.setdefault("class", []).append("missing_class")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                field_errors=field_errors,
            )

        # Check 4 — Class inherits from BaseAgent
        base_names: List[str] = []
        for base in class_node.bases:
            if isinstance(base, _ast.Name):
                base_names.append(base.id)
            elif isinstance(base, _ast.Attribute):
                base_names.append(base.attr)
        if "BaseAgent" not in base_names:
            errors.append(
                f"Class '{expected_class_name}' does not inherit from BaseAgent "
                f"(found: {base_names or ['none']})"
            )
            field_errors.setdefault("class", []).append("missing_base_class")

        # Collect all method names defined directly on the class
        method_names = [
            node.name
            for node in _ast.walk(class_node)
            if isinstance(node, _ast.FunctionDef)
        ]

        # Check 5 — execute_task method exists
        if "execute_task" not in method_names:
            errors.append(
                f"Class '{expected_class_name}' is missing required 'execute_task' method"
            )
            field_errors.setdefault("methods", []).append("missing_execute_task")
        else:
            # Check 6 — execute_task routes on task.get("type")
            execute_task_node = next(
                (
                    n
                    for n in _ast.walk(class_node)
                    if isinstance(n, _ast.FunctionDef) and n.name == "execute_task"
                ),
                None,
            )
            if execute_task_node is not None:
                method_src = _ast.unparse(execute_task_node)
                if '"type"' not in method_src and "'type'" not in method_src:
                    warnings.append(
                        'execute_task does not route on task.get("type") — '
                        "may use wrong routing key"
                    )
                    field_errors.setdefault("methods", []).append("wrong_routing_key")

        # Check 7 — Each capability has a corresponding method
        for cap in capabilities or []:
            # Strip optional signature (everything from '(' onward) before normalising
            bare = cap.split("(")[0]
            method_name = re.sub(r"[\s\-]+", "_", bare.lower().strip())
            if method_name not in method_names:
                warnings.append(
                    f"Capability '{cap}' has no corresponding method '{method_name}'"
                )
                field_errors.setdefault("capabilities", []).append(
                    f"missing_{method_name}"
                )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

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
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        schema_type = schema.get("type")

        if schema_type == "object":
            if not isinstance(data, dict):
                errors.append("Data must be a JSON object")
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    field_errors=field_errors,
                )
            for field in schema.get("required", []):
                if field not in data:
                    errors.append(f"Missing required field: {field}")
                    field_errors.setdefault(field, []).append("required")
            for field, field_schema in schema.get("properties", {}).items():
                if field in data:
                    sub = self.validate_against_schema(data[field], field_schema)
                    errors.extend(f"{field}: {e}" for e in sub.errors)
                    warnings.extend(sub.warnings)
                    if sub.field_errors:
                        field_errors.setdefault(field, []).extend(sub.errors)

        elif schema_type == "array":
            if not isinstance(data, list):
                errors.append("Data must be an array")
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    field_errors=field_errors,
                )
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    sub = self.validate_against_schema(item, items_schema)
                    errors.extend(f"[{i}]: {e}" for e in sub.errors)

        elif schema_type == "string":
            if not isinstance(data, str):
                errors.append("Value must be a string")
            else:
                min_len = schema.get("minLength", 0)
                max_len = schema.get("maxLength")
                if len(data) < min_len:
                    errors.append(f"String is too short (min length {min_len})")
                if max_len is not None and len(data) > max_len:
                    errors.append(f"String is too long (max length {max_len})")
                pattern = schema.get("pattern")
                if pattern and not re.search(pattern, data):
                    errors.append(f"String does not match required pattern")

        elif schema_type in ("integer", "number"):
            expected: Any = int if schema_type == "integer" else (int, float)
            if not isinstance(data, expected):
                errors.append(f"Value must be a {schema_type}")
            else:
                if "minimum" in schema and data < schema["minimum"]:
                    errors.append(f"Value must be >= {schema['minimum']}")
                if "maximum" in schema and data > schema["maximum"]:
                    errors.append(f"Value must be <= {schema['maximum']}")

        elif schema_type == "boolean":
            if not isinstance(data, bool):
                errors.append("Value must be a boolean")

        enum_values = schema.get("enum")
        if enum_values is not None and data not in enum_values:
            errors.append(f"Value must be one of: {enum_values}")
            field_errors.setdefault("value", []).append("invalid_enum")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_type(self, value: Any, expected_type: Type) -> bool:
        """Validate value is of expected type."""
        return isinstance(value, expected_type)

    def validate_required_fields(
        self, data: Dict[str, Any], required: List[str]
    ) -> ValidationResult:
        """Validate required fields are present."""
        for field in required:
            if field not in data:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Missing required field: {field}"],
                    warnings=[],
                    field_errors={field: ["required"]},
                )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, Type]
    ) -> ValidationResult:
        """Validate field types match expected."""
        errors: List[str] = []
        field_errors: Dict[str, List[str]] = {}
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be of type {expected_type.__name__}"
                )
                field_errors.setdefault(field, []).append("invalid_type")
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid, errors=errors, warnings=[], field_errors=field_errors
        )

    # ==================== Data Validation ====================

    def validate_string(
        self,
        value: str,
        min_length: int = 0,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> ValidationResult:
        """Validate string value."""
        errors: List[str] = []
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                errors=["Value must be a string"],
                warnings=[],
                field_errors={"value": ["invalid_type"]},
            )
        if len(value) < min_length:
            errors.append(f"String is too short (minimum {min_length} characters)")
        if max_length is not None and len(value) > max_length:
            errors.append(f"String is too long (maximum {max_length} characters)")
        if pattern is not None and not re.search(pattern, value):
            errors.append(f"String does not match required pattern")
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid, errors=errors, warnings=[], field_errors={}
        )

    def validate_number(
        self,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> ValidationResult:
        """Validate numeric value."""
        errors: List[str] = []
        if not isinstance(value, (int, float)):
            return ValidationResult(
                is_valid=False,
                errors=["Value must be a number"],
                warnings=[],
                field_errors={"value": ["invalid_type"]},
            )
        if min_val is not None and value < min_val:
            errors.append(f"Value must be >= {min_val}")
        if max_val is not None and value > max_val:
            errors.append(f"Value must be <= {max_val}")
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid, errors=errors, warnings=[], field_errors={}
        )

    def validate_list(
        self,
        value: List,
        min_items: int = 0,
        max_items: Optional[int] = None,
        item_type: Optional[Type] = None,
    ) -> ValidationResult:
        """Validate list value."""
        errors: List[str] = []
        if not isinstance(value, list):
            return ValidationResult(
                is_valid=False,
                errors=["Value must be a list"],
                warnings=[],
                field_errors={"value": ["invalid_type"]},
            )
        if len(value) < min_items:
            errors.append(f"List must contain at least {min_items} items")
        if max_items is not None and len(value) > max_items:
            errors.append(f"List must contain at most {max_items} items")
        if item_type is not None:
            for i, item in enumerate(value):
                if not isinstance(item, item_type):
                    errors.append(
                        f"Item at index {i} must be of type {item_type.__name__}"
                    )
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid, errors=errors, warnings=[], field_errors={}
        )

    def validate_dict(
        self, value: Dict, required_keys: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate dictionary value."""
        errors: List[str] = []
        field_errors: Dict[str, List[str]] = {}
        if not isinstance(value, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Value must be a dictionary"],
                warnings=[],
                field_errors={"value": ["invalid_type"]},
            )
        if required_keys:
            for key in required_keys:
                if key not in value:
                    errors.append(f"Missing required key: {key}")
                    field_errors.setdefault(key, []).append("required")
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid, errors=errors, warnings=[], field_errors=field_errors
        )

    def validate_enum(self, value: Any, allowed_values: List[Any]) -> ValidationResult:
        """Validate value is in allowed values."""
        if value not in allowed_values:
            return ValidationResult(
                is_valid=False,
                errors=[
                    f"Value '{value}' must be one of: {', '.join(str(v) for v in allowed_values)}"
                ],
                warnings=[],
                field_errors={"value": ["invalid_enum"]},
            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL format."""
        if not isinstance(url, str) or not url:
            return ValidationResult(
                is_valid=False,
                errors=["URL must be a non-empty string"],
                warnings=[],
                field_errors={"url": ["invalid_type"]},
            )
        _url_re = re.compile(
            r"^(https?|ftp)://" r"(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)" r"$",
            re.IGNORECASE,
        )
        if not _url_re.match(url):
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid URL format: '{url}'"],
                warnings=[],
                field_errors={"url": ["invalid_format"]},
            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_email(self, email: str) -> ValidationResult:
        """Validate email format."""
        if not isinstance(email, str) or not email:
            return ValidationResult(
                is_valid=False,
                errors=["Email must be a non-empty string"],
                warnings=[],
                field_errors={"email": ["invalid_type"]},
            )
        _email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE)
        if not _email_re.match(email):
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid email format: '{email}'"],
                warnings=[],
                field_errors={"email": ["invalid_format"]},
            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    def validate_json(self, json_str: str) -> ValidationResult:
        """Validate JSON string."""
        if not isinstance(json_str, str):
            return ValidationResult(
                is_valid=False,
                errors=["JSON input must be a string"],
                warnings=[],
                field_errors={"json": ["invalid_type"]},
            )
        try:
            json.loads(json_str)
        except json.JSONDecodeError as exc:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON: {exc}"],
                warnings=[],
                field_errors={"json": ["parse_error"]},
            )
        return ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})

    # ==================== Business Rule Validation ====================

    def validate_budget_constraints(
        self, task: Dict[str, Any], budget: Dict[str, float]
    ) -> ValidationResult:
        """Validate task against budget constraints."""
        errors: List[str] = []
        warnings: List[str] = []
        field_errors: Dict[str, List[str]] = {}

        estimated_cost = task.get("estimated_cost", 0.0)
        total_budget = budget.get("total", 0.0)
        remaining_budget = budget.get("remaining", total_budget)

        if estimated_cost > remaining_budget:
            errors.append(
                f"Task estimated cost ({estimated_cost}) exceeds remaining budget ({remaining_budget})"
            )
            field_errors.setdefault("budget", []).append("insufficient")

        if total_budget > 0 and remaining_budget / total_budget < 0.1:
            warnings.append("Less than 10% of total budget remaining")

        token_limit = budget.get("token_limit")
        estimated_tokens = task.get("estimated_tokens")
        if token_limit is not None and estimated_tokens is not None:
            if estimated_tokens > token_limit:
                errors.append(
                    f"Estimated tokens ({estimated_tokens}) exceed token limit ({token_limit})"
                )
                field_errors.setdefault("tokens", []).append("limit_exceeded")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_errors=field_errors,
        )

    def validate_permissions(
        self, action: str, user_permissions: List[str]
    ) -> ValidationResult:
        """Validate action against permissions."""
        if not action:
            return ValidationResult(
                is_valid=False,
                errors=["Action cannot be empty"],
                warnings=[],
                field_errors={"action": ["empty"]},
            )
        # Support wildcard permission
        if "*" in user_permissions or action in user_permissions:
            return ValidationResult(
                is_valid=True, errors=[], warnings=[], field_errors={}
            )
        # Support namespace prefix matching (e.g. "agents:*" grants "agents:read")
        action_ns = action.split(":")[0]
        if f"{action_ns}:*" in user_permissions:
            return ValidationResult(
                is_valid=True, errors=[], warnings=[], field_errors={}
            )
        return ValidationResult(
            is_valid=False,
            errors=[f"Permission denied for action: '{action}'"],
            warnings=[],
            field_errors={"action": ["permission_denied"]},
        )

    def validate_rate_limits(
        self, request_count: int, limit: int, period: str
    ) -> ValidationResult:
        """Validate against rate limits."""
        warnings: List[str] = []
        if request_count > limit:
            return ValidationResult(
                is_valid=False,
                errors=[
                    f"Rate limit exceeded: {request_count} requests in {period} (limit {limit})"
                ],
                warnings=[],
                field_errors={"rate_limit": ["exceeded"]},
            )
        # Warn when approaching the limit (>= 80%)
        if limit > 0 and request_count / limit >= 0.8:
            warnings.append(
                f"Approaching rate limit: {request_count}/{limit} requests in {period}"
            )
        return ValidationResult(
            is_valid=True, errors=[], warnings=warnings, field_errors={}
        )

    # ==================== Rule Management ====================

    def add_rule(self, entity_type: str, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self._rules.setdefault(entity_type, []).append(rule)

    def remove_rule(self, entity_type: str, rule_name: str) -> bool:
        """Remove a validation rule."""
        rules = self._rules.get(entity_type, [])
        original_len = len(rules)
        self._rules[entity_type] = [r for r in rules if r.name != rule_name]
        return len(self._rules[entity_type]) < original_len

    def get_rules(self, entity_type: str) -> List[ValidationRule]:
        """Get validation rules for entity type."""
        return self._rules.get(entity_type, [])

    def clear_rules(self, entity_type: Optional[str] = None) -> None:
        """Clear validation rules."""
        if entity_type is None:
            self._rules.clear()
        else:
            self._rules.pop(entity_type, None)

    # ==================== Custom Validators ====================

    def register_validator(self, name: str, validator_func: Any) -> None:
        """Register a custom validator function."""
        if not callable(validator_func):
            raise ValueError(f"Validator '{name}' must be callable")
        self._custom_validators[name] = validator_func

    def unregister_validator(self, name: str) -> bool:
        """Unregister a custom validator."""
        if name in self._custom_validators:
            del self._custom_validators[name]
            return True
        return False

    def run_custom_validator(self, name: str, value: Any, **kwargs) -> ValidationResult:
        """Run a custom validator."""
        validator_func = self._custom_validators.get(name)
        if validator_func is None:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom validator '{name}' is not registered"],
                warnings=[],
                field_errors={"validator": ["not_found"]},
            )
        return validator_func(value, **kwargs)

    # ==================== Batch Validation ====================

    def validate_batch(
        self, items: List[Dict[str, Any]], validator_name: str
    ) -> List[ValidationResult]:
        """Validate a batch of items."""
        validator_func = self._custom_validators.get(validator_name)
        if validator_func is None:
            # Fall back to built-in task validation when no custom validator found
            if validator_name == "task":
                return [self.validate_task(item) for item in items]
            return [
                ValidationResult(
                    is_valid=False,
                    errors=[f"Validator '{validator_name}' is not registered"],
                    warnings=[],
                    field_errors={"validator": ["not_found"]},
                )
                for _ in items
            ]
        return [validator_func(item) for item in items]

    def validate_all(
        self, data: Dict[str, Any], rules: List[ValidationRule]
    ) -> ValidationResult:
        """Validate data against multiple rules."""
        all_errors: List[str] = []
        all_warnings: List[str] = []
        all_field_errors: Dict[str, List[str]] = {}

        for rule in rules:
            value = data.get(rule.field) if rule.field else data
            validator_func = self._custom_validators.get(rule.validator)
            if validator_func is None:
                continue
            result = validator_func(value, **rule.params)
            if not result.is_valid:
                if (
                    rule.level == ValidationLevel.STRICT
                    or self.level == ValidationLevel.STRICT
                ):
                    all_errors.append(rule.message)
                    if rule.field:
                        all_field_errors.setdefault(rule.field, []).append(rule.message)
                elif (
                    rule.level == ValidationLevel.LENIENT
                    or self.level == ValidationLevel.LENIENT
                ):
                    all_warnings.append(rule.message)
                else:
                    all_errors.append(rule.message)
                    if rule.field:
                        all_field_errors.setdefault(rule.field, []).append(rule.message)
            all_warnings.extend(result.warnings)

        is_valid = len(all_errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            field_errors=all_field_errors,
        )

    # ==================== Utilities ====================

    def set_level(self, level: ValidationLevel) -> None:
        """Set validation level."""
        self.level = level

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
