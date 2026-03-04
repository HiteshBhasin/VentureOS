# Abstract base agent class
class Base_Agent:
    def __init__(self, task_name: str, llm, memory=None, tools=None):
        self.task_name = task_name
        self.llm = llm
        self.memory = memory
        self.tools = tools or []
        self.status = "idle"

    def execute_task(self, ):
