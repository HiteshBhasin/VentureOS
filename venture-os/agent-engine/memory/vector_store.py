# Vector embeddings (Pinecone/Weaviate)
import fnmatch
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


@dataclass
class VectorEntry:
    """Represents a vector entry."""

    id: str
    vector: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    namespace: str = "default"


@dataclass
class SearchResult:
    """Search result with score."""

    id: str
    score: float
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class VectorStore:
    """Vector embedding storage and similarity search."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._client = None
        self._connected = False
        self._dimension: int = 1536  # Default OpenAI embedding dimension
        self._index_name: str = "default"
        # In-memory store: namespace -> {id: VectorEntry}
        self._store: Dict[str, Dict[str, VectorEntry]] = {"default": {}}
        self._indexes: Dict[str, Dict[str, Any]] = {}
        self._embedding_model: Optional[str] = None

    # ==================== Connection Management ====================

    def connect(self, provider: str = "pinecone", **kwargs) -> bool:
        """Connect to vector store provider."""
        # External providers optional; fall back to in-memory store
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from vector store."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "connected": self._connected,
            "backend": "in-memory",
            "current_index": self._index_name,
            "namespaces": list(self._store.keys()),
        }

    # ==================== Index Management ====================

    def create_index(self, name: str, dimension: int, metric: str = "cosine") -> bool:
        """Create a new index."""
        self._indexes[name] = {"name": name, "dimension": dimension, "metric": metric}
        self._store.setdefault("default", {})
        return True

    def delete_index(self, name: str) -> bool:
        """Delete an index."""
        self._indexes.pop(name, None)
        return True

    def list_indexes(self) -> List[str]:
        """List all indexes."""
        return list(self._indexes.keys())

    def describe_index(self, name: str) -> Dict[str, Any]:
        """Get index description."""
        return self._indexes.get(name, {})

    def set_index(self, name: str) -> None:
        """Set current working index."""
        self._index_name = name

    def get_index_stats(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get index statistics."""
        ns_total = sum(len(v) for v in self._store.values())
        return {
            "index": name or self._index_name,
            "total_vectors": ns_total,
            "namespaces": {ns: len(vecs) for ns, vecs in self._store.items()},
        }

    # ==================== Vector Operations ====================

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if _HAS_NUMPY:
            va = np.array(a, dtype=float)
            vb = np.array(b, dtype=float)
            denom = np.linalg.norm(va) * np.linalg.norm(vb)
            return float(np.dot(va, vb) / denom) if denom > 0 else 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict] = None,
        namespace: str = "default",
    ) -> bool:
        """Insert or update a vector."""
        self._store.setdefault(namespace, {})
        self._store[namespace][id] = VectorEntry(
            id=id, vector=vector, metadata=metadata or {},
            created_at=datetime.utcnow(), namespace=namespace,
        )
        return True

    def upsert_batch(
        self,
        vectors: List[Tuple[str, List[float], Optional[Dict]]],
        namespace: str = "default",
    ) -> Dict[str, bool]:
        """Insert or update multiple vectors."""
        return {vid: self.upsert(vid, vec, meta, namespace) for vid, vec, meta in vectors}

    def fetch(
        self, ids: List[str], namespace: str = "default"
    ) -> Dict[str, VectorEntry]:
        """Fetch vectors by IDs."""
        ns = self._store.get(namespace, {})
        return {vid: ns[vid] for vid in ids if vid in ns}

    def delete(self, ids: List[str], namespace: str = "default") -> bool:
        """Delete vectors by IDs."""
        ns = self._store.get(namespace, {})
        for vid in ids:
            ns.pop(vid, None)
        return True

    def delete_by_metadata(
        self, filter: Dict[str, Any], namespace: str = "default"
    ) -> int:
        """Delete vectors by metadata filter."""
        ns = self._store.get(namespace, {})
        to_delete = [
            vid for vid, entry in ns.items()
            if all(entry.metadata.get(k) == v for k, v in filter.items())
        ]
        for vid in to_delete:
            del ns[vid]
        return len(to_delete)

    def update_metadata(
        self, id: str, metadata: Dict[str, Any], namespace: str = "default"
    ) -> bool:
        """Update vector metadata."""
        entry = self._store.get(namespace, {}).get(id)
        if entry is None:
            return False
        entry.metadata.update(metadata)
        return True

    # ==================== Search Operations ====================

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: str = "default",
        filter: Optional[Dict] = None,
        include_metadata: bool = True,
        include_vectors: bool = False,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        ns = self._store.get(namespace, {})
        candidates = [
            entry for entry in ns.values()
            if filter is None or all(entry.metadata.get(k) == v for k, v in filter.items())
        ]
        scored = [
            (entry, self._cosine_similarity(query_vector, entry.vector))
            for entry in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for entry, score in scored[:top_k]:
            results.append(SearchResult(
                id=entry.id,
                score=score,
                vector=entry.vector if include_vectors else None,
                metadata=entry.metadata if include_metadata else None,
            ))
        return results

    def search_by_id(
        self, id: str, top_k: int = 10, namespace: str = "default"
    ) -> List[SearchResult]:
        """Search for vectors similar to existing vector."""
        entry = self._store.get(namespace, {}).get(id)
        if entry is None:
            return []
        return self.search(entry.vector, top_k=top_k + 1, namespace=namespace)

    def hybrid_search(
        self,
        query_vector: List[float],
        sparse_vector: Dict[str, Any],
        top_k: int = 10,
        alpha: float = 0.5,
        namespace: str = "default",
    ) -> List[SearchResult]:
        """Hybrid dense + sparse search."""
        # Without a sparse index, return dense results only
        return self.search(query_vector, top_k=top_k, namespace=namespace)

    def search_with_score_threshold(
        self,
        query_vector: List[float],
        threshold: float,
        max_results: int = 100,
        namespace: str = "default",
    ) -> List[SearchResult]:
        """Search with minimum score threshold."""
        results = self.search(query_vector, top_k=max_results, namespace=namespace)
        return [r for r in results if r.score >= threshold]

    # ==================== Namespace Operations ====================

    def create_namespace(self, namespace: str) -> bool:
        """Create a namespace."""
        self._store.setdefault(namespace, {})
        return True

    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace."""
        self._store.pop(namespace, None)
        return True

    def list_namespaces(self) -> List[str]:
        """List all namespaces."""
        return list(self._store.keys())

    def get_namespace_stats(self, namespace: str) -> Dict[str, Any]:
        """Get namespace statistics."""
        return {"namespace": namespace, "count": len(self._store.get(namespace, {}))}

    # ==================== Embedding Integration ====================

    def store_with_embedding(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict] = None,
        namespace: str = "default",
    ) -> bool:
        """Store text with auto-generated embedding."""
        embedding = self.get_embedding(text)
        meta = metadata or {}
        meta["_text"] = text
        return self.upsert(id, embedding, meta, namespace)

    def search_by_text(
        self,
        query: str,
        top_k: int = 10,
        namespace: str = "default",
        filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """Search using text query (auto-embedded)."""
        embedding = self.get_embedding(query)
        return self.search(embedding, top_k=top_k, namespace=namespace, filter=filter)

    def set_embedding_model(self, model_name: str) -> None:
        """Set embedding model for text operations."""
        self._embedding_model = model_name

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        # Deterministic hash-based embedding for in-memory use (no external calls)
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        # Produce a 256-dim unit vector from the hash bytes
        floats = [(b / 127.5) - 1.0 for b in h]  # 32 dims from 32 bytes
        # Pad/repeat to match dimension
        while len(floats) < self._dimension:
            floats.extend(floats)
        floats = floats[: self._dimension]
        if _HAS_NUMPY:
            arr = np.array(floats, dtype=float)
            norm = np.linalg.norm(arr)
            return (arr / norm).tolist() if norm > 0 else floats
        norm = math.sqrt(sum(x ** 2 for x in floats))
        return [x / norm for x in floats] if norm > 0 else floats

    # ==================== Utility ====================

    def count(self, namespace: str = "default", filter: Optional[Dict] = None) -> int:
        """Count vectors in namespace."""
        ns = self._store.get(namespace, {})
        if filter is None:
            return len(ns)
        return sum(
            1 for e in ns.values()
            if all(e.metadata.get(k) == v for k, v in filter.items())
        )

    def clear_namespace(self, namespace: str) -> bool:
        """Clear all vectors in namespace."""
        self._store[namespace] = {}
        return True

    def clear_all(self) -> bool:
        """Clear all vectors in index."""
        self._store = {ns: {} for ns in self._store}
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "backend": "in-memory",
            "connected": self._connected,
            "total_vectors": sum(len(v) for v in self._store.values()),
            "namespaces": {ns: len(vecs) for ns, vecs in self._store.items()},
            "dimension": self._dimension,
        }

    def optimize(self) -> None:
        """Optimize index for better performance."""
        # No-op for in-memory store
        pass
