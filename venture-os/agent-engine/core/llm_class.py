from openai import OpenAI
from dotenv import load_dotenv
import os


class LLM:
    def __init__(self, model: str = "gpt-5", temperature: float = 0.7) -> None:
        """Initialize the LLM class with the specified model and temperature.

        Args:
            model (str): The name of the OpenAI model to use (default is "gpt-5").
            temperature (float): The sampling temperature for generating responses (default is 0.7).
        """
        load_dotenv()  # Load environment variables from .env file
        opneai_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=opneai_key)

    def invoke(self, prompt: str, system_prmpt: str = "") -> str:
        """Invoke the LLM with the given prompt and return the generated response.

        Args:
            prompt (str): The input prompt to send to the LLM.
            system_prmpt (str): The system prompt to set the behavior of the assistant.

        Returns:
            str: The generated response from the LLM.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prmpt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
        )
        if response:
            return response.choices[0].message.content or ""
