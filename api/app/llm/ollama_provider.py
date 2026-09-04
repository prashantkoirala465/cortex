import json
import logging

import ollama
from pydantic import ValidationError

from app.config import settings
from app.llm.base import ExtractionResult, LLMProvider

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You extract structured knowledge from a personal note.

Read the note text and identify:
1. entities: distinct people, concepts, tools, projects, or things mentioned (short, consistent names)
2. relationships: how those entities relate to each other, as (source, target, label) triples using ONLY entity names from your entities list

Respond with ONLY valid JSON in exactly this shape, nothing else:
{"entities": [{"name": "...", "type": "..."}], "relationships": [{"source": "...", "target": "...", "label": "..."}]}

If nothing meaningful can be extracted, respond with {"entities": [], "relationships": []}."""


class OllamaProvider(LLMProvider):
    def __init__(self) -> None:
        self._client = ollama.Client(host=settings.ollama_host)

    def extract(self, text: str) -> ExtractionResult:
        response = self._client.chat(
            model=settings.ollama_model,
            format="json",
            options={"temperature": 0},
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        raw = response["message"]["content"]
        try:
            return ExtractionResult.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError):
            logger.warning("extraction model returned unparseable output: %.200s", raw)
            return ExtractionResult()

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embed(model=settings.ollama_embedding_model, input=texts)
        return response["embeddings"]
