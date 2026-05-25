# Meta-Agent: orchestrates all agents
import json
import logging
from core.agent_factory import AgentFactory
from .llm_class import LLM


class Meta_agent:
    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def analyze_user_requirement(self, user_input: str):
        """_summary_

        Args:
            input (str): _description_
        """
        prompt = f"Analyze the user requirement and decompose it into smaller tasks: {user_input}"
        system_prompt = """You are a helpful assistant that analyzes user requirements and decomposes them into smaller tasks. the output should be a list of tasks that can be executed by base agents. Each task should be concise and actionable. the pattern should in json format : example=
        {
            "primary_goal": "Launch AI marketing agency",
            "domain": "Digital Marketing",
            "constraints": ["domestic and global markets"],
            "required_capabilities": [
                "market research",
                "service definition",
                "pricing strategy",
                "customer acquisition strategy"
            ],
            "complexity_level": "medium"
            }
            keep all the attributes as is , as I will be using them to create task graph and spawn base agents. the primary goal is the main objective that the user wants to achieve. the domain is the specific area or industry related to the primary goal. constraints are any limitations or restrictions that need to be considered while achieving the primary goal. required capabilities are the skills, knowledge, or resources needed to accomplish the primary goal. complexity level indicates how difficult it is to achieve the primary goal, which can be categorized as low, medium, or high.
        """
        response = self.llm.invoke(prompt, system_prompt)
        parsed_response = json.loads(response) if response else {}
        return parsed_response

    def decompose_goals(self, response: dict):
        """_summary_

        Args:
            response (dict): parsed response from analyze_user_requirement

        Returns:
            _type_: _description_
        """
        tasks = []
        if isinstance(response, dict) and "required_capabilities" in response:
            for task in response["required_capabilities"]:
                tasks.append(
                    {
                        "task_name": task,
                        "status": "pending",
                        "agent_type": task,  # this can be used to determine which type of agent to spawn for this task
                        "assigned_agent": None,
                        "status": "pending",
                        "dependencies": [],
                    }
                )
        return tasks

    def create_task_graph(self, tasks):
        """
        you would need to analyze the dependencies between tasks and create a more complex graph
        Args:
            tasks (_type_): taks list
        Returns:
            _type_: task graph whch is a list of tasks sorted in topological order based on their dependencies
        """
        # .
        task_graph = self._topological_sort(tasks)
        return task_graph

    # def spawn_base_agent(self, task):
    #     """_summary_

    #     Args:
    #         task (_type_): _description_

    #     Returns:
    #         _type_: _description_
    #     """
    #     agent_factory = AgentFactory(self.llm)
    #     agent = agent_factory.spawn_agent(task)
    #     return agent

    # def supervise(self, tasks):
    #     for task in tasks:
    #         if task["status"] == "pending" and self.depency_satified(task):
    #             self.spawn_base_agent(task)
    #             task["assigned_agent"] = "agent_id"  # assign the agent id to the task
    #             task["status"] = "in progress"
    #             task["dependencies"].append(
    #                 task["task_name"]
    #             )  # add the task name to the dependency list of other tasks
    #         elif task["status"] == "in progress":
    #             # check the status of the assigned agent and update the task status accordingly
    #             agent_status = self.check_agent_status(task["assigned_agent"])
    #             if agent_status == "completed":
    #                 task["status"] = "completed"
    #             elif agent_status == "failed":
    #                 self.handle_failure(task)

    def refine_strategy(self):
        """Re-analyze current task statuses and adjust strategy."""
        all_tasks = getattr(self, "_tasks", [])
        if not all_tasks:
            return
        failed_tasks = [t for t in all_tasks if t.get("status") == "failed"]
        pending_tasks = [t for t in all_tasks if t.get("status") == "pending"]
        # Reset failed tasks for retry
        for task in failed_tasks:
            task["status"] = "pending"
            task["assigned_agent"] = None
            logging.info(
                f"Refining strategy: resetting failed task '{task['task_name']}' for retry"
            )
        # Re-sort pending tasks by dependency order
        if pending_tasks:
            sorted_tasks = self._topological_sort(pending_tasks)
            for i, task in enumerate(sorted_tasks):
                task["priority"] = i
            logging.info(
                f"Refining strategy: re-prioritized {len(sorted_tasks)} pending tasks"
            )

    def _topological_sort(self, tasks):
        """_summary_

        Args:
            tasks (_type_): _description_

        Returns:
            _type_: _description_
        """

        def dfs(task, visited: set, stack: list):
            visited.add(task["task_name"])
            for dep in task["dependencies"]:
                if dep not in visited:
                    dfs(dep, visited, stack)
            stack.append(task)

        visited = set()
        stack = []
        for task in tasks:
            if task["task_name"] not in visited:
                dfs(task, visited, stack)
        return stack[::-1]

    def depency_satified(self, task: list):
        # check if all dependencies of the task are completed
        for dep in task["dependencies"]:
            if dep["status"] != "completed":
                return False
        return True

    def check_agent_status(self, agent_id):
        # check the status of the assigned agent
        if agent_id:
            # logic to check agent status
            return "completed"  # or "failed"
        return "pending"

    def handle_failure(self, task):
        # logic to handle task failure, such as retrying or reassigning the task
        if task["status"] == "failed":
            task["status"] = "pending"
            task["assigned_agent"] = None
            logging.info(f"Task {task['task_name']} failed. Retrying...")
