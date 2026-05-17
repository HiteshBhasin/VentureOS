# Central memory coordinator
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class MemoryType(Enum):
    """Types of memory storage."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


class MemoryTier(Enum):
    """Memory storage tiers."""

    CACHE = "cache"
    VECTOR = "vector"
    STRUCTURED = "structured"


@dataclass
class MemoryEntry:
    """Represents a memory entry."""

    key: str
    value: Any
    memory_type: MemoryType
    tier: MemoryTier
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None


class MemoryManager:
    """Central coordinator for all memory operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._cache_store = None
        self._vector_store = None
        self._structured_store = None
        self._audit_log = None

    # ==================== Initialization ====================

    def initialize(self) -> None:
        """Initialize all memory stores."""
        # Connect stores that are already attached but not yet active.
        pass

    def connect_cache_store(self, store: Any) -> None:
        """Connect cache store."""
        self._cache_store = store

    def connect_vector_store(self, store: Any) -> None:
        """Connect vector store."""
        self._vector_store = store

    def connect_structured_store(self, store: Any) -> None:
        """Connect structured store."""
        self._structured_store = store

    def connect_audit_log(self, log: Any) -> None:
        """Connect audit log."""
        self._audit_log = log

    def health_check(self) -> Dict[str, bool]:
        """Check health of all stores."""
        result = {
            "cache_store": self._cache_store is not None and getattr(self._cache_store, "is_connected", lambda: False)(),
            "vector_store": self._vector_store is not None and getattr(self._vector_store, "is_connected", lambda: False)(),
            "structured_store": self._structured_store is not None and getattr(self._structured_store, "is_connected", lambda: False)(),
            "audit_log": self._audit_log is not None,
        }
        return result

    # ==================== Store Operations ====================

    def store(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Store data in appropriate tier."""
        if memory_type in (MemoryType.SHORT_TERM, MemoryType.WORKING):
            return self.store_in_cache(key, value, ttl=ttl)
        if memory_type == MemoryType.SEMANTIC and self._vector_store:
            return self.store_in_vector(key, value)
        if memory_type in (MemoryType.LONG_TERM, MemoryType.EPISODIC):
            if self._structured_store:
                return self.store_in_structured("memory", {"key": key, "value": str(value), **(metadata or {})})
        # Fall back to cache
        return self.store_in_cache(key, value, ttl=ttl)

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data by key."""
        # Try cache first, then structured
        if self._cache_store:
            val = self._cache_store.get(key)
            if val is not None:
                return val
        if self._structured_store:
            row = self._structured_store.select_one("memory", {"key": key})
            if row:
                return row.get("value")
        return None

    def delete(self, key: str) -> bool:
        """Delete data by key."""
        deleted = False
        if self._cache_store:
            deleted = self._cache_store.delete(key) or deleted
        if self._vector_store:
            self._vector_store.delete([key])
            deleted = True
        if self._structured_store:
            count = self._structured_store.delete("memory", {"key": key})
            deleted = (count > 0) or deleted
        return deleted

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._cache_store and self._cache_store.exists(key):
            return True
        if self._structured_store:
            return self._structured_store.exists("memory", {"key": key})
        return False

    def update(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Update existing entry."""
        if self._cache_store and self._cache_store.exists(key):
            return self._cache_store.set(key, value)
        if self._structured_store:
            count = self._structured_store.update("memory", {"value": str(value)}, {"key": key})
            return count > 0
        return False

    def get_or_set(
        self, key: str, default_factory: Any, ttl: Optional[int] = None
    ) -> Any:
        """Get value or set default if not exists."""
        val = self.retrieve(key)
        if val is None:
            val = default_factory() if callable(default_factory) else default_factory
            self.store(key, val, ttl=ttl)
        return val

    # ==================== Tiered Operations ====================

    def store_in_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store in cache tier."""
        if self._cache_store:
            return self._cache_store.set(key, value, ttl=ttl)
        return False

    def store_in_vector(
        self, key: str, value: Any, embedding: Optional[List[float]] = None
    ) -> bool:
        """Store in vector tier with embedding."""
        if self._vector_store:
            vec = embedding or self._vector_store.get_embedding(str(value))
            return self._vector_store.upsert(key, vec, metadata={"value": str(value)})
        return False

    def store_in_structured(self, table: str, data: Dict[str, Any]) -> bool:
        """Store in structured tier."""
        if self._structured_store:
            return self._structured_store.insert(table, data) is not None
        return False

    def retrieve_from_cache(self, key: str) -> Optional[Any]:
        """Retrieve from cache tier."""
        return self._cache_store.get(key) if self._cache_store else None

    def retrieve_from_vector(self, key: str) -> Optional[Any]:
        """Retrieve from vector tier."""
        if self._vector_store:
            entries = self._vector_store.fetch([key])
            entry = entries.get(key)
            return entry.metadata.get("value") if entry else None
        return None

    def retrieve_from_structured(
        self, table: str, query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve from structured tier."""
        if self._structured_store:
            return self._structured_store.select(table, where=query)
        return []

    # ==================== Search Operations ====================

    def search(
        self, query: str, limit: int = 10, memory_type: Optional[MemoryType] = None
    ) -> List[MemoryEntry]:
        """Search across all tiers."""
        results = []
        if self._vector_store:
            for sr in self._vector_store.search_by_text(query, top_k=limit):
                results.append(MemoryEntry(
                    key=sr.id,
                    value=sr.metadata.get("value") if sr.metadata else None,
                    memory_type=memory_type or MemoryType.SEMANTIC,
                    tier=MemoryTier.VECTOR,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata=sr.metadata or {},
                    embedding=sr.vector,
                ))
        return results[:limit]

    def semantic_search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Perform semantic search using embeddings."""
        return self.search(query, limit=limit, memory_type=MemoryType.SEMANTIC)

    def search_by_metadata(
        self, metadata_filter: Dict[str, Any], limit: int = 10
    ) -> List[MemoryEntry]:
        """Search by metadata."""
        if self._vector_store:
            results = []
            for ns in self._vector_store.list_namespaces():
                for entry in list(self._vector_store._store.get(ns, {}).values()):
                    if all(entry.metadata.get(k) == v for k, v in metadata_filter.items()):
                        results.append(MemoryEntry(
                            key=entry.id,
                            value=entry.metadata.get("value"),
                            memory_type=MemoryType.SEMANTIC,
                            tier=MemoryTier.VECTOR,
                            created_at=entry.created_at,
                            updated_at=entry.created_at,
                            metadata=entry.metadata,
                        ))
                        if len(results) >= limit:
                            return results
        return []

    def search_by_time_range(self, start: datetime, end: datetime) -> List[MemoryEntry]:
        """Search by time range."""
        if self._vector_store:
            results = []
            for ns in self._vector_store.list_namespaces():
                for entry in self._vector_store._store.get(ns, {}).values():
                    if start <= entry.created_at <= end:
                        results.append(MemoryEntry(
                            key=entry.id,
                            value=entry.metadata.get("value"),
                            memory_type=MemoryType.SEMANTIC,
                            tier=MemoryTier.VECTOR,
                            created_at=entry.created_at,
                            updated_at=entry.created_at,
                            metadata=entry.metadata,
                        ))
            return results
        return []

    def find_similar(
        self, embedding: List[float], limit: int = 10
    ) -> List[MemoryEntry]:
        """Find similar entries by embedding."""
        if self._vector_store:
            results = self._vector_store.search(embedding, top_k=limit)
            return [
                MemoryEntry(
                    key=sr.id,
                    value=sr.metadata.get("value") if sr.metadata else None,
                    memory_type=MemoryType.SEMANTIC,
                    tier=MemoryTier.VECTOR,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata=sr.metadata or {},
                    embedding=sr.vector,
                )
                for sr in results
            ]
        return []

    # ==================== Context Management ====================

    def store_context(self, agent_id: str, context: Dict[str, Any]) -> bool:
        """Store agent context."""
        return self.store_in_cache(f"ctx:{agent_id}", context)

    def retrieve_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent context."""
        return self.retrieve_from_cache(f"ctx:{agent_id}")

    def update_context(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent context."""
        ctx = self.retrieve_context(agent_id) or {}
        ctx.update(updates)
        return self.store_context(agent_id, ctx)

    def clear_context(self, agent_id: str) -> bool:
        """Clear agent context."""
        return self.delete(f"ctx:{agent_id}")

    # ==================== History Management ====================

    def store_history(self, agent_id: str, entry: Dict[str, Any]) -> bool:
        """Store history entry."""
        hist = self.get_history(agent_id)
        hist.append(entry)
        return self.store_in_cache(f"hist:{agent_id}", hist)

    def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get agent history."""
        hist = self.retrieve_from_cache(f"hist:{agent_id}") or []
        return hist[-limit:]

    def clear_history(self, agent_id: str) -> bool:
        """Clear agent history."""
        return self.delete(f"hist:{agent_id}")

    def search_history(self, agent_id: str, query: str) -> List[Dict[str, Any]]:
        """Search agent history."""
        q = query.lower()
        return [
            h for h in self.get_history(agent_id)
            if q in str(h).lower()
        ]

    # ==================== Batch Operations ====================

    def store_batch(self, entries: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Store multiple entries."""
        return {
            e["key"]: self.store(
                e["key"], e["value"],
                memory_type=e.get("memory_type", MemoryType.SHORT_TERM),
                ttl=e.get("ttl"),
                metadata=e.get("metadata"),
            )
            for e in entries
        }

    def retrieve_batch(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple entries."""
        return {k: self.retrieve(k) for k in keys}

    def delete_batch(self, keys: List[str]) -> Dict[str, bool]:
        """Delete multiple entries."""
        return {k: self.delete(k) for k in keys}

    # ==================== Memory Management ====================

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats: Dict[str, Any] = {}
        if self._cache_store:
            stats["cache"] = self._cache_store.get_stats() if hasattr(self._cache_store, "get_stats") else {}
        if self._vector_store:
            stats["vector"] = self._vector_store.get_stats() if hasattr(self._vector_store, "get_stats") else {}
        if self._structured_store:
            stats["structured"] = self._structured_store.get_stats() if hasattr(self._structured_store, "get_stats") else {}
        return stats

    def get_tier_stats(self, tier: MemoryTier) -> Dict[str, Any]:
        """Get tier-specific statistics."""
        if tier == MemoryTier.CACHE and self._cache_store:
            return self._cache_store.get_stats() if hasattr(self._cache_store, "get_stats") else {}
        if tier == MemoryTier.VECTOR and self._vector_store:
            return self._vector_store.get_stats() if hasattr(self._vector_store, "get_stats") else {}
        if tier == MemoryTier.STRUCTURED and self._structured_store:
            return self._structured_store.get_stats() if hasattr(self._structured_store, "get_stats") else {}
        return {}

    def cleanup_expired(self) -> int:
        """Cleanup expired entries. Returns count removed."""
        if self._cache_store and hasattr(self._cache_store, "_local_cache"):
            expired = [
                k for k, e in list(self._cache_store._local_cache.items())
                if hasattr(e, "expires_at") and e.expires_at and datetime.utcnow() > e.expires_at
            ]
            for k in expired:
                del self._cache_store._local_cache[k]
            return len(expired)
        return 0

    def compact(self) -> None:
        """Compact memory stores."""
        self.cleanup_expired()

    def flush(self) -> None:
        """Flush all caches."""
        if self._cache_store and hasattr(self._cache_store, "flush"):
            self._cache_store.flush()

    # ==================== Shutdown ====================

    def close(self) -> None:
        """Close all connections."""
        self.close_cache_store()
        self.close_vector_store()
        self.close_structured_store()

    def close_cache_store(self) -> None:
        """Close cache store connection."""
        if self._cache_store and hasattr(self._cache_store, "disconnect"):
            self._cache_store.disconnect()

    def close_vector_store(self) -> None:
        """Close vector store connection."""
        if self._vector_store and hasattr(self._vector_store, "disconnect"):
            self._vector_store.disconnect()

    def close_structured_store(self) -> None:
        """Close structured store connection."""
        if self._structured_store and hasattr(self._structured_store, "disconnect"):
            self._structured_store.disconnect()
