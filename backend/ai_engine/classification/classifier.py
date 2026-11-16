"""Ticket intent / category / entity classification."""

import json
from typing import Any, Optional
from dataclasses import dataclass

from ai_engine.providers.factory import get_llm_provider
from ai_engine.prompts.templates import CLASSIFY_SYSTEM, CLASSIFY_USER


@dataclass
class ClassificationResult:
    intent: str
    category: str
    subcategory: str
    confidence: float
    entities: dict
    raw: Optional[dict] = None


class TicketClassifier:
    def __init__(self):
        self.llm = get_llm_provider()

    async def classify(self, subject: str, description: str) -> ClassificationResult:
        user_prompt = CLASSIFY_USER.format(subject=subject, description=description)
        resp = await self.llm.complete(
            system_prompt=CLASSIFY_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=512,
        )
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            # Fallback parsing for mock / malformed
            data = {
                "intent": "general_inquiry",
                "category": "General",
                "subcategory": "Inquiry",
                "confidence": 0.5,
                "entities": {},
            }
        return ClassificationResult(
            intent=data.get("intent", "general_inquiry"),
            category=data.get("category", "General"),
            subcategory=data.get("subcategory", "Inquiry"),
            confidence=float(data.get("confidence", 0.5)),
            entities=data.get("entities") or {},
            raw=data,
        )