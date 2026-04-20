# Web search tool
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import quote_plus, urlparse
import copy
import time

import httpx


class SearchEngine(Enum):
    """Supported search engines."""

    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"
    TAVILY = "tavily"


class SearchType(Enum):
    """Types of search."""

    WEB = "web"
    NEWS = "news"
    IMAGES = "images"
    VIDEOS = "videos"
    SCHOLAR = "scholar"


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str
    position: int
    source: str
    published_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Complete search response."""

    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    engine: SearchEngine
    search_type: SearchType


class WebSearch:
    """Web search tool with multiple engine support."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._default_engine: SearchEngine = SearchEngine.DUCKDUCKGO
        self._api_keys: Dict[SearchEngine, str] = {}
        self._cache_enabled: bool = False
        self._cache_ttl_seconds: int = 3600
        self._cache: Dict[str, Tuple[float, SearchResponse]] = {}
        self._rate_limits: Dict[SearchEngine, int] = {}
        self._rate_state: Dict[SearchEngine, Dict[str, Any]] = {}
        self._search_history: List[Dict[str, Any]] = []
        self._stats: Dict[str, Any] = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "avg_search_time_ms": 0.0,
            "by_engine": {engine.value: 0 for engine in SearchEngine},
            "by_type": {search_type.value: 0 for search_type in SearchType},
        }

        for engine in SearchEngine:
            env_name = f"{engine.value.upper()}_API_KEY"
            if env_name in self.config and self.config.get(env_name):
                self._api_keys[engine] = self.config[env_name]

        default_engine = self.config.get("default_engine")
        if isinstance(default_engine, str):
            try:
                self._default_engine = SearchEngine(default_engine.lower())
            except ValueError:
                pass

    # ==================== Configuration ====================

    def set_api_key(self, engine: SearchEngine, api_key: str) -> None:
        """Set API key for search engine."""
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        self._api_keys[engine] = api_key.strip()

    def set_default_engine(self, engine: SearchEngine) -> None:
        """Set default search engine."""
        self._default_engine = engine

    def get_default_engine(self) -> SearchEngine:
        """Get default search engine."""
        return self._default_engine

    def get_available_engines(self) -> List[SearchEngine]:
        """Get list of configured engines."""
        available = [SearchEngine.DUCKDUCKGO]
        for engine in [
            SearchEngine.GOOGLE,
            SearchEngine.BING,
            SearchEngine.SERPER,
            SearchEngine.TAVILY,
        ]:
            if engine in self._api_keys:
                available.append(engine)
        return available

    # ==================== Search Operations ====================

    def search(
        self, query: str, num_results: int = 10, engine: Optional[SearchEngine] = None
    ) -> SearchResponse:
        """Perform web search."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if num_results <= 0:
            raise ValueError("num_results must be > 0")

        active_engine = engine or self._default_engine
        search_type = SearchType.WEB
        cache_key = self._build_cache_key(
            active_engine, query, num_results, search_type
        )

        cached = self.get_cached_result(cache_key) if self._cache_enabled else None
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached
        self._stats["cache_misses"] += 1

        self._check_rate_limit(active_engine)
        start = time.perf_counter()

        try:
            if active_engine == SearchEngine.DUCKDUCKGO:
                response = self._search_duckduckgo(query, num_results, search_type)
            elif active_engine == SearchEngine.SERPER:
                response = self._search_serper(query, num_results, search_type)
            elif active_engine == SearchEngine.TAVILY:
                response = self._search_tavily(query, num_results, search_type)
            elif active_engine in {SearchEngine.GOOGLE, SearchEngine.BING}:
                # Google/Bing usually require paid APIs; if not configured, fallback safely.
                if SearchEngine.SERPER in self._api_keys:
                    response = self._search_serper(query, num_results, search_type)
                else:
                    response = self._search_duckduckgo(query, num_results, search_type)
            else:
                raise ValueError(f"Unsupported engine: {active_engine.value}")
        except Exception:
            self._stats["errors"] += 1
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        response.search_time_ms = elapsed_ms

        self._record_search(response)

        if self._cache_enabled:
            self._cache[cache_key] = (
                time.time() + self._cache_ttl_seconds,
                copy.deepcopy(response),
            )

        return response

    def search_news(
        self, query: str, num_results: int = 10, time_range: Optional[str] = None
    ) -> SearchResponse:
        """Search news articles."""
        decorated_query = query
        if time_range:
            decorated_query = f"{query} {time_range}"
        return self._search_typed(decorated_query, num_results, SearchType.NEWS)

    def search_images(
        self, query: str, num_results: int = 10, size: Optional[str] = None
    ) -> SearchResponse:
        """Search images."""
        decorated_query = query if size is None else f"{query} {size}"
        return self._search_typed(decorated_query, num_results, SearchType.IMAGES)

    def search_videos(
        self, query: str, num_results: int = 10, duration: Optional[str] = None
    ) -> SearchResponse:
        """Search videos."""
        decorated_query = query if duration is None else f"{query} {duration}"
        return self._search_typed(decorated_query, num_results, SearchType.VIDEOS)

    def search_scholar(
        self, query: str, num_results: int = 10, year_range: Optional[tuple] = None
    ) -> SearchResponse:
        """Search academic papers."""
        scholar_query = f"{query} site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov"
        if year_range and len(year_range) == 2:
            scholar_query = f"{scholar_query} {year_range[0]}..{year_range[1]}"
        return self._search_typed(scholar_query, num_results, SearchType.SCHOLAR)

    def search_site(
        self, query: str, site: str, num_results: int = 10
    ) -> SearchResponse:
        """Search within specific site."""
        if not site:
            raise ValueError("site cannot be empty")
        return self.search(f"{query} site:{site}", num_results=num_results)

    # ==================== Advanced Search ====================

    def search_with_filters(
        self, query: str, filters: Dict[str, Any], num_results: int = 10
    ) -> SearchResponse:
        """Search with advanced filters."""
        response = self.search(query, num_results=num_results)
        response.results = self.filter_results(response.results, filters)
        response.total_results = len(response.results)
        return response

    def search_exact_phrase(self, phrase: str, num_results: int = 10) -> SearchResponse:
        """Search for exact phrase."""
        return self.search(f'"{phrase}"', num_results=num_results)

    def search_exclude_terms(
        self, query: str, exclude: List[str], num_results: int = 10
    ) -> SearchResponse:
        """Search excluding specific terms."""
        exclusion = " ".join(f"-{term}" for term in exclude if term)
        full_query = f"{query} {exclusion}".strip()
        return self.search(full_query, num_results=num_results)

    def search_file_type(
        self, query: str, file_type: str, num_results: int = 10
    ) -> SearchResponse:
        """Search for specific file types."""
        if not file_type:
            raise ValueError("file_type cannot be empty")
        return self.search(f"{query} filetype:{file_type}", num_results=num_results)

    def search_by_date_range(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        num_results: int = 10,
    ) -> SearchResponse:
        """Search within date range."""
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")
        date_query = f"{query} after:{start_date.date().isoformat()} before:{end_date.date().isoformat()}"
        return self.search(date_query, num_results=num_results)

    def search_related(self, url: str, num_results: int = 10) -> SearchResponse:
        """Find pages related to URL."""
        if not url:
            raise ValueError("url cannot be empty")
        return self.search(f"related:{url}", num_results=num_results)

    # ==================== Multi-Engine Search ====================

    def search_all_engines(
        self, query: str, num_results: int = 10
    ) -> Dict[SearchEngine, SearchResponse]:
        """Search across all configured engines."""
        responses: Dict[SearchEngine, SearchResponse] = {}
        for engine in self.get_available_engines():
            try:
                responses[engine] = self.search(
                    query, num_results=num_results, engine=engine
                )
            except Exception:
                continue
        return responses

    def search_and_merge(
        self, query: str, engines: List[SearchEngine], num_results: int = 10
    ) -> SearchResponse:
        """Search multiple engines and merge results."""
        all_results: List[SearchResult] = []
        for engine in engines:
            try:
                response = self.search(query, num_results=num_results, engine=engine)
                all_results.extend(response.results)
            except Exception:
                continue

        deduped = self.deduplicate_results(all_results)
        merged = deduped[:num_results]
        for idx, item in enumerate(merged, start=1):
            item.position = idx

        return SearchResponse(
            query=query,
            results=merged,
            total_results=len(merged),
            search_time_ms=0.0,
            engine=self._default_engine,
            search_type=SearchType.WEB,
        )

    def compare_results(
        self, query: str, engines: List[SearchEngine]
    ) -> Dict[str, Any]:
        """Compare results across engines."""
        comparisons: Dict[str, Any] = {
            "query": query,
            "engines": {},
            "common_urls": [],
        }

        url_sets: Dict[SearchEngine, set] = {}
        for engine in engines:
            try:
                response = self.search(query, engine=engine)
                urls = {item.url for item in response.results}
                url_sets[engine] = urls
                comparisons["engines"][engine.value] = {
                    "count": len(response.results),
                    "top_titles": [item.title for item in response.results[:5]],
                    "domains": self.extract_domains(response.results),
                }
            except Exception as exc:
                comparisons["engines"][engine.value] = {"error": str(exc)}

        if url_sets:
            common = (
                set.intersection(*url_sets.values())
                if len(url_sets) > 1
                else next(iter(url_sets.values()))
            )
            comparisons["common_urls"] = sorted(common)

        return comparisons

    # ==================== Result Processing ====================

    def filter_results(
        self, results: List[SearchResult], filters: Dict[str, Any]
    ) -> List[SearchResult]:
        """Filter search results."""
        filtered = results

        domain = filters.get("domain")
        if domain:
            filtered = [r for r in filtered if domain in urlparse(r.url).netloc]

        contains = filters.get("contains")
        if contains:
            target = str(contains).lower()
            filtered = [
                r
                for r in filtered
                if target in r.title.lower() or target in r.snippet.lower()
            ]

        source = filters.get("source")
        if source:
            filtered = [r for r in filtered if r.source.lower() == str(source).lower()]

        if filters.get("has_date") is True:
            filtered = [r for r in filtered if r.published_date is not None]

        return filtered

    def rank_results(
        self, results: List[SearchResult], criteria: Dict[str, float]
    ) -> List[SearchResult]:
        """Re-rank results by criteria."""
        domain_boosts = criteria.get("domain_boost", {})
        keyword = str(criteria.get("keyword", "")).lower()
        keyword_weight = float(criteria.get("keyword_weight", 1.0))
        recency_weight = float(criteria.get("recency_weight", 0.0))

        scored: List[Tuple[float, SearchResult]] = []
        now = datetime.utcnow()

        for result in results:
            score = max(0.0, 1.0 - (result.position - 1) * 0.05)

            host = urlparse(result.url).netloc
            for domain, boost in domain_boosts.items():
                if domain in host:
                    score += float(boost)

            if keyword and (
                keyword in result.title.lower() or keyword in result.snippet.lower()
            ):
                score += keyword_weight

            if recency_weight > 0 and result.published_date is not None:
                days_old = max(1, (now - result.published_date).days)
                score += recency_weight * (1.0 / days_old)

            scored.append((score, result))

        ranked = [r for _, r in sorted(scored, key=lambda item: item[0], reverse=True)]
        for idx, item in enumerate(ranked, start=1):
            item.position = idx
        return ranked

    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results."""
        seen: set = set()
        deduped: List[SearchResult] = []
        for result in results:
            normalized = result.url.rstrip("/").lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(result)

        for idx, item in enumerate(deduped, start=1):
            item.position = idx
        return deduped

    def extract_domains(self, results: List[SearchResult]) -> List[str]:
        """Extract unique domains from results."""
        domains = {
            urlparse(result.url).netloc.lower() for result in results if result.url
        }
        return sorted([d for d in domains if d])

    # ==================== Caching ====================

    def enable_cache(self, ttl_seconds: int = 3600) -> None:
        """Enable result caching."""
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be > 0")
        self._cache_enabled = True
        self._cache_ttl_seconds = ttl_seconds

    def disable_cache(self) -> None:
        """Disable result caching."""
        self._cache_enabled = False

    def clear_cache(self) -> None:
        """Clear search cache."""
        self._cache.clear()

    def get_cached_result(self, query: str) -> Optional[SearchResponse]:
        """Get cached result for query."""
        record = self._cache.get(query)
        if not record:
            return None
        expires_at, response = record
        if time.time() > expires_at:
            self._cache.pop(query, None)
            return None
        return copy.deepcopy(response)

    # ==================== Rate Limiting ====================

    def set_rate_limit(self, engine: SearchEngine, requests_per_minute: int) -> None:
        """Set rate limit for engine."""
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be > 0")
        self._rate_limits[engine] = requests_per_minute
        self._rate_state.setdefault(engine, {"window_start": time.time(), "count": 0})

    def get_rate_limit_status(self, engine: SearchEngine) -> Dict[str, Any]:
        """Get rate limit status."""
        limit = self._rate_limits.get(engine)
        state = self._rate_state.get(engine, {"window_start": time.time(), "count": 0})
        now = time.time()
        elapsed = now - float(state["window_start"])
        remaining_window = max(0, 60 - int(elapsed))
        remaining_requests = (
            None if limit is None else max(0, limit - int(state["count"]))
        )
        return {
            "engine": engine.value,
            "limit": limit,
            "used": int(state["count"]),
            "remaining_requests": remaining_requests,
            "window_seconds_remaining": remaining_window,
        }

    def reset_rate_limit(self, engine: SearchEngine) -> None:
        """Reset rate limit counter."""
        self._rate_state[engine] = {"window_start": time.time(), "count": 0}

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        snapshot = copy.deepcopy(self._stats)
        snapshot["history_size"] = len(self._search_history)
        snapshot["cache_entries"] = len(self._cache)
        snapshot["default_engine"] = self._default_engine.value
        return snapshot

    def get_search_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get search history."""
        if limit <= 0:
            return []
        return copy.deepcopy(self._search_history[-limit:])

    def clear_history(self) -> None:
        """Clear search history."""
        self._search_history.clear()

    # ==================== Internal Helpers ====================

    def _build_cache_key(
        self,
        engine: SearchEngine,
        query: str,
        num_results: int,
        search_type: SearchType,
    ) -> str:
        return (
            f"{engine.value}|{search_type.value}|{num_results}|{query.strip().lower()}"
        )

    def _search_typed(
        self, query: str, num_results: int, search_type: SearchType
    ) -> SearchResponse:
        engine = self._default_engine
        self._check_rate_limit(engine)
        start = time.perf_counter()

        try:
            if engine == SearchEngine.SERPER:
                response = self._search_serper(query, num_results, search_type)
            elif engine == SearchEngine.TAVILY and search_type == SearchType.WEB:
                response = self._search_tavily(query, num_results, search_type)
            else:
                # DuckDuckGo endpoint is web-focused; non-web types use query decoration.
                response = self._search_duckduckgo(query, num_results, search_type)
        except Exception:
            self._stats["errors"] += 1
            raise

        response.search_time_ms = (time.perf_counter() - start) * 1000.0
        self._record_search(response)
        return response

    def _check_rate_limit(self, engine: SearchEngine) -> None:
        limit = self._rate_limits.get(engine)
        if limit is None:
            return

        now = time.time()
        state = self._rate_state.setdefault(engine, {"window_start": now, "count": 0})

        if now - float(state["window_start"]) >= 60:
            state["window_start"] = now
            state["count"] = 0

        if int(state["count"]) >= limit:
            raise RuntimeError(
                f"Rate limit exceeded for {engine.value}: {limit}/minute"
            )

        state["count"] = int(state["count"]) + 1

    def _record_search(self, response: SearchResponse) -> None:
        self._stats["total_searches"] += 1
        self._stats["by_engine"][response.engine.value] += 1
        self._stats["by_type"][response.search_type.value] += 1

        total = self._stats["total_searches"]
        old_avg = float(self._stats["avg_search_time_ms"])
        self._stats["avg_search_time_ms"] = (
            (old_avg * (total - 1)) + response.search_time_ms
        ) / total

        self._search_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "query": response.query,
                "engine": response.engine.value,
                "search_type": response.search_type.value,
                "total_results": response.total_results,
                "search_time_ms": response.search_time_ms,
            }
        )

        max_history = int(self.config.get("max_history", 1000))
        if len(self._search_history) > max_history:
            self._search_history = self._search_history[-max_history:]

    def _make_client(self) -> httpx.Client:
        timeout_s = float(self.config.get("timeout_seconds", 10.0))
        user_agent = self.config.get("user_agent", "venture-os-web-search/1.0")
        return httpx.Client(
            timeout=timeout_s,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    def _search_duckduckgo(
        self, query: str, num_results: int, search_type: SearchType
    ) -> SearchResponse:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1,
        }

        results: List[SearchResult] = []
        with self._make_client() as client:
            payload = client.get(url, params=params).json()

        position = 1
        abstract_url = payload.get("AbstractURL")
        if abstract_url:
            results.append(
                SearchResult(
                    title=payload.get("Heading")
                    or payload.get("AbstractSource")
                    or "Result",
                    url=abstract_url,
                    snippet=payload.get("AbstractText") or "",
                    position=position,
                    source="duckduckgo",
                )
            )
            position += 1

        def walk_topics(topics: List[Dict[str, Any]]) -> None:
            nonlocal position
            for item in topics:
                if position > num_results:
                    return
                if "Topics" in item:
                    walk_topics(item.get("Topics", []))
                    continue
                first_url = item.get("FirstURL")
                text = item.get("Text", "")
                if not first_url:
                    continue
                title = text.split(" - ")[0].strip() if text else first_url
                results.append(
                    SearchResult(
                        title=title,
                        url=first_url,
                        snippet=text,
                        position=position,
                        source="duckduckgo",
                    )
                )
                position += 1

        walk_topics(payload.get("RelatedTopics", []))

        if len(results) < num_results:
            fallback_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            results.append(
                SearchResult(
                    title=f"DuckDuckGo results for: {query}",
                    url=fallback_url,
                    snippet="Open this page for full search results.",
                    position=len(results) + 1,
                    source="duckduckgo",
                )
            )

        trimmed = results[:num_results]
        return SearchResponse(
            query=query,
            results=trimmed,
            total_results=len(trimmed),
            search_time_ms=0.0,
            engine=SearchEngine.DUCKDUCKGO,
            search_type=search_type,
        )

    def _search_serper(
        self, query: str, num_results: int, search_type: SearchType
    ) -> SearchResponse:
        api_key = self._api_keys.get(SearchEngine.SERPER)
        if not api_key:
            raise RuntimeError("SERPER_API_KEY is required for Serper search")

        endpoint_map = {
            SearchType.WEB: "search",
            SearchType.NEWS: "news",
            SearchType.IMAGES: "images",
            SearchType.VIDEOS: "videos",
            SearchType.SCHOLAR: "search",
        }
        endpoint = endpoint_map[search_type]
        url = f"https://google.serper.dev/{endpoint}"

        payload = {"q": query, "num": num_results}

        with self._make_client() as client:
            response = client.post(
                url,
                json=payload,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        key_map = {
            SearchType.WEB: "organic",
            SearchType.NEWS: "news",
            SearchType.IMAGES: "images",
            SearchType.VIDEOS: "videos",
            SearchType.SCHOLAR: "organic",
        }
        raw_results = data.get(key_map[search_type], [])

        results: List[SearchResult] = []
        for idx, item in enumerate(raw_results[:num_results], start=1):
            date_value = item.get("date")
            published_date = None
            if date_value and isinstance(date_value, str):
                try:
                    published_date = datetime.fromisoformat(
                        date_value.replace("Z", "+00:00")
                    )
                except ValueError:
                    published_date = None

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    position=idx,
                    source="serper",
                    published_date=published_date,
                    metadata={
                        "thumbnail": item.get("imageUrl") or item.get("thumbnailUrl"),
                        "raw": item,
                    },
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_time_ms=0.0,
            engine=SearchEngine.SERPER,
            search_type=search_type,
        )

    def _search_tavily(
        self, query: str, num_results: int, search_type: SearchType
    ) -> SearchResponse:
        if search_type != SearchType.WEB:
            # Tavily is optimized for web/research search.
            return self._search_duckduckgo(query, num_results, search_type)

        api_key = self._api_keys.get(SearchEngine.TAVILY)
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is required for Tavily search")

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": num_results,
            "include_answer": False,
            "include_raw_content": False,
        }

        with self._make_client() as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_results = data.get("results", [])
        results: List[SearchResult] = []
        for idx, item in enumerate(raw_results[:num_results], start=1):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    position=idx,
                    source="tavily",
                    metadata={"score": item.get("score")},
                )
            )

        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_time_ms=0.0,
            engine=SearchEngine.TAVILY,
            search_type=search_type,
        )
