"""Configuration and settings for the application."""

from langchain_ollama import ChatOllama

# LLM Configuration
LLM_MODEL = "qwen2.5-coder:3b"
LLM_TEMPERATURE = 0.1

# Initialize the local language model
local_llm = ChatOllama(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE
)
