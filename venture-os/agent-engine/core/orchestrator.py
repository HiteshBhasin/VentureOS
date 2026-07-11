# Task scheduling & coordination
from typing import Any, AsyncGenerator, Dict, List, Optional
import json
import os
import re
import uuid
import logging
import asyncio

# @ need to add asyncio loop for scheduling and monitoring agents and tasks also need to add more specific exception handling for different failure scenarios (agent errors, task failures, budget breaches) and implement retry logic with backoff for transient issues. Also need to implement more detailed metrics collection and reporting for agent performance, task execution times, and resource usage to enable better monitoring and optimization of the system.


from .llm_class import LLM
from .agent_factory import AgentFactory
from .budget_manager import BudgetManager, BudgetType
from .events import EventBus, EventType, Event
from .task_graph import TaskGraph, TaskNode, TaskStatus
from memory.memory_manager import MemoryManager, MemoryType
from monitoring.metrics import MetricsCollector
from monitoring.tracer import Tracer
from models.llm_router import LLMRouter
from tools.tool_registry import ToolRegistry
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.review_agent import ReviewAgent
from agents.runtime_agent import RuntimeAgent

logger = logging.getLogger(__name__)

# Maps agent type → the most general task type that agent accepts
_AGENT_DEFAULT_TASK = {
    "research": "generate_report",
    "coding": "generate_code",
    "review": "review_code",
    "runtime": "run_code",
}

# Hard cap on agents spawned per request — prevents runaway LLM-driven expansion.
# Override globally via the MAX_AGENTS_PER_REQUEST env var, or per-instance via
# Orchestrator(config={"max_agents_per_request": N}).
_DEFAULT_MAX_AGENTS_PER_REQUEST = int(os.getenv("MAX_AGENTS_PER_REQUEST", "6"))


class Orchestrator:
    """
    Central coordinator for the agent-engine system.
    Manages task decomposition, agent lifecycle, execution, and resource tracking.
    """

    # ==================== INITIALIZATION & SETUP ====================

    def __init__(self, llm: LLM, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize all subsystems: LLM, agents, memory, budget, metrics, tracer, events.

        Args:
            llm: The LLM instance for agent communication.
            config: Optional configuration dictionary.
        """
        self.llm = llm
        self.config = config or {}

        # Core subsystems (initialized in initialize_subsystems)
        self.llm_router: Optional[LLMRouter] = None
        self.agent_factory: Optional[AgentFactory] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.budget_manager: Optional[BudgetManager] = None
        self.tool_registry: Optional[ToolRegistry] = None

        # Monitoring subsystems
        self.metrics: Optional[MetricsCollector] = None
        self.tracer: Optional[Tracer] = None

        # Event system
        self.event_bus: Optional[EventBus] = None

        # Task management
        self.task_graph: Optional[TaskGraph] = None

        # Agent tracking
        self._active_agents: Dict[str, Any] = {}
        self._agent_results: Dict[str, Any] = {}

        # Request tracking
        self._correlation_id: Optional[str] = None

        # Initialize all subsystems
        self.initialize_subsystems()
        self.register_default_agent_types()
        self.setup_event_subscriptions()

        self.current_objectives: str = ""
        logger.info("Orchestrator initialized successfully")

    def initialize_subsystems(self) -> None:
        """Set up LLM router, agent factory, memory manager, budget manager, metrics, tracer, event bus."""
        logger.info("Initializing orchestrator subsystems...")

        # Initialize event bus first (other subsystems may emit events)
        self.event_bus = EventBus()
        logger.debug("EventBus initialized")

        # Initialize monitoring subsystems
        service_name = self.config.get("service_name", "agent-engine")
        self.tracer = Tracer(service_name=service_name)
        self.metrics = MetricsCollector()
        logger.debug("Monitoring subsystems initialized (Tracer, MetricsCollector)")

        # Initialize memory manager
        memory_config = self.config.get("memory", {})
        self.memory_manager = MemoryManager(config=memory_config)
        self.memory_manager.initialize()
        logger.debug("MemoryManager initialized")

        # Initialize budget manager
        budget_config = self.config.get("budget", {})
        self.budget_manager = BudgetManager(config=budget_config)
        self._configure_default_budgets()
        logger.debug("BudgetManager initialized")

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_default_tools()
        logger.debug("ToolRegistry initialized")

        # Initialize LLM router
        router_config = self.config.get("llm_router", {})
        self.llm_router = LLMRouter(config=router_config)
        logger.debug("LLMRouter initialized")

        # Initialize agent factory (requires memory and tools)
        self.agent_factory = AgentFactory(
            llm=self.llm,
            memory_manager=self.memory_manager,
            tool_registry=self.tool_registry,
        )
        logger.debug("AgentFactory initialized")

        # Initialize task graph
        self.task_graph = TaskGraph()
        logger.debug("TaskGraph initialized")

        logger.info("All subsystems initialized successfully")

    def _configure_default_budgets(self) -> None:
        """Configure default budget limits from config or use defaults."""
        if not self.budget_manager:
            return

        default_limits = {
            BudgetType.TOKENS: self.config.get("max_tokens", 1_000_000),
            BudgetType.COST: self.config.get("max_cost", 100.0),
            BudgetType.REQUESTS: self.config.get("max_requests", 10_000),
            BudgetType.TIME: self.config.get("max_time_seconds", 3600),
        }

        for budget_type, limit in default_limits.items():
            self.budget_manager.set_budget_limit(budget_type, limit)

    def register_default_agent_types(self) -> None:
        """Register coding, research, review, and runtime agent types with the factory."""
        if not self.agent_factory:
            logger.warning("AgentFactory not initialized, skipping agent registration")
            return

        # Register all default agent types
        agent_types = {
            "coding": CodingAgent,
            "research": ResearchAgent,
            "review": ReviewAgent,
            "runtime": RuntimeAgent,
        }

        for agent_type, agent_class in agent_types.items():
            self.agent_factory.register_agent_type(agent_type, agent_class)

        logger.info(
            f"Registered {len(agent_types)} default agent types: {list(agent_types.keys())}"
        )

    def setup_event_subscriptions(self) -> None:
        """Subscribe to relevant events for orchestration (agent lifecycle, task completion, errors)."""
        if not self.event_bus:
            logger.warning("EventBus not initialized, skipping event subscriptions")
            return

        # Subscribe to agent lifecycle events
        self.event_bus.subscribe(EventType.AGENT_CREATED, self._on_agent_created)
        self.event_bus.subscribe(EventType.AGENT_STARTED, self._on_agent_started)
        self.event_bus.subscribe(EventType.AGENT_STOPPED, self._on_agent_stopped)
        self.event_bus.subscribe(EventType.AGENT_ERROR, self._on_agent_error)

        # Subscribe to task events
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)

        # Subscribe to budget events
        self.event_bus.subscribe(EventType.BUDGET_WARNING, self._on_budget_warning)
        self.event_bus.subscribe(EventType.BUDGET_EXCEEDED, self._on_budget_exceeded)

        logger.info("Event subscriptions configured")

    # ==================== EVENT HANDLERS ====================

    def _on_agent_created(self, event: Event) -> None:
        """Handle agent created event."""
        agent_id = event.data.get("agent_id")
        if agent_id:
            logger.debug(f"Agent created: {agent_id}")

    def _on_agent_started(self, event: Event) -> None:
        """Handle agent started event."""
        agent_id = event.data.get("agent_id")
        if agent_id:
            logger.debug(f"Agent started: {agent_id}")

    def _on_agent_stopped(self, event: Event) -> None:
        """Handle agent stopped event."""
        agent_id = event.data.get("agent_id")
        if agent_id:
            logger.debug(f"Agent stopped: {agent_id}")
            self.unregister_agent(agent_id)

    def _on_agent_error(self, event: Event) -> None:
        """Handle agent error event."""
        agent_id = event.data.get("agent_id")
        error = event.data.get("error")
        logger.error(f"Agent error: {agent_id} - {error}")

    def _on_task_completed(self, event: Event) -> None:
        """Handle task completed event."""
        task_id = event.data.get("task_id")
        result = event.data.get("result")
        if task_id:
            logger.info(f"Task completed: {task_id}")
            self.mark_task_completed(task_id, result)

    def _on_task_failed(self, event: Event) -> None:
        """Handle task failed event."""
        task_id = event.data.get("task_id")
        error = event.data.get("error")
        if task_id:
            logger.error(f"Task failed: {task_id} - {error}")
            self.mark_task_failed(
                task_id, Exception(str(error) if error else "Unknown error")
            )

    def _on_budget_warning(self, event: Event) -> None:
        """Handle budget warning event."""
        budget_type = event.data.get("budget_type")
        usage_percent = event.data.get("usage_percent")
        logger.warning(f"Budget warning: {budget_type} at {usage_percent}%")

    def _on_budget_exceeded(self, event: Event) -> None:
        """Handle budget exceeded event."""
        budget_type = event.data.get("budget_type")
        logger.error(f"Budget exceeded: {budget_type}")

    # ==================== REQUEST PROCESSING ====================

    def process_user_request(self, user_input: str) -> Dict[str, Any]:
        """Backbone entry point — the Orchestrator owns every execution step:
        1. Meta_agent analyses goal and plans the specialist roster.
        2. Orchestrator spawns each specialist agent via AgentFactory.
        3. Orchestrator executes every assigned task.
        4. Orchestrator compiles the final comprehensive report.
        5. Always identify the objectives, If only simple questions like : "what is your name?" or "how many stars are in the sky". Do now spawn agents just answer the simple question. 
        """
        if not self.validate_user_input(user_input):
            return {"status": "error", "message": "Invalid or empty user input"}

        self._correlation_id = self.get_correlation_id()
        logger.info(
            f"Processing request [{self._correlation_id}]: {user_input[:80]}..."
        )
        prior_context = ""
        if self.memory_manager:
            last = self.memory_manager.retrieve("last_run_summary")
            if last:
                prior_context = f"\n\nPrior run context:\n{last}"
        # inject into the user_input or the meta analysis prompt

        try:
            from .meta_agent import Meta_agent

            # ── Step 1: Meta_agent analyses the goal and decides which agents are needed ──
            meta = Meta_agent(llm=self.llm)
            
            analysis = meta.analyze_user_requirement(user_input + prior_context)
            roster = meta._plan_agent_roster(analysis)
            if roster:
                # use_case is always a plain-English string per the meta-agent schema
                self.current_objectives = analysis.get("primary_goal") or str(roster[0].get("use_case", ""))
                    
            logger.info(
                f"[{self._correlation_id}] Roster planned — "
                f"{len(roster)} agents: {[r['agent_name'] for r in roster]}"
            )

            # ── Step 2: Orchestrator spawns every specialist agent ─────────────────────
            if not self.agent_factory:
                raise RuntimeError("AgentFactory not initialized")

            max_agents = self.config.get(
                "max_agents_per_request", _DEFAULT_MAX_AGENTS_PER_REQUEST
            )
            if len(roster) > max_agents:
                logger.warning(
                    f"Roster has {len(roster)} agents — capping at {max_agents}"
                )
                roster = roster[:max_agents]

            spawned: Dict[str, Any] = {}
            for spec in roster:
                agent_name = spec["agent_name"]
                try:
                    agent = self.agent_factory.spawn_dynamic_agent(
                        use_case=spec["use_case"],
                        agent_name=agent_name,
                        capabilities=spec.get("capabilities", []),
                    )
                    self.inject_agent_dependencies(agent)
                    self.register_active_agent(agent)
                    spawned[agent_name] = {
                        "agent": agent,
                        "tasks": spec.get("tasks", []),
                    }
                    logger.info(
                        f"  Spawned {type(agent).__name__} (id={agent.agent_id})"
                    )
                except Exception as exc:
                    logger.error(f"  Failed to spawn '{agent_name}': {exc}")
                    spawned[agent_name] = {
                        "agent": None,
                        "tasks": [],
                        "error": str(exc),
                    }

            # ── Step 3: Orchestrator executes every assigned task ──────────────────────
            all_results: Dict[str, Any] = {}
            for agent_name, entry in spawned.items():
                if entry.get("error"):
                    all_results[agent_name] = {
                        "status": "error",
                        "error": entry["error"],
                    }
                    continue
                agent = entry["agent"]
                task_results = []
                for task in entry["tasks"]:
                    try:
                        result = agent.execute_task(task)
                        task_results.append({"task": task, "result": result})
                        logger.info(
                            f"  [{agent_name}] '{task.get('type')}' → {result.get('status')}"
                        )
                    except Exception as exc:
                        logger.error(
                            f"  [{agent_name}] '{task.get('type')}' failed: {exc}"
                        )
                        task_results.append(
                            {
                                "task": task,
                                "result": {"status": "error", "error": str(exc)},
                            }
                        )
                agent.complete()
                all_results[agent_name] = {
                    "agent_id": agent.agent_id,
                    "agent_class": type(agent).__name__,
                    "status": agent.status,
                    "task_results": task_results,
                }
                self.unregister_agent(agent.agent_id)

            # ── Step 4: Orchestrator compiles the final comprehensive report ───────────
            report = self.compile_final_report(user_input, analysis, all_results)
            project_path = self._write_project_output(report, all_results)
            # after compiling report
            if self.memory_manager:
                self.memory_manager.store(
                    key=f"run:{self._correlation_id}",
                    value={"goal": user_input, "report": report},
                    memory_type=MemoryType.EPISODIC,
                )
                self.memory_manager.store(
                    key="last_run_summary",
                    value=report,
                    memory_type=MemoryType.SHORT_TERM,
                )

            return {
                "status": "success",
                "correlation_id": self._correlation_id,
                "goal": user_input,
                "analysis": analysis,
                "agents_spawned": [
                    e["agent"].agent_id for e in spawned.values() if e.get("agent")
                ],
                "agent_results": all_results,
                "report": report,
                "project_path": project_path,
            }

        except Exception as exc:
            logger.error(
                f"Error processing request [{self._correlation_id}]: {exc}",
                exc_info=True,
            )

            return {
                "status": "error",
                "message": str(exc),
                "correlation_id": self._correlation_id,
            }

    def validate_user_input(self, user_input: str) -> bool:
        """Validate and sanitize user request before processing."""
        if not user_input or not isinstance(user_input, str):
            return False
        sanitized = user_input.strip()
        if not sanitized:
            return False
        if len(sanitized) > 10_000:
            logger.warning("User input exceeds maximum allowed length (10000 chars)")
            return False
        return True

    def create_execution_plan(self, user_input: str) -> Dict[str, Any]:
        """Analyze requirement, decompose goals, build task graph DAG."""
        from .meta_agent import Meta_agent

        meta = Meta_agent(self.llm)
        analysis = meta.analyze_user_requirement(user_input)
        tasks = meta.decompose_goals(analysis)

        if not self.task_graph:
            self.task_graph = TaskGraph()
        else:
            self.task_graph.clear()

        for i, task_data in enumerate(tasks):
            node = TaskNode(
                task_id=f"task_{i + 1}",
                name=task_data.get("task_name", f"Task {i + 1}"),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", []),
                metadata={"agent_type": task_data.get("agent_type", "research")},
            )
            self.task_graph.add_task(node)

        logger.info(f"Created execution plan with {len(tasks)} tasks")
        return {
            "analysis": analysis,
            "task_count": len(tasks),
            "task_graph": self.task_graph.to_dict(),
        }

    # ==================== TASK GRAPH MANAGEMENT ====================

    def execute_task_graph(self, task_graph: Any) -> Dict[str, Any]:
        """Execute tasks in topological order respecting dependencies."""
        if not task_graph:
            return {"status": "error", "message": "No task graph provided"}

        results: Dict[str, Any] = {}
        max_iterations = len(task_graph._nodes) * 2 + 1  # Safety limit
        iterations = 0

        while not task_graph.is_complete() and iterations < max_iterations:
            ready_tasks = self.get_executable_tasks(task_graph)
            if not ready_tasks:
                break  # No progress possible — either done or deadlocked

            for task_node in ready_tasks:
                if not self.check_budget_before_execution(task_node):
                    self.mark_task_failed(
                        task_node.task_id, Exception("Budget exceeded")
                    )
                    continue
                try:
                    agent = self.spawn_and_configure_agent(task_node)
                    self.register_active_agent(agent)
                    result = self.execute_agent_task(agent, task_node)
                    results[task_node.task_id] = result
                    self.mark_task_completed(task_node.task_id, result)
                except Exception as exc:
                    logger.error(f"Task {task_node.task_id} failed: {exc}")
                    self.mark_task_failed(task_node.task_id, exc)

            iterations += 1

        return self.aggregate_task_results(task_graph, results)

    def get_executable_tasks(self, task_graph: Any) -> List[Any]:
        """Find tasks with all dependencies satisfied that are ready to execute."""
        if not task_graph:
            return []
        return task_graph.get_ready_tasks()

    def update_task_status(
        self, task_id: str, status: str, result: Optional[Any] = None
    ) -> None:
        """Update task status and propagate to dependent tasks."""
        if not self.task_graph:
            return
        self.task_graph.update_task(task_id, {"status": status})
        if result is not None:
            self.task_graph.update_task(task_id, {"result": result})

    def mark_task_completed(self, task_id: str, result: Any) -> None:
        """Mark task as completed and update dependency graph."""
        if self.task_graph:
            self.task_graph.mark_task_completed(task_id, result)
            self.store_shared_result(task_id, result)
            logger.info(f"Task {task_id} marked completed")

    def mark_task_failed(self, task_id: str, error: Exception) -> None:
        """Mark task as failed and handle dependent tasks."""
        if self.task_graph:
            self.task_graph.mark_task_failed(task_id, str(error))
            affected = self.task_graph.propagate_failure(task_id)
            if affected:
                logger.warning(f"Task {task_id} failure propagated to: {affected}")
            logger.error(f"Task {task_id} marked failed: {error}")

    # ==================== AGENT SPAWNING & MANAGEMENT ====================

    def _spawn_from_spec(self, spec: Dict[str, Any]) -> Any:
        """Spawn a dynamic agent from a roster spec dict, inject dependencies, register it."""
        if not self.agent_factory:
            raise RuntimeError("AgentFactory not initialized")
        agent = self.agent_factory.spawn_dynamic_agent(
            use_case=spec["use_case"],
            agent_name=spec["agent_name"],
            capabilities=spec.get("capabilities", []),
        )
        self.inject_agent_dependencies(agent)
        self.register_active_agent(agent)
        return agent

    def spawn_and_configure_agent(self, task: Any) -> Any:
        """Spawn agent via factory, inject dependencies (memory, tools, events), return agent."""
        if not self.agent_factory:
            raise RuntimeError("AgentFactory not initialized")
        task_dict = (
            task.__dict__
            if hasattr(task, "__dict__")
            else task if isinstance(task, dict) else {"name": str(task)}
        )
        agent_type = (
            task.metadata.get("agent_type", None)
            if hasattr(task, "metadata") and isinstance(task.metadata, dict)
            else None
        )
        agent = self.agent_factory.spawn_agent(task_dict, agent_type=agent_type)
        self.inject_agent_dependencies(agent)
        return agent

    def inject_agent_dependencies(self, agent: Any) -> None:
        """Inject memory manager, tool registry, event bus, and state machine into agent."""
        if self.memory_manager and hasattr(agent, "memory"):
            agent.memory = self.memory_manager
        if self.event_bus and hasattr(agent, "set_event_bus"):
            agent.set_event_bus(self.event_bus)
        if self.tool_registry and hasattr(agent, "tool_registry"):
            agent.tool_registry = self.tool_registry

    def register_active_agent(self, agent: Any) -> None:
        """Add agent to active registry for tracking."""
        agent_id = getattr(agent, "agent_id", str(id(agent)))
        self._active_agents[agent_id] = agent
        logger.debug(f"Registered active agent: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """Remove agent from active registry."""
        self._active_agents.pop(agent_id, None)
        logger.debug(f"Unregistered agent: {agent_id}")

    def get_agent_by_id(self, agent_id: str) -> Optional[Any]:
        """Retrieve agent instance by ID."""
        return self._active_agents.get(agent_id)

    def get_active_agents(self) -> List[Any]:
        """Return list of all currently active agents."""
        return list(self._active_agents.values())

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Return current state, metrics, and info for an agent."""
        agent = self._active_agents.get(agent_id)
        if not agent:
            return {"agent_id": agent_id, "status": "not_found"}
        return {
            "agent_id": agent_id,
            "agent_type": getattr(agent, "agent_type", "unknown"),
        }

    def track_active_agents(self) -> None:
        """Monitor running agents for timeouts and health."""
        for agent_id, agent in list(self._active_agents.items()):
            if hasattr(agent, "is_finished") and agent.is_finished():
                logger.info(f"Agent {agent_id} has finished; unregistering")
                self.unregister_agent(agent_id)

    # ==================== AGENT EXECUTION ====================

    def execute_agent_task(self, agent: Any, task: Any) -> Any:
        """Execute task with agent: start trace, invoke, monitor, record metrics.

        ``task`` can be either a TaskNode (task-graph path) or a plain dict
        (roster path, which already carries the correct ``type`` field).
        """
        import time

        agent_id = getattr(agent, "agent_id", str(id(agent)))
        task_id = (
            task.get("type", str(task))
            if isinstance(task, dict)
            else getattr(task, "task_id", str(task))
        )
        trace = self.start_execution_trace(task)
        start = time.monotonic()
        try:
            self.start_agent(agent)
            if isinstance(task, dict):
                # Roster path — task dict already has the correct type/description
                task_input = task
            else:
                # Task-graph path — reconstruct task_input from TaskNode attributes
                agent_type = (
                    task.metadata.get("agent_type", "research")
                    if hasattr(task, "metadata") and isinstance(task.metadata, dict)
                    else "research"
                )
                task_type = _AGENT_DEFAULT_TASK.get(agent_type, "generate_report")
                description = getattr(task, "description", "") or getattr(
                    task, "name", ""
                )
                task_input = {
                    "type": task_type,
                    "description": description,
                    "prompt": description,
                    "topic": description,
                    "code": description,
                }
            result = agent.execute_task(task_input)
            duration = time.monotonic() - start
            self.record_task_metrics(task, duration, success=True)
            self.handle_agent_completion(agent, result)
            self.end_execution_trace(trace, "success")
            self._agent_results[agent_id] = result
            return result
        except Exception as exc:
            duration = time.monotonic() - start
            self.record_task_metrics(task, duration, success=False, error=str(exc))
            self.handle_agent_failure(agent, exc)
            self.end_execution_trace(trace, "error")
            raise

    def start_agent(self, agent: Any) -> None:
        """Transition agent to running state."""
        if hasattr(agent, "set_state"):
            from .state_machine import AgentState

            agent.set_state(AgentState.RUNNING)
        elif hasattr(agent, "start"):
            agent.start()

    def pause_agent(self, agent_id: str) -> None:
        """Pause a running agent."""
        agent = self.get_agent_by_id(agent_id)
        if agent and hasattr(agent, "set_state"):
            from .state_machine import AgentState

            agent.set_state(AgentState.PAUSED)

    def resume_agent(self, agent_id: str) -> None:
        """Resume a paused agent."""
        agent = self.get_agent_by_id(agent_id)
        if agent and hasattr(agent, "set_state"):
            from .state_machine import AgentState

            agent.set_state(AgentState.RUNNING)

    def stop_agent(self, agent_id: str) -> None:
        """Stop an agent gracefully."""
        agent = self.get_agent_by_id(agent_id)
        if agent:
            if hasattr(agent, "stop"):
                agent.stop()
            self.unregister_agent(agent_id)

    def reset_agent(self, agent_id: str) -> None:
        """Reset agent to initial state."""
        agent = self.get_agent_by_id(agent_id)
        if agent and hasattr(agent, "set_state"):
            from .state_machine import AgentState

            agent.set_state(AgentState.IDLE)

    # ==================== COMPLETION & FAILURE HANDLING ====================

    def handle_agent_completion(self, agent: Any, result: Any) -> None:
        """Collect metrics, record outcome, update task graph, emit event."""
        agent_id = getattr(agent, "agent_id", str(id(agent)))
        self._agent_results[agent_id] = result
        self.publish_event(
            EventType.AGENT_STOPPED.value,
            {"agent_id": agent_id, "result": result},
        )
        logger.info(f"Agent {agent_id} completed successfully")

    def handle_agent_failure(self, agent: Any, error: Exception) -> None:
        """Log error, check retry budget, retry or escalate, emit failure event."""
        agent_id = getattr(agent, "agent_id", str(id(agent)))
        logger.error(f"Agent {agent_id} failed: {error}")
        self.publish_event(
            EventType.AGENT_ERROR.value,
            {"agent_id": agent_id, "error": str(error)},
        )

    def should_retry_task(self, task: Any, error: Exception) -> bool:
        """Determine if task should be retried based on error type and retry budget."""
        max_retries = self.config.get("max_task_retries", 2)
        retry_count = getattr(task, "metadata", {}).get("retry_count", 0)
        # Don't retry budget exceeded errors
        if "budget" in str(error).lower():
            return False
        return retry_count < max_retries

    def retry_task(self, task: Any) -> None:
        """Retry a failed task with fresh agent."""
        if hasattr(task, "metadata"):
            task.metadata["retry_count"] = task.metadata.get("retry_count", 0) + 1
        if hasattr(task, "status"):
            from .task_graph import TaskStatus

            task.status = TaskStatus.PENDING
        logger.info(f"Retrying task: {getattr(task, 'task_id', task)}")

    def escalate_failure(self, task: Any, error: Exception) -> None:
        """Escalate unrecoverable failure to user or supervisor."""
        task_id = getattr(task, "task_id", str(task))
        logger.critical(f"Escalating failure for task {task_id}: {error}")
        self.publish_event(
            EventType.TASK_FAILED.value,
            {"task_id": task_id, "error": str(error), "escalated": True},
        )

    # ==================== DEPENDENCY ERROR HANDLING ====================

    def handle_dependency_error(self, failed_task: Any) -> None:
        """Mark dependent tasks as skipped/failed, log issue, update UI."""
        task_id = getattr(failed_task, "task_id", str(failed_task))
        self.propagate_failure_to_dependents(task_id)
        logger.warning(f"Dependency error for task {task_id}: propagated to dependents")

    def propagate_failure_to_dependents(self, task_id: str) -> None:
        """Mark all tasks depending on failed task as blocked."""
        if self.task_graph:
            affected = self.task_graph.propagate_failure(task_id)
            logger.warning(f"Blocked tasks after {task_id} failure: {affected}")

    def get_dependent_tasks(self, task_id: str) -> List[Any]:
        """Get all tasks that depend on the given task."""
        if not self.task_graph:
            return []
        return [
            self.task_graph.get_task(tid)
            for tid in self.task_graph.get_dependents(task_id)
            if self.task_graph.get_task(tid)
        ]

    # ==================== CONTEXT & COMMUNICATION ====================

    def manage_agent_context(self) -> None:
        """Coordinate context sharing between agents."""
        for agent_id, result in self._agent_results.items():
            if result is not None:
                self.store_in_memory(f"agent_result:{agent_id}", result)

    def share_context_between_agents(
        self, source_agent_id: str, target_agent_id: str, context_key: str
    ) -> None:
        """Transfer context data from one agent to another."""
        value = self.retrieve_from_memory(f"agent_result:{source_agent_id}")
        if value is not None:
            self.store_in_memory(f"context:{target_agent_id}:{context_key}", value)

    def store_shared_result(self, task_id: str, result: Any) -> None:
        """Store task result in memory for dependent tasks."""
        self.store_in_memory(f"task_result:{task_id}", result)

    def retrieve_dependency_results(self, task: Any) -> Dict[str, Any]:
        """Retrieve results from all dependency tasks."""
        deps = getattr(task, "dependencies", [])
        return {
            dep_id: self.retrieve_from_memory(f"task_result:{dep_id}")
            for dep_id in deps
        }

    def get_correlation_id(self) -> str:
        """Get or create correlation ID for request tracing."""
        if not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
        return self._correlation_id

    # ==================== EVENT MANAGEMENT ====================

    def publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event via event bus with correlation ID."""
        if not self.event_bus:
            return
        try:
            evt_enum = EventType(event_type)
        except ValueError:
            logger.warning(f"Unknown event type: {event_type}")
            return
        from datetime import datetime

        event = Event(
            event_type=evt_enum,
            source="Orchestrator",
            timestamp=datetime.now(),
            data={**data, "correlation_id": self._correlation_id},
            correlation_id=self._correlation_id,
        )
        self.event_bus.publish(event)

    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process incoming events from subsystems."""
        logger.debug(f"Handling event {event_type}: {data}")
        self.publish_event(event_type, data)

    def subscribe_to_events(self, event_types: List[str], handler: Any) -> None:
        """Subscribe to specific event types with handler."""
        if not self.event_bus:
            return
        for et in event_types:
            try:
                self.event_bus.subscribe(EventType(et), handler)
            except ValueError:
                logger.warning(f"Cannot subscribe to unknown event type: {et}")

    # ==================== RESOURCE & BUDGET MANAGEMENT ====================

    def check_budget_before_execution(self, task: Any) -> bool:
        """Check if sufficient budget remains for task execution."""
        if not self.budget_manager:
            return True
        estimated_tokens = (
            task.metadata.get("estimated_tokens", 1000)
            if hasattr(task, "metadata")
            else 1000
        )
        return self.check_token_budget(estimated_tokens) and self.check_request_limit()

    def enforce_budget_constraints(self) -> None:
        """Check token, cost, request, and time limits."""
        if not self.budget_manager:
            return
        self.budget_manager.check_alerts()
        self.budget_manager.check_reset_periods()

    def check_token_budget(self, estimated_tokens: int) -> bool:
        """Verify token budget is not exceeded."""
        if not self.budget_manager:
            return True
        return self.budget_manager.has_budget_for_tokens(estimated_tokens)

    def check_cost_budget(self, estimated_cost: float) -> bool:
        """Verify cost budget is not exceeded."""
        if not self.budget_manager:
            return True
        return self.budget_manager.has_budget_for_cost(estimated_cost)

    def check_request_limit(self) -> bool:
        """Verify request limit is not exceeded."""
        if not self.budget_manager:
            return True
        return self.budget_manager.has_budget_for_request()

    def check_time_limit(self, task: Any) -> bool:
        """Verify execution time is within limit."""
        if not self.budget_manager:
            return True
        estimated_seconds = (
            task.metadata.get("estimated_time_seconds", 60)
            if hasattr(task, "metadata")
            else 60
        )
        return self.budget_manager.has_budget_for_time(estimated_seconds)

    def track_resource_usage(self) -> None:
        """Collect metrics continuously: tokens, costs, success rates."""
        if self.budget_manager:
            self.budget_manager.check_reset_periods()
        if self.metrics:
            self.metrics.record_gauge("active_agents", len(self._active_agents))

    def record_token_usage(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        """Record token usage for metrics."""
        if self.budget_manager:
            self.budget_manager.record_token_usage(
                prompt_tokens, completion_tokens, model
            )

    def record_cost(self, source: str, amount: float) -> None:
        """Record cost expenditure."""
        if self.budget_manager:
            self.budget_manager.record_cost(amount, source)

    # ==================== METRICS & TRACING ====================

    def start_execution_trace(self, task: Any) -> Any:
        """Start distributed trace for task execution."""
        if not self.tracer:
            return None
        task_id = getattr(task, "task_id", str(task))
        return self.tracer.start_span(f"task:{task_id}")

    def end_execution_trace(self, trace: Any, status: str) -> None:
        """End trace and record final status."""
        if trace and hasattr(trace, "set_status") and hasattr(trace, "end"):
            from monitoring.tracer import SpanStatus

            span_status = SpanStatus.OK if status == "success" else SpanStatus.ERROR
            trace.set_status(span_status)
            trace.end()

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Start a new span within current trace."""
        if not self.tracer:
            return None
        return self.tracer.start_span(name, attributes=attributes)

    def record_task_metrics(
        self, task: Any, duration: float, success: bool, error: Optional[str] = None
    ) -> None:
        """Record task execution metrics."""
        if not self.metrics:
            return
        task_id = getattr(task, "task_id", str(task))
        self.metrics.increment_counter("tasks_completed" if success else "tasks_failed")

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get current execution metrics summary."""
        base: Dict[str, Any] = {
            "active_agents": len(self._active_agents),
            "completed_results": len(self._agent_results),
        }
        if self.task_graph:
            base["task_progress"] = self.task_graph.get_progress()
        if self.budget_manager:
            base["budget"] = self.budget_manager.get_budget_status()
        if self.metrics:
            base["metrics"] = self.metrics.get_summary()
        return base

    # ==================== RESULT AGGREGATION ====================

    def aggregate_task_results(
        self, task_graph: Any, agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect outputs from all agents, organize by dependency, generate summary."""
        if not task_graph:
            return {"status": "error", "message": "No task graph"}
        progress = task_graph.get_progress()
        ordered_ids = task_graph.topological_sort()
        ordered_results = {
            tid: agent_results.get(tid) for tid in ordered_ids if tid in agent_results
        }
        failed_tasks = [
            t.task_id
            for t in task_graph.get_all_tasks()
            if hasattr(t, "status") and t.status.value == "failed"
        ]
        return {
            "status": "complete" if task_graph.is_complete() else "partial",
            "progress": progress,
            "results": ordered_results,
            "failed_tasks": failed_tasks,
        }

    def generate_execution_report(self) -> Dict[str, Any]:
        """Generate report: timeline, resource usage, cost breakdown, traces."""
        from datetime import datetime

        report: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "correlation_id": self._correlation_id,
            "metrics": self.get_execution_metrics(),
        }
        if self.budget_manager:
            report["budget"] = self.budget_manager.generate_budget_report()
        if self.task_graph:
            report["task_summary"] = self.task_graph.get_progress()
        return report

    def generate_task_summary(self, task_results: Dict[str, Any]) -> str:
        """Generate human-readable summary of task execution."""
        lines = ["=== Task Execution Summary ==="]
        for task_id, result in task_results.items():
            status = "✓" if result is not None else "✗"
            lines.append(f"  {status} {task_id}: {str(result)[:80]}")
        return "\n".join(lines)

    def compile_final_report(
        self, goal: str, analysis: Dict[str, Any], results: Dict[str, Any]
    ) -> str:
        """Synthesize all specialist agent outputs into one comprehensive report."""
        agent_summaries: List[str] = []
        for agent_name, agent_data in results.items():
            if agent_data.get("status") == "error":
                agent_summaries.append(
                    f"**{agent_name}**: FAILED — {agent_data.get('error', 'unknown error')}"
                )
                continue
            task_outputs: List[str] = []
            for tr in agent_data.get("task_results", []):
                task_type = tr.get("task", {}).get("type", "task")
                res = tr.get("result") or {}
                # Dynamically-generated agents aren't guaranteed to wrap their
                # output in a dict — some capability methods return the raw
                # string from _invoke_llm() directly.
                if isinstance(res, dict):
                    output = (
                        res.get("output")
                        or res.get("result")
                        or res.get("report")
                        or res.get("code")
                        or str(res)
                    )
                else:
                    output = res
                task_outputs.append(f"  - [{task_type}]: {str(output)[:800]}")
            agent_summaries.append(
                f"**{agent_name}** ({agent_data.get('agent_class', '')}):\n"
                + "\n".join(task_outputs)
            )

        agents_block = (
            "\n\n".join(agent_summaries) if agent_summaries else "(no agent output)"
        )
        prompt = (
            f"You are the Chief AI Officer. Your specialist agents have completed their work.\n\n"
            f"ORIGINAL GOAL:\n{goal}\n\n"
            f"GOAL ANALYSIS:\n{json.dumps(analysis, indent=2)}\n\n"
            f"SPECIALIST AGENT OUTPUTS:\n{agents_block}\n\n"
            "Write a comprehensive, professional final report that:\n"
            "1. Opens with an **Executive Summary** (3-4 sentences)\n"
            "2. Has a dedicated section for each specialist agent's key findings\n"
            "3. Closes with **Integrated Recommendations & Next Steps**\n"
            "Use clear Markdown formatting with headers and bullet points."
        )
        system = (
            "You are a senior executive synthesizing specialist AI reports into a final deliverable. "
            "Write clearly, concisely, and professionally. Use Markdown headers."
        )
        try:
            return self.llm.invoke(prompt, system) or self._fallback_report(
                goal, agent_summaries
            )
        except Exception as exc:
            logger.warning(
                f"compile_final_report LLM call failed ({exc}); using fallback."
            )
            return self._fallback_report(goal, agent_summaries)

    _LANG_EXTENSIONS = {
        "python": "py", "py": "py",
        "javascript": "js", "js": "js",
        "typescript": "ts", "ts": "ts",
        "bash": "sh", "sh": "sh", "shell": "sh",
        "sql": "sql",
        "json": "json",
        "yaml": "yaml", "yml": "yaml",
        "html": "html",
        "css": "css",
    }

    _CODE_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)

    @staticmethod
    def _collect_strings(obj: Any) -> List[str]:
        """Recursively collect every string value from an arbitrarily-shaped
        result payload. Dynamically-generated agents return their output
        under whatever key name the LLM happened to pick (``implementation``,
        ``code``, ``output``, ``result``, ...) — scanning by a fixed key
        allowlist misses most of them, so this scans every string in the
        structure instead.
        """
        out: List[str] = []
        if isinstance(obj, str):
            out.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                out.extend(Orchestrator._collect_strings(v))
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                out.extend(Orchestrator._collect_strings(v))
        return out

    def _extract_code_files(self, agent_results: Dict[str, Any]) -> Dict[str, str]:
        """Best-effort extraction of real source code from agent outputs.

        Two sources: (1) the raw ``source`` field CodingAgent now preserves
        alongside its sandboxed execution result, and (2) fenced code blocks
        (```lang ... ```) found anywhere in any agent's result payload.
        Agents that only produced prose with no fenced code yield nothing
        here — this can't invent code that was never generated.
        """
        files: Dict[str, str] = {}
        seen_snippets: set = set()

        def _safe_stem(*parts: str) -> str:
            raw = "_".join(p for p in parts if p)
            return re.sub(r"[^\w.-]+", "_", raw).strip("_") or "output"

        for agent_name, agent_data in agent_results.items():
            if not isinstance(agent_data, dict):
                continue
            for i, tr in enumerate(agent_data.get("task_results", [])):
                task_type = (tr.get("task") or {}).get("type", "task")
                result = tr.get("result")
                if result is None:
                    continue

                if isinstance(result, dict):
                    source = result.get("source")
                    if isinstance(source, str) and source.strip():
                        ext = self._LANG_EXTENSIONS.get(
                            str(result.get("language", "python")).lower(), "txt"
                        )
                        stem = _safe_stem(agent_name, task_type, str(i))
                        files[f"{stem}.{ext}"] = source
                        seen_snippets.add(source.strip())

                for text in self._collect_strings(result):
                    for j, m in enumerate(self._CODE_FENCE_RE.finditer(text)):
                        lang, code = m.group(1).lower(), m.group(2)
                        if not code.strip() or code.strip() in seen_snippets:
                            continue
                        seen_snippets.add(code.strip())
                        ext = self._LANG_EXTENSIONS.get(lang, "txt")
                        stem = _safe_stem(agent_name, task_type, f"{i}_{j}")
                        files[f"{stem}.{ext}"] = code

        return files

    def _write_project_output(
        self, report: str, agent_results: Dict[str, Any]
    ) -> Optional[str]:
        """Materialize this run's output as a project folder on disk, so
        completing a task leaves behind more than a DB row — a real
        directory the user can open, under agent-engine/generated_projects/.

        Any actual source code the agents produced is written under src/ as
        real files. When the roster never generated real code (common for
        analysis-style agents that only return prose), src/ is simply empty
        — this materializes what was produced, it doesn't fabricate code.
        """
        try:
            from tools.file_handler import FileHandler

            root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "generated_projects"
            )
            project_dir = os.path.join(root, self._correlation_id or "run")
            fh = FileHandler()
            fh.create_directory(project_dir)
            fh.write(os.path.join(project_dir, "report.md"), report)
            fh.write_json(os.path.join(project_dir, "results.json"), agent_results)

            code_files = self._extract_code_files(agent_results)
            for filename, content in code_files.items():
                fh.write(os.path.join(project_dir, "src", filename), content)
            if code_files:
                logger.info(f"Extracted {len(code_files)} source file(s) into src/")
            else:
                logger.info(
                    "No extractable source code in agent output — src/ not created"
                )

            abs_path = os.path.abspath(project_dir)
            logger.info(f"Project output written to {abs_path}")
            return abs_path
        except Exception as exc:
            logger.warning(f"Failed to write project output to disk: {exc}")
            return None

    def _fallback_report(self, goal: str, agent_summaries: List[str]) -> str:
        """Plain-text report used when the LLM is unavailable (e.g. rate-limited)."""
        lines = [
            "# Execution Report (auto-generated — LLM unavailable)\n",
            f"**Goal**: {goal}\n",
            "## Agent Outputs\n",
        ]
        lines.extend(agent_summaries or ["*(no agent output)*"])
        return "\n".join(lines)

    def store_execution_results(self, results: Dict[str, Any]) -> None:
        """Persist execution results to memory."""
        if self.memory_manager:
            correlation_id = self.get_correlation_id()
            self.store_in_memory(f"execution:{correlation_id}", results)

    # ==================== TOOL MANAGEMENT ====================

    def register_tool(self, tool: Any, handler) -> None:
        """Register a tool with the tool registry."""
        if self.tool_registry:
            self.tool_registry.register(tool, handler)

    def get_available_tools(self) -> List[Any]:
        """Get list of all available tools."""
        if not self.tool_registry:
            return []
        if hasattr(self.tool_registry, "get_all_tools"):
            return self.tool_registry.get_all_tools()
        return []

    def _register_default_tools(self) -> None:
        """Wire real external tools into the registry so agents can call
        ``self.use_tool(...)`` for facts instead of only ever reciting
        training data via ``_invoke_llm``. Handlers return plain JSON-safe
        dicts, not raw dataclasses, since task results get persisted as
        JSONB.
        """
        if not self.tool_registry:
            return
        from tools.tool_registry import ToolCategory, ToolDefinition, ToolParameter
        from tools.web_search import WebSearch

        web_search = WebSearch(config=self.config.get("web_search", {}))

        def _web_search_handler(query: str, num_results: int = 5) -> Dict[str, Any]:
            response = web_search.search(query, num_results=num_results)
            return {
                "query": response.query,
                "engine": response.engine.value,
                "total_results": response.total_results,
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "snippet": r.snippet,
                        "source": r.source,
                    }
                    for r in response.results
                ],
            }

        self.tool_registry.register(
            ToolDefinition(
                name="web_search",
                description=(
                    "Search the live web for current, factual information. Use "
                    "this instead of guessing whenever a task needs up-to-date "
                    "or real-world facts — news, current events, specific "
                    "companies/products, prices, etc."
                ),
                category=ToolCategory.WEB,
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="The search query",
                        required=True,
                    ),
                    ToolParameter(
                        name="num_results",
                        type="integer",
                        description="Maximum number of results to return",
                        required=False,
                        default=5,
                    ),
                ],
            ),
            handler=_web_search_handler,
        )
        logger.info("Registered default tools: web_search")

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute tool via tool executor with safety checks."""
        if not self.validate_tool_invocation(tool_name, args):
            raise ValueError(f"Invalid tool invocation: {tool_name}")
        if self.tool_registry and hasattr(self.tool_registry, "execute"):
            return self.tool_registry.execute(tool_name, args)
        raise RuntimeError(f"Tool '{tool_name}' not available")

    def validate_tool_invocation(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Validate tool invocation parameters."""
        if not tool_name or not isinstance(tool_name, str):
            return False
        if not isinstance(args, dict):
            return False
        return True

    # ==================== MEMORY MANAGEMENT ====================

    def store_in_memory(self, key: str, value: Any, memory_type: str = "cache") -> None:
        """Store data in specified memory tier (cache, vector, structured)."""
        if not self.memory_manager:
            return
        if hasattr(self.memory_manager, "store"):
            self.memory_manager.store(key, value, memory_type=memory_type)

    def retrieve_from_memory(
        self, key: str, memory_type: str = "cache"
    ) -> Optional[Any]:
        """Retrieve data from specified memory tier."""
        if not self.memory_manager:
            return None
        if hasattr(self.memory_manager, "retrieve"):
            return self.memory_manager.retrieve(key, memory_type=memory_type)
        return None

    def search_memory(self, query: str, limit: int = 10) -> List[Any]:
        """Search memory using semantic similarity."""
        if not self.memory_manager:
            return []
        if hasattr(self.memory_manager, "search"):
            return self.memory_manager.search(query, limit=limit)
        return []

    def clear_task_memory(self, task_id: str) -> None:
        """Clear memory associated with a specific task."""
        if self.memory_manager and hasattr(self.memory_manager, "delete"):
            self.memory_manager.delete(f"task_result:{task_id}")

    # ==================== SHUTDOWN & CLEANUP ====================

    def graceful_shutdown(self) -> None:
        """Stop running agents, finalize metrics, flush caches, close connections."""
        logger.info("Initiating graceful shutdown...")
        self.stop_all_agents()
        self.finalize_metrics()
        self.flush_caches()
        self.close_connections()
        self.cleanup_resources()
        logger.info("Graceful shutdown complete")

    def stop_all_agents(self) -> None:
        """Stop all currently running agents."""
        if self.agent_factory:
            self.agent_factory.stop_all_agents()
        self._active_agents.clear()

    def finalize_metrics(self) -> None:
        """Finalize and persist all collected metrics."""
        if self.metrics and hasattr(self.metrics, "flush"):
            self.metrics.flush()

    def flush_caches(self) -> None:
        """Flush all cache stores."""
        if self.memory_manager and hasattr(self.memory_manager, "flush"):
            self.memory_manager.flush()

    def close_connections(self) -> None:
        """Close all database and API connections."""
        if self.memory_manager and hasattr(self.memory_manager, "close"):
            self.memory_manager.close()

    def cleanup_resources(self) -> None:
        """Clean up temporary resources and files."""
        self._active_agents.clear()
        self._agent_results.clear()
        if self.task_graph:
            self.task_graph.clear()

    # ==================== HEALTH & STATUS ====================

    def health_check(self) -> Dict[str, Any]:
        """Check health of all subsystems."""
        return {
            "event_bus": self.event_bus is not None,
            "agent_factory": self.agent_factory is not None,
            "memory_manager": self.memory_manager is not None,
            "budget_manager": self.budget_manager is not None,
            "tool_registry": self.tool_registry is not None,
            "metrics": self.metrics is not None,
            "tracer": self.tracer is not None,
            "task_graph": self.task_graph is not None,
            "llm_router": self.llm_router is not None,
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status including agents, tasks, resources."""
        status: Dict[str, Any] = {
            "health": self.health_check(),
            "active_agents": len(self._active_agents),
            "correlation_id": self._correlation_id,
        }
        if self.task_graph:
            status["task_progress"] = self.task_graph.get_progress()
        if self.budget_manager:
            status["budget"] = self.budget_manager.get_budget_status()
        return status

    def is_ready(self) -> bool:
        """Check if orchestrator is ready to accept requests."""
        return (
            self.agent_factory is not None
            and self.memory_manager is not None
            and self.event_bus is not None
        )

    def get_queue_status(self) -> Dict[str, Any]:
        """Get status of task queue."""
        if not self.task_graph:
            return {"total": 0, "ready": 0, "running": 0, "pending": 0}
        progress = self.task_graph.get_progress()
        return {
            "total": progress["total"],
            "pending": progress["pending"],
            "ready": progress["ready"],
            "running": progress["running"],
            "completed": progress["completed"],
            "failed": progress["failed"],
        }

    async def _run_agent(
        self, spec: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run one agent and all its tasks, yielding a progress event after each step.

        Yields dicts with an ``event`` key:
          - ``agent_spawned``  — agent is ready
          - ``task_done``      — one task finished successfully
          - ``task_error``     — one task failed
          - ``agent_error``    — agent could not be spawned
          - ``agent_done``     — final summary (callers collect this to build all_results)
        """
        agent_name = spec["agent_name"]

        # ── spawn ──────────────────────────────────────────────────────────────────
        try:
            agent = await asyncio.to_thread(self._spawn_from_spec, spec)
            yield {
                "event": "agent_spawned",
                "agent_name": agent_name,
                "agent_id": agent.agent_id,
            }
        except Exception as exc:
            logger.error(f"Failed to spawn '{agent_name}': {exc}")
            yield {
                "event": "agent_error",
                "agent_name": agent_name,
                "error": str(exc),
                "task_results": [],
            }
            return

        # ── execute tasks ──────────────────────────────────────────────────────────
        task_results: List[Dict[str, Any]] = []
        for task in spec.get("tasks", []):
            try:
                result = await asyncio.to_thread(self.execute_agent_task, agent, task)
                task_results.append({"task": task, "result": result})
                yield {
                    "event": "task_done",
                    "agent_name": agent_name,
                    "task_type": task.get("type"),
                    "status": result.get("status"),
                }
            except Exception as exc:
                logger.error(f"[{agent_name}] task '{task.get('type')}' failed: {exc}")
                task_results.append(
                    {"task": task, "result": {"status": "error", "error": str(exc)}}
                )
                yield {
                    "event": "task_error",
                    "agent_name": agent_name,
                    "task_type": task.get("type"),
                    "error": str(exc),
                }

        agent.complete()
        # final summary — callers key on event=="agent_done" to build all_results
        yield {
            "event": "agent_done",
            "agent_name": agent_name,
            "agent_id": agent.agent_id,
            "agent_class": type(agent).__name__,
            "status": agent.status,
            "task_results": task_results,
        }
