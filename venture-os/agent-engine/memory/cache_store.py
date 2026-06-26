# Fast cache (Redis)
import fnmatch
import json
import os
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

try:
    import redis as _redis_lib

    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False


@dataclass
class CacheEntry:
    """Represents a cache entry."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hits: int = 0


class CacheStore:
    """Redis-based fast caching layer."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._client = None
        self._connected = False
        self._local_cache: Dict[str, CacheEntry] = {}

    # ==================== Connection Management ====================

    def connect(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ) -> bool:
        """Connect to Redis server."""
        # No REDIS_URL/REDIS_HOST configured — skip the network attempt entirely
        # and go straight to the in-memory fallback (avoids an OS-level connect
        # timeout on every Orchestrator instantiation when Redis isn't deployed).
        if _HAS_REDIS and (os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")):
            try:
                self._client = _redis_lib.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=False,
                    socket_connect_timeout=1,
                    retry_on_timeout=False,
                    retry=_redis_lib.retry.Retry(_redis_lib.backoff.NoBackoff(), 0),
                )
                self._client.ping()
                self._connected = True
                return True
            except Exception:
                self._client = None
        # Fall back to in-memory
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected

    def ping(self) -> bool:
        """Ping Redis server."""
        if self._client:
            try:
                return bool(self._client.ping())
            except Exception:
                return False
        return self._connected

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "connected": self._connected,
            "backend": "redis" if self._client else "in-memory",
            "local_cache_size": len(self._local_cache),
        }

    # ==================== Basic Operations ====================

    def _serialize(self, value: Any) -> bytes:
        return json.dumps(value, default=str).encode()

    def _deserialize(self, data: bytes) -> Any:
        if data is None:
            return None
        try:
            return json.loads(data.decode())
        except Exception:
            return data

    def _is_expired(self, entry: CacheEntry) -> bool:
        return entry.expires_at is not None and datetime.now(timezone.utc) > entry.expires_at

    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        if self._client:
            try:
                data = self._client.get(key)
                byte_data = data if isinstance(data, bytes) else None
                return self._deserialize(byte_data) if byte_data is not None else None
            except Exception:
                pass
        entry = self._local_cache.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            del self._local_cache[key]
            return None
        entry.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set key-value pair."""
        if self._client:
            try:
                data = self._serialize(value)
                if ttl:
                    self._client.setex(key, ttl, data)
                else:
                    self._client.set(key, data)
                return True
            except Exception:
                pass
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl) if ttl else None
        self._local_cache[key] = CacheEntry(
            key=key, value=value, created_at=datetime.now(timezone.utc), expires_at=expires_at
        )
        return True

    def delete(self, key: str) -> bool:
        """Delete key."""
        deleted = False
        if self._client:
            try:
                deleted = bool(self._client.delete(key))
            except Exception:
                pass
        if key in self._local_cache:
            del self._local_cache[key]
            deleted = True
        return deleted

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._client:
            try:
                return bool(self._client.exists(key))
            except Exception:
                pass
        entry = self._local_cache.get(key)
        if entry is None:
            return False
        if self._is_expired(entry):
            del self._local_cache[key]
            return False
        return True

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if self._client:
            try:
                return bool(self._client.expire(key, seconds))
            except Exception:
                pass
        entry = self._local_cache.get(key)
        if entry:
            entry.expires_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            return True
        return False

    def ttl(self, key: str) -> int:
        """Get time-to-live for key."""
        if self._client:
            try:
                return int(self._client.ttl(key))
            except Exception:
                pass
        entry = self._local_cache.get(key)
        if entry is None or entry.expires_at is None:
            return -1
        remaining = (entry.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    def persist(self, key: str) -> bool:
        """Remove expiration from key."""
        if self._client:
            try:
                return bool(self._client.persist(key))
            except Exception:
                pass
        entry = self._local_cache.get(key)
        if entry:
            entry.expires_at = None
            return True
        return False

    # ==================== Batch Operations ====================

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys."""
        return {k: self.get(k) for k in keys}

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs."""
        for k, v in mapping.items():
            self.set(k, v, ttl=ttl)
        return True

    def mdelete(self, keys: List[str]) -> int:
        """Delete multiple keys. Returns count deleted."""
        return sum(1 for k in keys if self.delete(k))

    # ==================== Atomic Operations ====================

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment value."""
        if self._client:
            try:
                return int(self._client.incr(key, amount))
            except Exception:
                pass
        current = int(self.get(key) or 0)
        new_val = current + amount
        self.set(key, new_val)
        return new_val

    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement value."""
        return self.incr(key, -amount)

    def getset(self, key: str, value: Any) -> Optional[Any]:
        """Get old value and set new value."""
        old = self.get(key)
        self.set(key, value)
        return old

    def setnx(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set if not exists."""
        if self.exists(key):
            return False
        return self.set(key, value, ttl=ttl)

    # ==================== Hash Operations ====================
    # Hash operations use a nested dict in the local cache.

    def _hash_key(self, name: str) -> str:
        return f"__hash__{name}"

    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field."""
        if self._client:
            try:
                data = self._client.hget(name, key)
                return self._deserialize(data) if data is not None else None
            except Exception:
                pass
        h = self.get(self._hash_key(name)) or {}
        return h.get(key)

    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field."""
        if self._client:
            try:
                self._client.hset(name, key, self._serialize(value))
                return True
            except Exception:
                pass
        h = self.get(self._hash_key(name)) or {}
        h[key] = value
        self.set(self._hash_key(name), h)
        return True

    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if self._client:
            try:
                raw = self._client.hgetall(name)
                return {k.decode(): self._deserialize(v) for k, v in raw.items()}
            except Exception:
                pass
        return self.get(self._hash_key(name)) or {}

    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        if self._client:
            try:
                return int(self._client.hdel(name, *keys))
            except Exception:
                pass
        h = self.get(self._hash_key(name)) or {}
        count = sum(1 for k in keys if k in h)
        for k in keys:
            h.pop(k, None)
        self.set(self._hash_key(name), h)
        return count

    def hexists(self, name: str, key: str) -> bool:
        """Check if hash field exists."""
        return self.hget(name, key) is not None

    def hkeys(self, name: str) -> List[str]:
        """Get all hash keys."""
        return list(self.hgetall(name).keys())

    # ==================== List Operations ====================

    def _list_key(self, key: str) -> str:
        return f"__list__{key}"

    def lpush(self, key: str, *values: Any) -> int:
        """Push to left of list."""
        if self._client:
            try:
                return int(
                    self._client.lpush(key, *[self._serialize(v) for v in values])
                )
            except Exception:
                pass
        lst = self.get(self._list_key(key)) or []
        for v in values:
            lst.insert(0, v)
        self.set(self._list_key(key), lst)
        return len(lst)

    def rpush(self, key: str, *values: Any) -> int:
        """Push to right of list."""
        if self._client:
            try:
                return int(
                    self._client.rpush(key, *[self._serialize(v) for v in values])
                )
            except Exception:
                pass
        lst = self.get(self._list_key(key)) or []
        lst.extend(values)
        self.set(self._list_key(key), lst)
        return len(lst)

    def lpop(self, key: str) -> Optional[Any]:
        """Pop from left of list."""
        if self._client:
            try:
                data = self._client.lpop(key)
                return self._deserialize(data) if data is not None else None
            except Exception:
                pass
        lst = self.get(self._list_key(key)) or []
        if not lst:
            return None
        val = lst.pop(0)
        self.set(self._list_key(key), lst)
        return val

    def rpop(self, key: str) -> Optional[Any]:
        """Pop from right of list."""
        if self._client:
            try:
                data = self._client.rpop(key)
                return self._deserialize(data) if data is not None else None
            except Exception:
                pass
        lst = self.get(self._list_key(key)) or []
        if not lst:
            return None
        val = lst.pop()
        self.set(self._list_key(key), lst)
        return val

    def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get list range."""
        if self._client:
            try:
                raw = self._client.lrange(key, start, end)
                return [self._deserialize(v) for v in raw]
            except Exception:
                pass
        lst = self.get(self._list_key(key)) or []
        return lst[start : end + 1 if end != -1 else None]

    def llen(self, key: str) -> int:
        """Get list length."""
        if self._client:
            try:
                return int(self._client.llen(key))
            except Exception:
                pass
        return len(self.get(self._list_key(key)) or [])

    # ==================== Set Operations ====================

    def _set_key(self, key: str) -> str:
        return f"__set__{key}"

    def sadd(self, key: str, *values: Any) -> int:
        """Add to set."""
        if self._client:
            try:
                return int(
                    self._client.sadd(key, *[self._serialize(v) for v in values])
                )
            except Exception:
                pass
        s = set(self.get(self._set_key(key)) or [])
        before = len(s)
        s.update(values)
        self.set(self._set_key(key), list(s))
        return len(s) - before

    def srem(self, key: str, *values: Any) -> int:
        """Remove from set."""
        if self._client:
            try:
                return int(
                    self._client.srem(key, *[self._serialize(v) for v in values])
                )
            except Exception:
                pass
        s = set(self.get(self._set_key(key)) or [])
        before = len(s)
        s.difference_update(values)
        self.set(self._set_key(key), list(s))
        return before - len(s)

    def smembers(self, key: str) -> set:
        """Get all set members."""
        if self._client:
            try:
                raw = self._client.smembers(key)
                return {self._deserialize(v) for v in raw}
            except Exception:
                pass
        return set(self.get(self._set_key(key)) or [])

    def sismember(self, key: str, value: Any) -> bool:
        """Check if value is in set."""
        return value in self.smembers(key)

    def scard(self, key: str) -> int:
        """Get set cardinality."""
        return len(self.smembers(key))

    # ==================== Key Management ====================

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if self._client:
            try:
                return [k.decode() for k in self._client.keys(pattern)]
            except Exception:
                pass
        all_keys = list(self._local_cache.keys())
        if pattern == "*":
            return all_keys
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def scan(self, cursor: int = 0, pattern: str = "*", count: int = 100) -> tuple:
        """Scan keys incrementally."""
        if self._client:
            try:
                return self._client.scan(cursor=cursor, match=pattern, count=count)
            except Exception:
                pass
        matched = self.keys(pattern)
        chunk = matched[cursor : cursor + count]
        next_cursor = cursor + count if cursor + count < len(matched) else 0
        return next_cursor, chunk

    def rename(self, old_key: str, new_key: str) -> bool:
        """Rename a key."""
        val = self.get(old_key)
        if val is None:
            return False
        self.set(new_key, val)
        self.delete(old_key)
        return True

    def type(self, key: str) -> str:
        """Get key type."""
        val = self.get(key)
        if val is None:
            return "none"
        return type(val).__name__

    # ==================== Utility ====================

    def flush(self) -> None:
        """Flush all keys."""
        self._local_cache.clear()
        if self._client:
            try:
                self._client.flushdb()
            except Exception:
                pass

    def flush_db(self) -> None:
        """Flush current database."""
        self.flush()

    def info(self) -> Dict[str, Any]:
        """Get Redis info."""
        if self._client:
            try:
                return dict(self._client.info())
            except Exception:
                pass
        return {"backend": "in-memory", "keys": len(self._local_cache)}

    def dbsize(self) -> int:
        """Get number of keys."""
        if self._client:
            try:
                return int(self._client.dbsize())
            except Exception:
                pass
        return len(self._local_cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._local_cache)
        hits = sum(e.hits for e in self._local_cache.values())
        expired = sum(1 for e in self._local_cache.values() if self._is_expired(e))
        return {
            "total_keys": total,
            "total_hits": hits,
            "expired_keys": expired,
            "backend": "redis" if self._client else "in-memory",
            "connected": self._connected,
        }
