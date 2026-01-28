"""Configuration and settings for the application."""

from langchain_ollama import ChatOllama

import os

# LLM Configuration
LLM_MODEL = "qwen2.5-coder:3b"
LLM_TEMPERATURE = 0.1

# Initialize the local language model
# Docker needs to access host machine's Ollama via host.docker.internal or configured URL
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

local_llm = ChatOllama(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    base_url=ollama_base_url
)
