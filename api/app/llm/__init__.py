from app.llm.base import ExtractedEntity, ExtractedRelationship, ExtractionResult, LLMProvider
from app.llm.ollama_provider import OllamaProvider


def get_llm_provider() -> LLMProvider:
    return OllamaProvider()


__all__ = [
    "ExtractedEntity",
    "ExtractedRelationship",
    "ExtractionResult",
    "LLMProvider",
    "get_llm_provider",
]
