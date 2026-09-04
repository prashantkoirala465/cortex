from abc import ABC, abstractmethod

from pydantic import BaseModel


class ExtractedEntity(BaseModel):
    name: str
    type: str | None = None


class ExtractedRelationship(BaseModel):
    source: str
    target: str
    label: str


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = []
    relationships: list[ExtractedRelationship] = []


class LLMProvider(ABC):
    """Seam between the extraction pipeline and whichever model actually
    runs it. LLM backends are a volatile dependency (rate limits, model
    deprecation, cost) - isolating them here means swapping providers
    later (e.g. a hosted one for deployment) doesn't touch pipeline logic."""

    @abstractmethod
    def extract(self, text: str) -> ExtractionResult: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str: ...
