from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class QueryInterpreterAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "parse_user_query":
            return self._parse_user_query(task)
        elif task_type == "extract_intent_and_context":
            return self._extract_intent_and_context(task)
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _parse_user_query(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query_text = task.get("query_text", "")
        prompt = f"""
        Analyze the following user query and determine if it is asking for the assistant's name.
        Query: "{query_text}"

        Respond with a JSON object containing:
        - "is_asking_for_name": boolean indicating if the query is asking for the assistant's name
        - "confidence": float between 0 and 1 representing confidence in the determination
        - "query_summary": a brief summary of the query
        """
        system_prompt = """
        You are an expert query interpreter. Your task is to analyze user queries and determine their intent.
        """
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": response}

    def _extract_intent_and_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query_text = task.get("query_text", "")
        prompt = f"""
        Extract the intent and relevant context from the following user query:
        Query: "{query_text}"

        Respond with a JSON object containing:
        - "intent": the primary intent of the query (e.g., "ask_name", "request_info", "general_conversation")
        - "context": a dictionary of key-value pairs representing relevant context extracted from the query
        - "confidence": float between 0 and 1 representing confidence in the extraction
        """
        system_prompt = """
        You are an expert intent and context extractor. Your task is to analyze user queries and extract their intent and relevant context.
        """
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "result": response}