# Common utility functions
from typing import Any, Dict, List, Optional, TypeVar
from datetime import datetime
import hashlib
import uuid


T = TypeVar("T")


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier.

    Args:
        prefix: Optional prefix for the ID.

    Returns:
        Unique identifier string.
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def generate_hash(content: str) -> str:
    """Generate a hash from content.

    Args:
        content: String content to hash.

    Returns:
        Hash string.
    """
    return hashlib.sha256(content.encode()).hexdigest()
    pass


def timestamp_now() -> str:
    """Get current timestamp in ISO format.

    Returns:
        ISO formatted timestamp string.
    """
    return datetime.utcnow().isoformat() + "Z"


def parse_timestamp(timestamp: str) -> datetime:
    """Parse an ISO timestamp string.

    Args:
        timestamp: ISO formatted timestamp string.

    Returns:
        Datetime object.
    """
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary.
        override: Dictionary with override values.

    Returns:
        Merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten.
        parent_key: Parent key prefix.
        sep: Separator for nested keys.

    Returns:
        Flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks.

    Args:
        lst: List to chunk.
        chunk_size: Size of each chunk.

    Returns:
        List of chunks.
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to max length.

    Args:
        s: String to truncate.
        max_length: Maximum length.
        suffix: Suffix to add when truncated.

    Returns:
        Truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def safe_get(d: Dict, *keys, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        d: Dictionary to get value from.
        *keys: Chain of keys to traverse.
        default: Default value if key not found.

    Returns:
        Retrieved value or default.
    """
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def sanitize_string(s: str) -> str:
    """Sanitize a string for safe use.

    Args:
        s: String to sanitize.

    Returns:
        Sanitized string.
    """
    return s.replace("\n", " ").replace("\r", " ").strip()


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in text.

    Args:
        text: Text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    # Simple heuristic: 1 token ~ 4 characters
    return len(text) // 4


def format_bytes(num_bytes: float) -> str:
    """Format bytes into human readable string.

    Args:
        num_bytes: Number of bytes.

    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    prefixes = ["B", "KB", "MB", "GB", "TB"]
    for i, prefix in enumerate(prefixes):
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {prefix}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string (e.g., "2m 30s").
    """
    prefixes = [("h", 3600), ("m", 60), ("s", 1)]
    result = []
    for suffix, divisor in prefixes:
        if seconds >= divisor:
            value = int(seconds // divisor)
            result.append(f"{value}{suffix}")
            seconds -= value * divisor
    return " ".join(result) if result else "0s"
