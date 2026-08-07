from dotenv import load_dotenv
import os
import time
import logging

logger = logging.getLogger(__name__)

# How long to wait before retrying on a 429 (doubles each attempt)
_RATE_LIMIT_BASE_DELAY = 5.0   # seconds
_RATE_LIMIT_MAX_RETRIES = 4

# Network timeout for every provider's HTTP client. Without this, a stalled
# connection (observed inside Docker's NAT'd network) hangs the call forever —
# there's no task-level watchdog elsewhere, so a single hung request wedges
# the whole worker process indefinitely.
_REQUEST_TIMEOUT_SECONDS = 60.0

# Cohere models removed after Sep 2025 → current replacements
_COHERE_ALIASES: dict[str, str] = {
    "command-r-plus": "command-a-03-2025",
    "command-r": "command-r7b-12-2024",
    "command": "command-a-03-2025",
    "command-light": "command-r7b-12-2024",
}


# instead of if else statment we can use factory pattern to create the llm client based on the model name
class LLM:
    def __init__(self, model: str, temperature: float = 0.7) -> None:
        """Initialize the LLM class with the specified model and temperature."""
        load_dotenv()
        self.model = model
        self.temperature = temperature
        self.provider: str = ""

        if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
            from openai import OpenAI

            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"), timeout=_REQUEST_TIMEOUT_SECONDS
            )
            self.provider = "openai"

        elif model.startswith("gemini-"):
            try:
                from google import genai  # type: ignore[import-untyped]
                from google.genai.types import HttpOptions
            except ImportError:
                raise ImportError("Install google-genai: pip install google-genai")
            self.client = genai.Client(
                api_key=os.getenv("GOOGLE_GEMINI_API_KEY"),
                http_options=HttpOptions(timeout=int(_REQUEST_TIMEOUT_SECONDS * 1000)),
            )
            self.provider = "gemini"

        elif model.startswith("mistral-"):
            try:
                from mistralai import Mistral  # type: ignore[import-untyped]
            except ImportError:
                raise ImportError("Install mistralai: pip install mistralai")
            self.client = Mistral(
                api_key=os.getenv("MISTRAL_API_KEY"),
                timeout_ms=int(_REQUEST_TIMEOUT_SECONDS * 1000),
            )
            self.provider = "mistral"

        elif model.startswith("bedrock/"):
            import boto3  # type: ignore[import-not-found]

            self.client = boto3.client(
                "bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1")
            )
            # Strip the "bedrock/" prefix to get the actual Bedrock modelId,
            # e.g. "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0".
            self.model = model[len("bedrock/") :]
            self.provider = "bedrock"

        elif model.startswith("command"):
            try:
                import cohere  # type: ignore[import-untyped]
            except ImportError:
                raise ImportError("Install cohere: pip install cohere")
            # Remap any deprecated model names automatically
            resolved = _COHERE_ALIASES.get(model, model)
            if resolved != model:
                print(
                    f"[LLM] Cohere model '{model}' was removed — using '{resolved}' instead."
                )
                self.model = resolved
            self.client = cohere.ClientV2(
                api_key=os.getenv("COHERE_API_KEY"), timeout=_REQUEST_TIMEOUT_SECONDS
            )
            self.provider = "cohere"

        else:
            raise ValueError(
                f"Unsupported model: '{model}'. "
                "Supported prefixes: gpt-, o1, o3, gemini-, mistral-, command, bedrock/"
            )

    def _invoke_once(self, prompt: str, system_prmpt: str) -> str:
        """Single (non-retried) LLM call — called by invoke()."""
        if self.provider == "openai":
            response = self.client.chat.completions.create(  # type: ignore[union-attr]
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prmpt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""

        elif self.provider == "gemini":
            full_prompt = f"{system_prmpt}\n\n{prompt}" if system_prmpt else prompt
            response = self.client.models.generate_content(  # type: ignore[union-attr]
                model=self.model, contents=full_prompt
            )
            return response.text or ""

        elif self.provider == "mistral":
            response = self.client.chat.complete(  # type: ignore[union-attr]
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prmpt},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""

        elif self.provider == "cohere":
            messages = []
            if system_prmpt:
                messages.append({"role": "system", "content": system_prmpt})
            messages.append({"role": "user", "content": prompt})
            response = self.client.chat(model=self.model, messages=messages)  # type: ignore[union-attr]
            content = response.message.content  # type: ignore[union-attr]
            return content[0].text if content else ""  # type: ignore[union-attr]

        elif self.provider == "bedrock":
            response = self.client.converse(  # type: ignore[union-attr]
                modelId=self.model,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                system=[{"text": system_prmpt}] if system_prmpt else [],
                inferenceConfig={"temperature": self.temperature},
            )
            return response["output"]["message"]["content"][0]["text"]

        raise ValueError(f"Unknown provider: '{self.provider}'")

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Return True if the exception signals a 429 / rate-limit condition."""
        msg = str(exc).lower()
        return (
            "429" in msg
            or "rate limit" in msg
            or "rate_limited" in msg
            or "too many requests" in msg
            or "resource_exhausted" in msg  # Gemini
            or "quota" in msg
            or "throttling" in msg  # Bedrock ThrottlingException
        )

    def invoke(self, prompt: str, system_prmpt: str = "") -> str:
        """Invoke the LLM with automatic retry on rate-limit responses."""
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(_RATE_LIMIT_MAX_RETRIES):
            try:
                return self._invoke_once(prompt, system_prmpt)
            except Exception as exc:
                last_exc = exc
                if self._is_rate_limit_error(exc) and attempt < _RATE_LIMIT_MAX_RETRIES - 1:
                    delay = _RATE_LIMIT_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Rate limit on attempt {attempt + 1}/{_RATE_LIMIT_MAX_RETRIES}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                # Non-rate-limit error or final attempt — re-raise immediately
                raise
        raise last_exc
