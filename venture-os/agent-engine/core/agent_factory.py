# Agent Factory: Spawn and manage agents
from typing import Any, Dict, List, Optional, Type
import importlib.util
import inspect
import logging
import uuid
import time
import asyncio
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Keywords used to auto-detect agent types from task content
AGENT_TYPE_KEYWORDS = {
    "coding": [
        "code",
        "implement",
        "function",
        "class",
        "debug",
        "fix",
        "refactor",
        "program",
    ],
    "research": [
        "research",
        "find",
        "search",
        "investigate",
        "analyze",
        "discover",
        "learn",
    ],
    "review": ["review", "check", "validate", "audit", "inspect", "evaluate", "assess"],
    "runtime": ["run", "execute", "deploy", "start", "launch", "test"],
}

class AgentFactory:
    """Factory for creating, tracking, and managing agents."""

    def __init__(self, llm, memory_manager=None, tool_registry=None):
        self.llm = llm
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        self._agent_registry: Dict[str, Type[BaseAgent]] = {}
        self._active_agents: Dict[str, BaseAgent] = {}

    # ==================== Agent Type Registration ====================

    def register_agent_type(
        self, agent_type: str, agent_class: Type[BaseAgent]
    ) -> None:
        """Register an agent class for a specific type.

        Args:
            agent_type: String identifier for the agent type (e.g., "coding", "research").
            agent_class: The agent class to instantiate for this type.
        """
        self._agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")

    def get_registered_types(self) -> List[str]:
        """Get list of all registered agent types."""
        return list(self._agent_registry.keys())

    # ==================== Agent Creation ====================

    def spawn_agent(
        self,
        task: Dict[str, Any],
        agent_type: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> BaseAgent:
        """Spawn an agent for the given task.

        Args:
            task: Task definition dictionary.
            agent_type: Optional type override; auto-detected if not provided.
            config: Optional configuration for the agent.

        Returns:
            Instantiated agent ready for execution.

        Raises:
            ValueError: If agent type is not registered.
        """
        # Determine agent type if not provided
        if not agent_type:
            agent_type = self._determine_agent_type(task)

        # Validate agent type is registered
        if agent_type not in self._agent_registry:
            available = self.get_registered_types()
            raise ValueError(
                f"Unknown agent type '{agent_type}'. Available types: {available}"
            )

        # Generate unique agent ID
        agent_id = self._generate_agent_id(task)

        # Get the agent class and instantiate
        agent_class = self._agent_registry[agent_type]
        tools = self._get_tools_for_agent(agent_type)

        agent = agent_class(
            agent_id=agent_id,
            llm=self.llm,
            memory=None,  # Will be injected
            tools=tools,
            config=config,
        )

        # Inject dependencies (memory, additional tools)
        self._inject_dependencies(agent)

        # Track the active agent
        self._active_agents[agent_id] = agent
        logger.info(f"Spawned {agent_type} agent with ID: {agent_id}")

        return agent

    def spawn_multiple(
        self, tasks: List[Dict[str, Any]], config: Optional[Dict] = None
    ) -> List[BaseAgent]:
        """Spawn multiple agents for a list of tasks.

        Args:
            tasks: List of task definitions.
            config: Shared configuration for all agents.

        Returns:
            List of instantiated agents.
        """
        agents = []
        for task in tasks:
            agent_type = task.get("type")
            agent = self.spawn_agent(task, agent_type=agent_type, config=config)
            agents.append(agent)
        return agents

    def _determine_agent_type(self, task: Dict[str, Any]) -> str:
        """Determine the appropriate agent type based on task content.

        Args:
            task: Task definition to analyze.

        Returns:
            Agent type string.
        """
        # Check if task explicitly specifies type
        if "type" in task:
            return task["type"]

        # Analyze task description for keywords
        description = task.get("description", "").lower()
        name = task.get("name", "").lower()
        content = f"{description} {name}"

        # Score each agent type based on keyword matches
        scores: Dict[str, int] = {}
        for agent_type, keywords in AGENT_TYPE_KEYWORDS.items():
            if agent_type in self._agent_registry:
                score = sum(1 for kw in keywords if kw in content)
                if score > 0:
                    scores[agent_type] = score

        # Return the highest scoring type, or default to first registered
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])

        # Fallback to first registered type or 'coding' as default
        registered = self.get_registered_types()
        if registered:
            return registered[0]
        return "coding"

    def _generate_agent_id(self, task: Dict[str, Any]) -> str:
        """Generate a unique agent ID.

        Args:
            task: Task definition for context.

        Returns:
            Unique agent identifier string.
        """
        task_name = task.get("name", "task")
        # Sanitize task name for use in ID
        safe_name = "".join(c if c.isalnum() else "_" for c in task_name[:20])
        timestamp = int(time.time() * 1000)
        unique_suffix = uuid.uuid4().hex[:8]
        return f"agent_{safe_name}_{timestamp}_{unique_suffix}"

    # ==================== Active Agent Management ====================

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieve an active agent by ID."""
        return self._active_agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """Get all active agents."""
        return self._active_agents.copy()

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from active tracking.

        Args:
            agent_id: ID of the agent to remove.

        Returns:
            True if removed, False if not found.
        """
        if agent_id in self._active_agents:
            agent = self._active_agents.pop(agent_id)
            agent.stop()
            logger.info(f"Removed agent: {agent_id}")
            return True
        return False

    def stop_all_agents(self) -> None:
        """Stop all active agents."""
        for agent_id, agent in self._active_agents.items():
            agent.stop()
            logger.info(f"Stopped agent: {agent_id}")
        self._active_agents.clear()

    # ==================== Dependency Injection ====================

    def _inject_dependencies(self, agent: BaseAgent) -> None:
        """Inject memory and tools into an agent.

        Args:
            agent: Agent instance to configure.
        """
        # Inject memory manager
        if self.memory_manager:
            agent.memory = self.memory_manager

        # Additional tool injection could happen here
        # Tools are already set during instantiation from _get_tools_for_agent

    def _get_tools_for_agent(self, agent_type: str) -> List:
        """Get appropriate tools for an agent type.

        Args:
            agent_type: The type of agent.

        Returns:
            List of tool instances.
        """
        if not self.tool_registry:
            return []

        # Try to get agent-specific tools from registry
        if hasattr(self.tool_registry, "get_tools_for_type"):
            return self.tool_registry.get_tools_for_type(agent_type)

        # Fallback: return all available tools
        if hasattr(self.tool_registry, "get_all_tools"):
            return self.tool_registry.get_all_tools()

        return []

    # ==================== Dynamic Agent Generation ====================

    def spawn_dynamic_agent(
        self,
        use_case: str,
        agent_name: str,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict] = None,
    ) -> BaseAgent:
        """Use a CodingAgent to generate a brand-new agent class from a use-case
        description, save it to agents/, dynamically load it, register it, and
        return a running instance.

        Args:
            use_case:     Plain-English description of what the agent should do.
            agent_name:   Short snake_case name, e.g. "email_outreach".
            capabilities: Optional list of specific skills the agent should have.
            config:       Optional config passed to the spawned agent.

        Returns:
            A running instance of the newly generated agent.
        """
        from agents.coding_agent import CodingAgent

        # Step 1 — Generate the agent source file via CodingAgent
        logger.info(f"Generating new agent '{agent_name}' for use case: {use_case}")
        coder = CodingAgent(agent_id=f"meta_coder_{uuid.uuid4().hex[:8]}", llm=self.llm)
        result = coder.execute_task({
            "type": "generate_agent",
            "use_case": use_case,
            "agent_name": agent_name,
            "capabilities": capabilities or [],
        })

        if result.get("status") != "success":
            raise RuntimeError(f"CodingAgent failed to generate agent: {result}")

        file_path: str = result["file_path"]
        class_name: str = result["class_name"]
        logger.info(f"Agent source written to {file_path}")

        # Step 2 — Dynamically load the module
        module_name = f"agents.{agent_name}_agent"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        # Step 3 — Find the generated class (subclass of BaseAgent)
        agent_class: Optional[Type[BaseAgent]] = None
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                agent_class = obj
                break

        if agent_class is None:
            raise ImportError(
                f"No BaseAgent subclass found in generated file: {file_path}"
            )

        # Step 4 — Register and spawn
        self.register_agent_type(agent_name, agent_class)
        agent_id = f"agent_{agent_name}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        agent = agent_class(
            agent_id=agent_id,
            llm=self.llm,
            memory=None,
            tools=self._get_tools_for_agent(agent_name),
            config=config,
        )
        self._inject_dependencies(agent)
        self._active_agents[agent_id] = agent
        agent.start()

        logger.info(f"Dynamic agent '{class_name}' spawned with ID: {agent_id}")
        return agent
