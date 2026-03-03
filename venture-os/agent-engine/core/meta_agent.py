# Meta-Agent: orchestrates all agents
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
        return response

    def decompose_goals(self, response: str):
        """_summary_

        Args:
            response (str): _description_

        Returns:
            _type_: _description_
        """
        tasks = []
        for task in response.get("required_capabilities", []):
            tasks.append(
                {
                    "task_name": task,
                    "status": "pending",
                    "assigned_agent": None,
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

    def spawn_base_agent(self, task):
        graph = self.create_task_graph(task)
        agent = self.create_agent(task)
        return agent

    def supervise(self, tasks):
        for task in tasks:
            if task["status"] == "peneding" and self.depency_satified(task):
                self.spawn_base_agent(task)
                task["assigned_agent"] = "agent_id"  # assign the agent id to the task
                task["status"] = "in progress"
                task["dependency"].append(
                    task["task_name"]
                )  # add the task name to the dependency list of other tasks
            elif task["status"] == "in progress":
                # check the status of the assigned agent and update the task status accordingly
                agent_status = self.check_agent_status(task["assigned_agent"])
                if agent_status == "completed":
                    task["status"] = "completed"
                elif agent_status == "failed":
                    self.handle_failure(task)

    def refine_strategy(self):
        pass

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
