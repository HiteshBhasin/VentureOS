# Review & QA agent
import uuid
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class ReviewAgent(BaseAgent):
    """Agent specialized for quality assurance, code review, and validation."""

    def __init__(
        self,
        agent_id: str,
        llm,
        memory=None,
        tools: Optional[List] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__(agent_id, llm, memory, tools, config)
        self.review_criteria: Dict[str, Any] = {}
        self.review_history: List[Dict[str, Any]] = []

    # ==================== Core Execution ====================

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a review or QA task."""
        task_type = task.get("type")

        if task_type == "review_code":
            result = self.review_code(
                code=task.get("code", ""),
                criteria=task.get("criteria"),
            )
            self.add_to_review_history(result)
            return {"status": "success", "type": task_type, "result": result}

        if task_type == "security_scan":
            findings = self.security_scan(code=task.get("code", ""))
            return {"status": "success", "type": task_type, "findings": findings}

        if task_type == "review_tests":
            result = self.review_tests(test_code=task.get("test_code", ""))
            self.add_to_review_history(result)
            return {"status": "success", "type": task_type, "result": result}

        return {"status": "error", "error": f"Unsupported task type: {task_type}"}

    # ==================== Code Review ====================

    def review_code(self, code: str, criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive code review."""
        active_criteria = criteria or self.review_criteria
        prompt = (
            "Review the following code and provide risks, defects, maintainability issues, "
            f"and actionable improvements. Criteria: {active_criteria}\n{code}"
        )
        system_prompt = "You are a senior code reviewer."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "review_id": f"review-{uuid.uuid4().hex[:8]}",
            "summary": summary,
            "criteria": active_criteria,
            "issues": [],
            "recommendation": "changes_requested" if summary else "approve",
        }

    def review_pull_request(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review a pull request."""
        title = pr_data.get("title", "Untitled PR")
        description = pr_data.get("description", "")
        files = pr_data.get("files", [])
        prompt = (
            f"Review this pull request. Title: {title}\nDescription: {description}\n"
            f"Changed files metadata: {files}"
        )
        system_prompt = "You are a pull request reviewer."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {
            "pr": title,
            "summary": summary,
            "file_count": len(files) if isinstance(files, list) else 0,
            "approved": False,
        }

    def check_coding_standards(self, code: str, standards: str) -> List[Dict[str, Any]]:
        """Check code against coding standards."""
        prompt = f"Check this code against {standards} and list violations:\n{code}"
        system_prompt = "You are a strict coding standards auditor."
        findings = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not findings:
            return []
        return [{"standard": standards, "finding": findings}]

    def review_architecture(self, architecture_doc: str) -> Dict[str, Any]:
        """Review system architecture design."""
        prompt = f"Review this architecture doc for risks and trade-offs:\n{architecture_doc}"
        system_prompt = "You are a software architecture reviewer."
        assessment = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"assessment": assessment, "decision": "revise" if assessment else "ok"}

    def review_api_design(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Review API design and endpoints."""
        prompt = (
            f"Review this API design for consistency and best practices:\n{api_spec}"
        )
        system_prompt = "You are an API design reviewer."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"analysis": result, "api_spec": api_spec}

    # ==================== Security Review ====================

    def security_scan(self, code: str) -> List[Dict[str, Any]]:
        """Scan code for security vulnerabilities."""
        prompt = (
            "Review this code for common security issues (injection, auth flaws, secrets, "
            f"unsafe deserialization):\n{code}"
        )
        system_prompt = "You are an application security reviewer."
        findings = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not findings:
            return []
        return [{"severity": "medium", "finding": findings}]

    def check_dependencies(self, dependencies: List[str]) -> List[Dict[str, Any]]:
        """Check dependencies for known vulnerabilities."""
        return [
            {
                "dependency": dep,
                "status": "unchecked",
                "note": "Vulnerability DB integration not configured.",
            }
            for dep in dependencies
        ]

    def review_authentication(self, auth_code: str) -> Dict[str, Any]:
        """Review authentication implementation."""
        prompt = f"Review this authentication code for security and correctness:\n{auth_code}"
        system_prompt = "You are an authentication security expert."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"summary": summary, "risk_level": "unknown"}

    def check_data_handling(self, code: str) -> List[Dict[str, Any]]:
        """Check for proper data handling and privacy."""
        prompt = (
            "Check this code for data privacy, PII handling, logging hygiene, and retention "
            f"risks:\n{code}"
        )
        system_prompt = "You are a data privacy reviewer."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not result:
            return []
        return [{"category": "data_handling", "finding": result}]

    # ==================== Performance Review ====================

    def review_performance(self, code: str) -> Dict[str, Any]:
        """Review code for performance issues."""
        prompt = (
            f"Review this code for performance issues and optimization ideas:\n{code}"
        )
        system_prompt = "You are a performance engineer."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"summary": summary, "status": "reviewed"}

    def identify_bottlenecks(self, code: str) -> List[Dict[str, Any]]:
        """Identify potential performance bottlenecks."""
        prompt = f"Identify likely bottlenecks in this code:\n{code}"
        system_prompt = "You are a profiling expert."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not result:
            return []
        return [{"bottleneck": result, "impact": "unknown"}]

    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity metrics."""
        prompt = (
            f"Estimate complexity and maintainability concerns in this code:\n{code}"
        )
        system_prompt = "You are a code quality analyst."
        analysis = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"analysis": analysis, "cyclomatic": "unknown", "cognitive": "unknown"}

    def review_database_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Review database queries for efficiency."""
        reviews: List[Dict[str, Any]] = []
        for query in queries:
            prompt = (
                f"Review this database query for performance and correctness:\n{query}"
            )
            system_prompt = "You are a database performance reviewer."
            review = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
            reviews.append({"query": query, "review": review})
        return reviews

    # ==================== Test Review ====================

    def review_tests(self, test_code: str) -> Dict[str, Any]:
        """Review test coverage and quality."""
        prompt = (
            "Review this test code for quality, coverage gaps, and flaky patterns:\n"
            f"{test_code}"
        )
        system_prompt = "You are a software test architect."
        summary = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"summary": summary, "coverage_quality": "unknown"}

    def analyze_test_coverage(self, coverage_report: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test coverage report."""
        total = float(coverage_report.get("total", 0.0))
        status = "good" if total >= 80 else "needs_improvement"
        return {
            "total": total,
            "status": status,
            "recommendation": (
                "Increase tests for low-coverage modules"
                if total < 80
                else "Maintain current coverage"
            ),
        }

    def suggest_test_cases(self, code: str) -> List[Dict[str, Any]]:
        """Suggest additional test cases."""
        prompt = f"Suggest additional test cases for this code:\n{code}"
        system_prompt = "You are a QA engineer specialized in edge-case testing."
        suggestions = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not suggestions:
            return []
        return [{"type": "suggested", "details": suggestions}]

    def validate_test_assertions(self, test_code: str) -> List[Dict[str, Any]]:
        """Validate test assertions are meaningful."""
        prompt = (
            "Assess whether the assertions in these tests are meaningful and sufficient:\n"
            f"{test_code}"
        )
        system_prompt = "You are a testing quality reviewer."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not result:
            return []
        return [{"assessment": result}]

    # ==================== Documentation Review ====================

    def review_documentation(self, docs: str) -> Dict[str, Any]:
        """Review documentation quality and completeness."""
        prompt = f"Review this documentation for clarity and completeness:\n{docs}"
        system_prompt = "You are a technical documentation reviewer."
        review = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"summary": review, "quality": "unknown"}

    def check_api_documentation(self, api_docs: str, api_spec: Dict) -> Dict[str, Any]:
        """Check API documentation against specification."""
        prompt = (
            "Compare API documentation against API specification and list mismatches.\n"
            f"Docs:\n{api_docs}\nSpec:\n{api_spec}"
        )
        system_prompt = "You are an API documentation auditor."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        return {"result": result, "matches": False if result else True}

    def review_comments(self, code: str) -> List[Dict[str, Any]]:
        """Review code comments for accuracy and usefulness."""
        prompt = f"Review comments in this code for accuracy and usefulness:\n{code}"
        system_prompt = "You are a code readability reviewer."
        result = self._invoke_llm(prompt=prompt, system_prompt=system_prompt) or ""
        if not result:
            return []
        return [{"comment_review": result}]

    # ==================== Validation ====================

    def validate_output(self, output: Any, expected_schema: Dict) -> Dict[str, Any]:
        """Validate output against expected schema."""
        missing_keys = [
            key
            for key in expected_schema.keys()
            if not isinstance(output, dict) or key not in output
        ]
        return {
            "is_valid": len(missing_keys) == 0,
            "missing_keys": missing_keys,
            "expected_schema": expected_schema,
        }

    def validate_data(self, data: Any, validation_rules: Dict) -> Dict[str, Any]:
        """Validate data against rules."""
        errors: List[str] = []
        if validation_rules.get("required") and not data:
            errors.append("Data is required")
        if "type" in validation_rules:
            expected_type = validation_rules["type"]
            if expected_type == "dict" and not isinstance(data, dict):
                errors.append("Data must be a dict")
            if expected_type == "list" and not isinstance(data, list):
                errors.append("Data must be a list")
            if expected_type == "str" and not isinstance(data, str):
                errors.append("Data must be a string")
        return {"is_valid": len(errors) == 0, "errors": errors}

    def cross_validate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cross-validate results from multiple sources."""
        if not results:
            return {"status": "empty", "agreement": 0.0}

        decisions = [str(item.get("decision", "")) for item in results]
        dominant = max(set(decisions), key=decisions.count) if decisions else ""
        agreement = decisions.count(dominant) / len(decisions) if decisions else 0.0
        return {"status": "ok", "agreement": round(agreement, 3), "dominant": dominant}

    # ==================== Review Management ====================

    def set_review_criteria(self, criteria: Dict[str, Any]) -> None:
        """Set criteria for reviews."""
        self.review_criteria = dict(criteria)

    def get_review_criteria(self) -> Dict[str, Any]:
        """Get current review criteria."""
        return dict(self.review_criteria)

    def add_to_review_history(self, review: Dict[str, Any]) -> None:
        """Add review to history."""
        self.review_history.append(review)

    def get_review_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get review history."""
        if limit <= 0:
            return []
        return self.review_history[-limit:]

    def generate_review_report(self, review_id: str) -> Dict[str, Any]:
        """Generate detailed review report."""
        review = next(
            (
                item
                for item in self.review_history
                if item.get("review_id") == review_id
            ),
            None,
        )
        if not review:
            return {"status": "error", "error": f"Review not found: {review_id}"}

        return {
            "status": "success",
            "review_id": review_id,
            "report": review,
        }

    def approve_with_comments(
        self, item_id: str, comments: List[str]
    ) -> Dict[str, Any]:
        """Approve item with comments."""
        return {
            "item_id": item_id,
            "decision": "approved",
            "comments": comments,
        }

    def request_changes(
        self, item_id: str, changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Request changes for item."""
        return {
            "item_id": item_id,
            "decision": "changes_requested",
            "changes": changes,
        }
