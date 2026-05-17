# Memory audit trail
import csv
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class AuditAction(Enum):
    """Types of auditable actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    ERROR = "error"


class AuditLevel(Enum):
    """Audit log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Represents an audit log entry."""

    id: str
    timestamp: datetime
    action: AuditAction
    level: AuditLevel
    actor: str
    resource: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLog:
    """Persistent audit trail for all operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._storage = None
        self._buffer: List[AuditEntry] = []
        self._buffer_size: int = 100

    # ==================== Connection ====================

    def initialize(self, storage_backend: str = "postgresql") -> bool:
        """Initialize audit log storage."""
        # In-memory storage is always available; external backends are optional
        self._storage_backend = storage_backend
        self._initialized = True
        return True

    def close(self) -> None:
        """Close audit log and flush buffer."""
        self.flush()
        self._initialized = False

    def is_initialized(self) -> bool:
        """Check if audit log is initialized."""
        return getattr(self, "_initialized", False)

    # ==================== Logging Operations ====================

    def log(
        self,
        action: AuditAction,
        actor: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        level: AuditLevel = AuditLevel.INFO,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Log an audit entry. Returns entry ID."""
        entry = AuditEntry(
            id=uuid.uuid4().hex,
            timestamp=datetime.utcnow(),
            action=action,
            level=level,
            actor=actor,
            resource=resource,
            resource_id=resource_id,
            details=details or {},
            correlation_id=correlation_id,
        )
        self._buffer.append(entry)
        if len(self._buffer) >= self._buffer_size:
            self.flush()
        return entry.id

    def log_create(
        self,
        actor: str,
        resource: str,
        resource_id: str,
        details: Optional[Dict] = None,
    ) -> str:
        """Log a create action."""
        return self.log(AuditAction.CREATE, actor, resource, resource_id, details)

    def log_read(
        self,
        actor: str,
        resource: str,
        resource_id: str,
        details: Optional[Dict] = None,
    ) -> str:
        """Log a read action."""
        return self.log(AuditAction.READ, actor, resource, resource_id, details)

    def log_update(
        self, actor: str, resource: str, resource_id: str, changes: Dict[str, Any]
    ) -> str:
        """Log an update action with changes."""
        return self.log(AuditAction.UPDATE, actor, resource, resource_id, {"changes": changes})

    def log_delete(
        self,
        actor: str,
        resource: str,
        resource_id: str,
        details: Optional[Dict] = None,
    ) -> str:
        """Log a delete action."""
        return self.log(AuditAction.DELETE, actor, resource, resource_id, details)

    def log_error(
        self, actor: str, resource: str, error: str, details: Optional[Dict] = None
    ) -> str:
        """Log an error."""
        d = {"error": error, **(details or {})}
        return self.log(AuditAction.ERROR, actor, resource, level=AuditLevel.ERROR, details=d)

    def log_execution(
        self,
        actor: str,
        resource: str,
        duration_ms: float,
        success: bool,
        details: Optional[Dict] = None,
    ) -> str:
        """Log an execution event."""
        d = {"duration_ms": duration_ms, "success": success, **(details or {})}
        level = AuditLevel.INFO if success else AuditLevel.ERROR
        entry_id = self.log(AuditAction.EXECUTE, actor, resource, level=level, details=d)
        # Patch duration_ms on the buffered entry
        for e in reversed(self._buffer):
            if e.id == entry_id:
                e.duration_ms = duration_ms
                e.success = success
                break
        return entry_id

    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        all_entries = self._storage if self._storage else self._buffer
        for e in all_entries:
            if e.id == entry_id:
                return e
        return None

    def _all_entries(self) -> List[AuditEntry]:
        base = list(self._storage) if self._storage else []
        return base + self._buffer

    def get_entries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Get audit entries with optional filters."""
        entries = self._all_entries()
        if filters:
            for k, v in filters.items():
                if k == "action":
                    entries = [e for e in entries if e.action == v]
                elif k == "level":
                    entries = [e for e in entries if e.level == v]
                elif k == "actor":
                    entries = [e for e in entries if e.actor == v]
                elif k == "resource":
                    entries = [e for e in entries if e.resource == v]
                elif k == "success":
                    entries = [e for e in entries if e.success == v]
        return entries[offset: offset + limit]

    def get_by_actor(self, actor: str, limit: int = 100) -> List[AuditEntry]:
        """Get entries by actor."""
        return [e for e in self._all_entries() if e.actor == actor][-limit:]

    def get_by_resource(
        self, resource: str, resource_id: Optional[str] = None, limit: int = 100
    ) -> List[AuditEntry]:
        """Get entries by resource."""
        entries = [e for e in self._all_entries() if e.resource == resource]
        if resource_id:
            entries = [e for e in entries if e.resource_id == resource_id]
        return entries[-limit:]

    def get_by_action(self, action: AuditAction, limit: int = 100) -> List[AuditEntry]:
        """Get entries by action type."""
        return [e for e in self._all_entries() if e.action == action][-limit:]

    def get_by_time_range(
        self, start: datetime, end: datetime, limit: int = 100
    ) -> List[AuditEntry]:
        """Get entries within time range."""
        return [
            e for e in self._all_entries() if start <= e.timestamp <= end
        ][-limit:]

    def get_by_correlation_id(self, correlation_id: str) -> List[AuditEntry]:
        """Get entries by correlation ID."""
        return [e for e in self._all_entries() if e.correlation_id == correlation_id]

    def get_errors(self, limit: int = 100) -> List[AuditEntry]:
        """Get error entries."""
        return [
            e for e in self._all_entries() if e.level in (AuditLevel.ERROR, AuditLevel.CRITICAL)
        ][-limit:]

    # ==================== Search Operations ====================

    def search(self, query: str, limit: int = 100) -> List[AuditEntry]:
        """Full-text search audit entries."""
        q = query.lower()
        return [
            e for e in self._all_entries()
            if q in e.actor.lower()
            or q in e.resource.lower()
            or q in json.dumps(e.details).lower()
        ][-limit:]

    def search_details(
        self, key: str, value: Any, limit: int = 100
    ) -> List[AuditEntry]:
        """Search by details field."""
        return [
            e for e in self._all_entries() if e.details.get(key) == value
        ][-limit:]

    # ==================== Statistics ====================

    def get_stats(
        self, time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get audit statistics."""
        entries = self._all_entries()
        if time_range:
            start, end = time_range
            entries = [e for e in entries if start <= e.timestamp <= end]
        total = len(entries)
        errors = sum(1 for e in entries if e.level in (AuditLevel.ERROR, AuditLevel.CRITICAL))
        return {
            "total_entries": total,
            "error_count": errors,
            "error_rate": errors / total if total else 0.0,
            "action_counts": {a.value: sum(1 for e in entries if e.action == a) for a in AuditAction},
            "actor_counts": {e.actor: 0 for e in entries},
        }

    def get_action_counts(self) -> Dict[AuditAction, int]:
        """Get counts by action type."""
        result: Dict[AuditAction, int] = {a: 0 for a in AuditAction}
        for e in self._all_entries():
            result[e.action] = result.get(e.action, 0) + 1
        return result

    def get_actor_activity(self, actor: str) -> Dict[str, Any]:
        """Get activity summary for actor."""
        entries = self.get_by_actor(actor, limit=10000)
        return {
            "actor": actor,
            "total_actions": len(entries),
            "action_counts": {a.value: sum(1 for e in entries if e.action == a) for a in AuditAction},
            "error_count": sum(1 for e in entries if e.level == AuditLevel.ERROR),
            "last_activity": entries[-1].timestamp.isoformat() if entries else None,
        }

    def get_resource_activity(self, resource: str) -> Dict[str, Any]:
        """Get activity summary for resource."""
        entries = self.get_by_resource(resource, limit=10000)
        return {
            "resource": resource,
            "total_actions": len(entries),
            "action_counts": {a.value: sum(1 for e in entries if e.action == a) for a in AuditAction},
            "last_activity": entries[-1].timestamp.isoformat() if entries else None,
        }

    def get_error_rate(
        self, time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> float:
        """Get error rate."""
        stats = self.get_stats(time_range)
        return stats["error_rate"]

    # ==================== Buffer Management ====================

    def flush(self) -> int:
        """Flush buffer to storage. Returns count flushed."""
        count = len(self._buffer)
        if self._storage is not None:
            self._storage.extend(self._buffer)
        else:
            self._storage = list(self._buffer)
        self._buffer.clear()
        return count

    def set_buffer_size(self, size: int) -> None:
        """Set buffer size."""
        self._buffer_size = size

    def get_buffer_count(self) -> int:
        """Get number of entries in buffer."""
        return len(self._buffer)

    # ==================== Retention ====================

    def purge_old_entries(self, older_than_days: int) -> int:
        """Purge entries older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        before = len(self._all_entries())
        if self._storage:
            self._storage = [e for e in self._storage if e.timestamp >= cutoff]
        self._buffer = [e for e in self._buffer if e.timestamp >= cutoff]
        return before - len(self._all_entries())

    def archive_entries(self, older_than_days: int, archive_path: str) -> int:
        """Archive old entries to file."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        to_archive = [e for e in self._all_entries() if e.timestamp < cutoff]
        if to_archive:
            self.export_to_file(archive_path, format="json", filters={"_before": cutoff})
        return len(to_archive)

    def set_retention_policy(self, days: int) -> None:
        """Set retention policy."""
        self._retention_days = days

    # ==================== Export ====================

    def export_to_file(
        self, filepath: str, format: str = "json", filters: Optional[Dict] = None
    ) -> int:
        """Export entries to file."""
        entries = self.get_entries(filters=filters, limit=10_000_000)
        data = [
            {
                **{k: v.value if hasattr(v, "value") else v for k, v in asdict(e).items()},
            }
            for e in entries
        ]
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return len(data)

    def export_to_csv(self, filepath: str, filters: Optional[Dict] = None) -> int:
        """Export entries to CSV."""
        entries = self.get_entries(filters=filters, limit=10_000_000)
        if not entries:
            return 0
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(asdict(entries[0]).keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in entries:
                row = {k: v.value if hasattr(v, "value") else v for k, v in asdict(e).items()}
                writer.writerow(row)
        return len(entries)
