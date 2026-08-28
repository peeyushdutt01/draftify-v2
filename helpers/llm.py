import logging
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

def get_llm(**kwargs):

    provider = kwargs.pop(
        "provider",
        os.getenv("LLM_PROVIDER", "ollama")
    )
    logger.info("Creating LLM client: provider=%s model=%s", provider, kwargs.get("model"))


    return ChatOpenAI(
        api_key=os.getenv("NVIDIA_API_KEY"),
        base_url="https://integrate.api.nvidia.com/v1",
        **kwargs
    )

    raise ValueError(f"Unsupported LLM provider: {provider}")