# Text embedding generation
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np


class EmbeddingProvider(Enum):
    """Supported embedding providers."""

    OPENAI = "openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    VOYAGER = "voyager"
    LOCAL = "local"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding model."""

    provider: EmbeddingProvider
    model_name: str
    dimension: int
    max_tokens: int
    batch_size: int = 32
    normalize: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""

    text: str
    embedding: List[float]
    model: str
    tokens_used: int
    dimension: int


class EmbeddingModel:
    """Wrapper for embedding models."""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config
        self._model = None
        self._cache: Dict[str, List[float]] = {}
        self._cache_enabled: bool = False
        self._stats: Dict[str, Any] = {
            "total_tokens": 0,
            "total_requests": 0,
            "cache_hits": 0,
        }

    # ==================== Configuration ====================

    def load_model(
        self,
        provider: EmbeddingProvider,
        model_name: str,
        api_key: Optional[str] = None,
    ) -> None:
        """Load embedding model."""
        if provider == EmbeddingProvider.OPENAI:
            import openai

            if api_key:
                openai.api_key = api_key
                self._model = {
                    "provider": provider,
                    "model_name": model_name,
                    "api_key": api_key,
                }  # Placeholder for actual model loading
        elif provider == EmbeddingProvider.COHERE:
            import cohere

            if api_key:
                self._model = {
                    "provider": provider,
                    "model_name": model_name,
                    "api_key": api_key,
                }  # Placeholder for actual model loading
        elif provider == EmbeddingProvider.HUGGINGFACE:
            from transformers import AutoTokenizer, AutoModel

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            self._model = {
                "provider": provider,
                "model_name": model_name,
                "tokenizer": tokenizer,
                "model": model,
                "api_key": api_key,
            }
        elif provider == EmbeddingProvider.LOCAL:
            # Placeholder for local model loading
            self._model = {
                "provider": provider,
                "model_name": model_name,
            }
        elif provider == EmbeddingProvider.VOYAGER:
            import voyager

            self._model = {
                "provider": provider,
                "model_name": model_name,
                "api_key": api_key,
            }  # Placeholder for actual model loading
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def unload_model(self) -> None:
        """Unload current model."""
        self._model = None

    def set_config(self, config: EmbeddingConfig) -> None:
        """Set model configuration."""
        self.config = config

    def get_config(self) -> Optional[EmbeddingConfig]:
        """Get current configuration."""
        return self.config

    def set_api_key(self, api_key: str) -> None:
        """Set API key for provider."""
        if self._model:
            self._model["api_key"] = api_key

    # ==================== Embedding Operations ====================

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if text is None or text.strip() == "":
            raise ValueError("Input text cannot be empty.")
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            raise ValueError("Input texts cannot be empty.")
        model = SentenceTransformer("Qwen/Qwen3-VL-Embedding-2B")
        return model.encode(texts).tolist()

    def embed_with_metadata(self, text: str) -> EmbeddingResult:
        """Generate embedding with metadata."""
        embedded_vector = self.embed(text)
        tokens_used = self.count_tokens(text)
        dimension = len(embedded_vector)
        return EmbeddingResult(
            text=text,
            embedding=embedded_vector,
            model=self.get_current_model() or "unknown",
            tokens_used=tokens_used,
            dimension=dimension,
        )

    def embed_document(
        self, document: str, chunk_size: int = 512, overlap: int = 50
    ) -> List[List[float]]:
        """Embed document with chunking."""

        if not document:
            raise ValueError("Input document cannot be empty.")
        step = chunk_size - overlap
        chunks = [document[i : i + chunk_size] for i in range(0, len(document), step)]
        return self.embed_batch(chunks)

    def embed_query(self, query: str) -> List[float]:
        """Generate query-optimized embedding."""
        if not query or not self.config:
            raise ValueError("Query cannot be empty and model must be configured.")
        return self.embed(query)

    # ==================== Similarity ====================

    def cosine_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity."""
        if not embedding1 or not embedding2:
            raise ValueError("Embeddings cannot be empty.")
        a = np.array(embedding1, dtype=np.float64)
        b = np.array(embedding2, dtype=np.float64)
        norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def euclidean_distance(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate Euclidean distance."""
        a = np.array(embedding1, dtype=np.float64)
        b = np.array(embedding2, dtype=np.float64)
        return float(np.linalg.norm(a - b))

    def dot_product(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate dot product."""
        a = np.array(embedding1, dtype=np.float64)
        b = np.array(embedding2, dtype=np.float64)
        return float(np.dot(a, b))

    def find_most_similar(
        self,
        query_embedding: List[float],
        embeddings: List[List[float]],
        top_k: int = 5,
    ) -> List[tuple]:
        """Find most similar embeddings."""
        if not query_embedding or not embeddings:
            raise ValueError("Query embedding and embeddings list cannot be empty.")

        similarities = [
            (i, self.cosine_similarity(query_embedding, emb))
            for i, emb in enumerate(embeddings)
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def similarity_matrix(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Calculate similarity matrix."""
        arr = np.array(embeddings, dtype=np.float64)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = arr / norms
        return (normalized @ normalized.T).tolist()

    # ==================== Utilities ====================

    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding vector."""
        a = np.array(embedding, dtype=np.float64)
        norm = np.linalg.norm(a)
        if norm == 0:
            return embedding
        return (a / norm).tolist()

    def average_embeddings(self, embeddings: List[List[float]]) -> List[float]:
        """Average multiple embeddings."""
        return np.mean(np.array(embeddings, dtype=np.float64), axis=0).tolist()

    def reduce_dimension(
        self, embeddings: List[List[float]], target_dim: int
    ) -> List[List[float]]:
        """Reduce embedding dimensions."""
        from sklearn.decomposition import PCA

        pca = PCA(n_components=target_dim)
        return pca.fit_transform(np.array(embeddings, dtype=np.float64)).tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self.config:
            return self.config.dimension
        return 0

    def get_max_tokens(self) -> int:
        """Get maximum tokens."""
        if self.config:
            return self.config.max_tokens
        return 0

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        # Approximate: ~4 characters per token (standard heuristic)
        return max(1, len(text) // 4)

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to max tokens."""
        return text[: max_tokens * 4]

    # ==================== Caching ====================

    def enable_cache(self) -> None:
        """Enable embedding cache."""
        self._cache_enabled = True

    def disable_cache(self) -> None:
        """Disable embedding cache."""
        self._cache_enabled = False

    def get_cached(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        return self._cache.get(text)

    def cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding."""
        if self._cache_enabled:
            self._cache[text] = embedding

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get cache size."""
        return len(self._cache)

    # ==================== Provider-specific ====================

    def embed_openai(
        self, texts: List[str], model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        import openai

        api_key = self._model.get("api_key") if self._model else None
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(input=texts, model=model)
        return [item.embedding for item in response.data]

    def embed_cohere(
        self, texts: List[str], model: str = "embed-english-v3.0"
    ) -> List[List[float]]:
        """Generate embeddings using Cohere."""
        import cohere

        api_key = self._model.get("api_key") if self._model else None
        co = cohere.Client(api_key=api_key)
        response = co.embed(texts=texts, model=model, input_type="search_document")
        return [list(emb) for emb in response.embeddings]

    def embed_huggingface(
        self, texts: List[str], model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> List[List[float]]:
        """Generate embeddings using HuggingFace."""
        from sentence_transformers import SentenceTransformer as ST

        st_model = ST(model)
        return st_model.encode(texts).tolist()

    def embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        if self._model and "model" in self._model:
            return self._model["model"].encode(texts).tolist()
        raise RuntimeError("No local model loaded. Call load_model() first.")

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        return dict(self._stats)

    def get_usage(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            "total_requests": self._stats["total_requests"],
            "total_tokens": self._stats["total_tokens"],
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {"total_tokens": 0, "total_requests": 0, "cache_hits": 0}

    # ==================== Available Models ====================

    def list_available_models(
        self, provider: Optional[EmbeddingProvider] = None
    ) -> List[str]:
        """List available models."""
        all_models: Dict[EmbeddingProvider, List[str]] = {
            EmbeddingProvider.OPENAI: [
                "text-embedding-3-small",
                "text-embedding-3-large",
                "text-embedding-ada-002",
            ],
            EmbeddingProvider.COHERE: [
                "embed-english-v3.0",
                "embed-multilingual-v3.0",
                "embed-english-light-v3.0",
            ],
            EmbeddingProvider.HUGGINGFACE: [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
            ],
            EmbeddingProvider.SENTENCE_TRANSFORMERS: [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "paraphrase-MiniLM-L6-v2",
            ],
            EmbeddingProvider.LOCAL: [],
            EmbeddingProvider.VOYAGER: [],
        }
        if provider:
            return all_models.get(provider, [])
        return [m for models in all_models.values() for m in models]

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information."""
        if self._model and self._model.get("model_name") == model_name:
            return {k: v for k, v in self._model.items() if k != "api_key"}
        return {"model_name": model_name}

    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def get_current_model(self) -> Optional[str]:
        """Get current model name."""
        if self._model:
            return self._model.get("model_name")
        return None
