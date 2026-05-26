from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent

class ValuePropositionDesignerAgent(BaseAgent):
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")
        if task_type == "identify_tool_benefits":
            return self._identify_tool_benefits(task.get("product_data"), task.get("company_needs"))
        elif task_type == "draft_personalized_subject_line":
            return self._draft_personalized_subject_line(task.get("company_data"), task.get("tool_benefits"))
        elif task_type == "write_value_driven_email":
            return self._write_value_driven_email(
                task.get("company_data"),
                task.get("tool_benefits"),
                task.get("subject_line")
            )
        else:
            return {"status": "error", "error": f"Unknown task type: {task.get('type')}"}

    def _identify_tool_benefits(self, product_data: Dict[str, Any], company_needs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Given the following product data and company needs, identify the key benefits of the CI/CD tool that align with the company's requirements.

        Product Data:
        {product_data}

        Company Needs:
        {company_needs}

        Provide a list of key benefits in a structured format.
        """
        system_prompt = """
        You are an expert in CI/CD tools and value proposition design. Your task is to identify the most relevant benefits of a CI/CD tool based on the product features and the company's specific needs.
        """
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "tool_benefits": response}

    def _draft_personalized_subject_line(self, company_data: Dict[str, Any], tool_benefits: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Given the following company data and identified tool benefits, draft a personalized and compelling subject line for an email to the VP of Engineering.

        Company Data:
        {company_data}

        Tool Benefits:
        {tool_benefits}

        The subject line should be concise, value-driven, and tailored to the VP of Engineering's priorities.
        """
        system_prompt = """
        You are a skilled copywriter specializing in crafting personalized and high-impact subject lines for executive audiences. Focus on the value and relevance to the VP of Engineering.
        """
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "subject_line": response}

    def _write_value_driven_email(self, company_data: Dict[str, Any], tool_benefits: Dict[str, Any], subject_line: str) -> Dict[str, Any]:
        prompt = f"""
        Write a value-driven email to the VP of Engineering using the provided company data, tool benefits, and subject line.

        Company Data:
        {company_data}

        Tool Benefits:
        {tool_benefits}

        Subject Line:
        {subject_line}

        The email should be concise, professional, and focused on the value the CI/CD tool brings to their specific challenges and goals.
        """
        system_prompt = """
        You are an expert in crafting persuasive and value-driven emails for executive audiences. Ensure the email is tailored to the VP of Engineering's priorities and highlights the key benefits of the CI/CD tool.
        """
        response = self._invoke_llm(prompt, system_prompt)
        return {"status": "success", "email": response}