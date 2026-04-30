from __future__ import annotations

import os

from llm.config import PipelineConfig
from llm.groq_client import GroqExtractionClient, LLMClientError
from llm.ollama_client import OllamaExtractionClient, OllamaClientError


def create_extraction_client(config: PipelineConfig):
    if config.client == "ollama":
        return OllamaExtractionClient(url=config.ollama_url)
    if config.client == "groq":
        return GroqExtractionClient(api_key=os.getenv("GROQ_API_KEY"))
    raise LLMClientError(f"Unsupported client type: {config.client}")
