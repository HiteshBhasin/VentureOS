# Research & analysis agent
import json
import uuid
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Agent specialized for research, information gathering, and analysis."""

    def __init__(
        self,
        agent_id: str,
        llm,
        memory=None,
        tools: Optional[List] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__(agent_id, llm, memory, tools, config)
        self.research_sources: List[str] = []
        self.findings: List[Dict[str, Any]] = []

    # ==================== Core Execution ====================

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a research task."""
        task_type = task.get("type")

        if task_type == "search_web":
            results = self.search_web(
                query=task.get("query", ""),
                num_results=int(task.get("num_results", 10)),
            )
            return {"status": "success", "type": task_type, "results": results}

        if task_type == "summarize_content":
            summary = self.summarize_content(
                content=task.get("content", ""),
                max_length=int(task.get("max_length", 500)),
            )
            return {"status": "success", "type": task_type, "summary": summary}

        if task_type == "fact_check":
            result = self.fact_check(
                claim=task.get("claim", ""),
                sources=task.get("sources"),
            )
            return {"status": "success", "type": task_type, "result": result}

        if task_type == "generate_report":
            report = self.generate_report(
                findings=task.get("findings", self.findings),
                format=task.get("format", "markdown"),
            )
            return {"status": "success", "type": task_type, "report": report}

        return {"status": "error", "error": f"Unsupported task type: {task_type}"}

    # ==================== Search & Discovery ====================

    def search_web(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search the web for information."""
        prompt = (
            f"Provide up to {num_results} web research leads for query: {query}. "
            "Return concise bullet points with title and relevance."
        )
        system_prompt = (
            "You are a research assistant that suggests high-quality sources."
        )
        response = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""

        lines = [
            line.strip("- ").strip() for line in response.splitlines() if line.strip()
        ]
        results: List[Dict[str, Any]] = []
        for idx, line in enumerate(lines[:num_results], start=1):
            results.append(
                {
                    "id": f"web-{idx}",
                    "title": line[:120],
                    "url": "",
                    "snippet": line,
                    "relevance": "high" if idx <= 3 else "medium",
                }
            )
        return results

    def search_documents(
        self, query: str, document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search within stored documents."""
        documents = document_ids or list(self.code_context.keys())
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        for doc_id in documents:
            text = str(self.code_context.get(doc_id, ""))
            if query_lower in text.lower():
                results.append(
                    {
                        "document_id": doc_id,
                        "matched": True,
                        "preview": text[:240],
                    }
                )
        return results

    def search_code_repositories(
        self, query: str, languages: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search code repositories for relevant code."""
        langs = languages or ["python"]
        return [
            {
                "repository": "local-workspace",
                "query": query,
                "languages": langs,
                "note": "Repository search integration not configured; returning query metadata.",
            }
        ]

    def search_academic(
        self, query: str, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search academic papers and publications."""
        prompt = (
            f"Suggest academic search keywords and likely paper topics for: {query}. "
            f"Constraints: {filters or {}}"
        )
        system_prompt = "You are an academic research assistant."
        response = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        lines = [
            line.strip("- ").strip() for line in response.splitlines() if line.strip()
        ]
        return [
            {
                "title": line,
                "authors": [],
                "year": None,
                "source": "suggested",
            }
            for line in lines[:10]
        ]

    def find_related_topics(self, topic: str, depth: int = 2) -> List[str]:
        """Find related topics for exploration."""
        prompt = (
            f"List related research topics for '{topic}' with exploration depth {depth}. "
            "Return one topic per line."
        )
        system_prompt = "You are a knowledge graph assistant."
        response = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return [
            line.strip("- ").strip() for line in response.splitlines() if line.strip()
        ]

    # ==================== Data Collection ====================

    def scrape_url(self, url: str, selectors: Optional[Dict] = None) -> Dict[str, Any]:
        """Scrape content from a URL."""
        return {
            "url": url,
            "selectors": selectors or {},
            "content": "",
            "status": "not_fetched",
            "message": "Scraper tool integration is not configured.",
        }

    def fetch_api_data(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fetch data from an API endpoint."""
        return {
            "endpoint": endpoint,
            "params": params or {},
            "data": None,
            "status": "not_fetched",
            "message": "API fetch integration is not configured.",
        }

    def extract_text_from_document(self, document_path: str) -> str:
        """Extract text content from a document."""
        if document_path in self.code_context:
            return str(self.code_context[document_path])
        return ""

    def collect_data_points(
        self, sources: List[str], data_spec: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Collect specific data points from multiple sources."""
        points: List[Dict[str, Any]] = []
        fields = data_spec.get("fields", [])
        for source in sources:
            points.append(
                {
                    "source": source,
                    "fields": fields,
                    "data": {},
                    "status": "collected_stub",
                }
            )
        return points

    # ==================== Analysis ====================

    def analyze_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collected findings."""
        prompt = f"Analyze these findings and provide themes, risks, and recommendations:\n{findings}"
        system_prompt = "You are a senior research analyst."
        analysis = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "total_findings": len(findings),
            "analysis": analysis,
            "high_confidence_count": sum(
                1
                for item in findings
                if str(item.get("confidence", "")).lower()
                in {"high", "0.8", "0.9", "1.0"}
            ),
        }

    def summarize_content(self, content: str, max_length: int = 500) -> str:
        """Summarize content to specified length."""
        prompt = f"Summarize the following content in under {max_length} characters:\n{content}"
        system_prompt = "You are a concise summarization assistant."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return summary[:max_length]

    def extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content."""
        prompt = f"Extract key points from this content. Return one point per line:\n{content}"
        system_prompt = "You are an information extraction assistant."
        response = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return [
            line.strip("- ").strip() for line in response.splitlines() if line.strip()
        ]

    def identify_trends(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify trends in data."""
        prompt = f"Identify major trends in this dataset:\n{data}"
        system_prompt = "You are a data trend analyst."
        response = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not response:
            return []
        return [{"trend": response, "confidence": "medium"}]

    def compare_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare information across multiple sources."""
        if not sources:
            return {"source_count": 0, "consensus": "none", "differences": []}

        titles = [str(source.get("title", "")) for source in sources]
        unique_titles = len(set(titles))
        consensus = "high" if unique_titles <= 1 else "mixed"
        return {
            "source_count": len(sources),
            "consensus": consensus,
            "differences": [] if consensus == "high" else ["Source titles vary"],
        }

    def fact_check(
        self, claim: str, sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Verify a claim against sources."""
        prompt = (
            f"Fact-check this claim and provide a verdict with confidence: {claim}. "
            f"Consider these sources if relevant: {sources or []}."
        )
        system_prompt = "You are a fact-checking assistant."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "claim": claim,
            "verdict": "needs_review",
            "confidence": "unknown",
            "analysis": result,
            "sources": sources or [],
        }

    def sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        prompt = (
            "Analyze the sentiment of this text and classify as positive, neutral, or "
            f"negative with short rationale:\n{text}"
        )
        system_prompt = "You are a sentiment analysis assistant."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"label": "unknown", "score": 0.0, "analysis": result}

    # ==================== Report Generation ====================

    def generate_report(
        self, findings: List[Dict[str, Any]], format: str = "markdown"
    ) -> str:
        """Generate a research report."""
        prompt = (
            f"Generate a {format} research report from these findings with sections for "
            f"overview, key findings, risks, and recommendations:\n{findings}"
        )
        system_prompt = "You are a professional research report writer."
        report = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return report

    def create_summary(self, research_id: str) -> Dict[str, Any]:
        """Create executive summary of research."""
        matching = [
            item for item in self.findings if item.get("research_id") == research_id
        ]
        report = self.generate_report(matching, format="markdown")
        summary = self.summarize_content(report, max_length=700)
        return {
            "research_id": research_id,
            "finding_count": len(matching),
            "summary": summary,
        }

    def compile_bibliography(self, sources: List[Dict[str, Any]]) -> str:
        """Compile bibliography from sources."""
        lines: List[str] = []
        for idx, source in enumerate(sources, start=1):
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            author = source.get("author", "Unknown")
            year = source.get("year", "n.d.")
            lines.append(f"{idx}. {author} ({year}). {title}. {url}".strip())
        return "\n".join(lines)

    def export_findings(self, format: str = "json") -> Any:
        """Export findings in specified format."""
        normalized = format.lower()
        if normalized == "json":
            return json.dumps(self.findings, indent=2)
        if normalized == "dict":
            return self.findings
        if normalized == "text":
            return "\n".join(str(item) for item in self.findings)
        return {"error": f"Unsupported export format: {format}"}

    # ==================== Research Management ====================

    def start_research_session(self, topic: str, objectives: List[str]) -> str:
        """Start a new research session."""
        session_id = f"research-{uuid.uuid4().hex[:10]}"
        self.add_to_context(
            "active_research_session",
            {
                "id": session_id,
                "topic": topic,
                "objectives": objectives,
            },
        )
        return session_id

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """Add a finding to current research."""
        self.findings.append(finding)

    def get_findings(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get findings with optional filters."""
        if not filters:
            return list(self.findings)

        filtered: List[Dict[str, Any]] = []
        for item in self.findings:
            if all(item.get(key) == value for key, value in filters.items()):
                filtered.append(item)
        return filtered

    def prioritize_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize sources by relevance and reliability."""

        def source_score(source: Dict[str, Any]) -> float:
            relevance = float(source.get("relevance_score", 0.5))
            reliability = float(source.get("reliability_score", 0.5))
            return (relevance * 0.6) + (reliability * 0.4)

        ranked = sorted(sources, key=source_score, reverse=True)
        for rank, source in enumerate(ranked, start=1):
            source["priority_rank"] = rank
            source["priority_score"] = round(source_score(source), 3)
        return ranked

    def validate_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Validate source credibility."""
        required_fields = ["title", "url"]
        missing = [field for field in required_fields if not source.get(field)]
        credibility = "high" if not missing else "low"
        return {
            "source": source,
            "is_valid": len(missing) == 0,
            "missing_fields": missing,
            "credibility": credibility,
        }

    def clear_findings(self) -> None:
        """Clear all findings."""
        self.findings.clear()
