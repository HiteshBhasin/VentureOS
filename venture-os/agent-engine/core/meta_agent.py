# Meta-Agent: goal analysis and agent roster planning only.
# All execution (spawning, running tasks, reporting) is handled by the Orchestrator.
import json
import logging
from typing import Any, Dict, List, Optional

from .llm_class import LLM
from models.llm_router import LLMRouter, ModelCapability

logger = logging.getLogger(__name__)


class Meta_agent:
    def __init__(self, llm: LLM, llm_router: Optional[LLMRouter] = None) -> None:
        """Responsible for goal analysis and agent roster planning only.
        All execution — spawning, running tasks, reporting — is handled by the Orchestrator.

        Args:
            llm:        Default LLM instance used when no router is configured.
            llm_router: Optional LLMRouter. When provided, each LLM call picks the
                        best registered endpoint for the task's capability before invoking.
        """
        self.llm = llm
        self.llm_router: Optional[LLMRouter] = llm_router

    def analyze_user_requirement(self, user_input: str) -> Dict[str, Any]:
        """Decompose a plain-English goal into a structured analysis dict.

        Returns a dict with keys:
            primary_goal, domain, constraints, required_capabilities, complexity_level
        """
        prompt = f"Analyze the user requirement and decompose it into smaller tasks: {user_input}"
        system_prompt = (
            "You are a helpful assistant that analyzes user requirements and decomposes them "
            "into smaller tasks. Return ONLY valid JSON with this exact structure:\n"
            "{\n"
            '  "primary_goal": "...",\n'
            '  "domain": "...",\n'
            '  "constraints": ["..."],\n'
            '  "required_capabilities": ["...", "..."],\n'
            '  "complexity_level": "low|medium|high"\n'
            "}\n"
            "No markdown, no explanation — JSON only."
        )
        llm = self._get_llm_for_task(ModelCapability.REASONING)
        response = llm.invoke(prompt, system_prompt)
        if not response:
            raise ValueError("LLM returned empty response for requirement analysis")
        return self._parse_json_response(response)

    def _plan_agent_roster(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ask the LLM to map required capabilities to concrete agent definitions.

        Returns a list of dicts, each with:
            agent_name   : snake_case identifier
            use_case     : 1-2 sentence description
            capabilities : list of method signatures e.g. "draft_email(recipient_info)"
            tasks        : list of concrete task dicts to execute immediately
        """
        prompt = (
            f"Given this goal analysis:\n{json.dumps(analysis, indent=2)}\n\n"
            "Design a roster of EXACTLY 3 to 5 specialized AI agents to accomplish this goal. "
            "Pick the most impactful capabilities — do not pad the list. "
            "For each agent, provide these fields:\n"
            "  agent_name   : short snake_case name (no spaces)\n"
            "  use_case     : 1-2 sentence plain-English description\n"
            '  capabilities : list of method signatures e.g. ["analyze_market_trends(market_data)", ...]\n'
            "  tasks        : list of 1-2 concrete task dicts. "
            'IMPORTANT: each task dict MUST have a "type" key whose value is the capability name '
            "EXACTLY as it appears before the opening parenthesis "
            '(e.g. if capability is "analyze_market_trends(market_data)", then type must be '
            '"analyze_market_trends"). Include any other relevant keys the task needs.\n\n'
            "Return ONLY a valid JSON array with no markdown fences."
        )
        system = (
            "You are an AI system architect. "
            "Output only a valid JSON array, no explanation, no markdown."
        )
        llm = self._get_llm_for_task(ModelCapability.REASONING)
        response = llm.invoke(prompt, system)
        if not response:
            raise ValueError("LLM returned empty response for roster planning")
        result = self._parse_json_response(response)
        if not isinstance(result, list):
            raise ValueError(f"Expected a JSON array from roster planning, got: {type(result)}")
        return result

    # ==================== Goal Decomposition ====================

    def decompose_goals(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert the analysis's required_capabilities into a flat task list."""
        tasks = []
        if isinstance(analysis, dict) and "required_capabilities" in analysis:
            for capability in analysis["required_capabilities"]:
                tasks.append(
                    {
                        "task_name": capability,
                        "agent_type": capability,
                        "assigned_agent": None,
                        "status": "pending",
                        "dependencies": [],
                    }
                )
        return tasks

    def create_task_graph(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return tasks sorted in topological dependency order."""
        return self._topological_sort(tasks)

    # ==================== Internal Helpers ====================

    def _get_llm_for_task(self, capability: Optional[ModelCapability] = None) -> LLM:
        """Return the best LLM for this task using the router, or fall back to self.llm.

        If a router is configured and has registered endpoints, it picks the endpoint
        whose capability matches (or the cheapest available endpoint as a default).
        A fresh LLM instance is created from the selected endpoint's model_id so the
        right provider is used for this specific call.
        """
        if not self.llm_router:
            return self.llm
        try:
            if capability:
                decision = self.llm_router.route_by_capability(capability)
            else:
                decision = self.llm_router.route({})
            endpoint = decision.endpoint
            logger.debug(
                f"LLMRouter selected '{endpoint.model_id}' "
                f"(reason={decision.reason}, capability={capability})"
            )
            return LLM(model=endpoint.model_id, temperature=self.llm.temperature)
        except Exception as exc:
            logger.warning(f"LLMRouter failed ({exc}), falling back to default LLM")
            return self.llm

    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks so that all dependencies appear before the tasks that need them."""

        task_map = {t["task_name"]: t for t in tasks}
        visited: set = set()
        stack: List[Dict[str, Any]] = []

        def dfs(task: Dict[str, Any]) -> None:
            visited.add(task["task_name"])
            for dep_name in task.get("dependencies", []):
                if dep_name not in visited and dep_name in task_map:
                    dfs(task_map[dep_name])
            stack.append(task)

        for task in tasks:
            if task["task_name"] not in visited:
                dfs(task)

        return stack[::-1]

    @staticmethod
    def _parse_json_response(response: str) -> Any:
        """Strip markdown fences if present, then parse and return JSON."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1]  # content between first pair of fences
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM response is not valid JSON: {exc}\nRaw response:\n{response[:500]}"
            ) from exc

