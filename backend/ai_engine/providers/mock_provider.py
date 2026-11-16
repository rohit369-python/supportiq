"""Mock LLM and Embedding providers for development and testing."""

import hashlib
import json
import random
import time
from typing import Optional

from ai_engine.providers.base import LLMProvider, EmbeddingProvider, LLMResponse, EmbeddingResponse
from app.config.settings import settings


class MockLLMProvider(LLMProvider):
    name = "mock"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        start = time.perf_counter()
        # Deterministic-ish mock based on input hash
        h = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
        lower = user_prompt.lower()

        # Classification-style responses
        if "intent" in system_prompt.lower() or "classify" in system_prompt.lower():
            intents = [
                "order_tracking", "refund_request", "return_request", "payment_issue",
                "login_issue", "account_recovery", "product_complaint", "technical_support",
                "delivery_delay", "warranty_question", "cancellation", "general_inquiry",
            ]
            intent = intents[int(h[:2], 16) % len(intents)]
            categories = {
                "order_tracking": ("Orders", "Tracking"),
                "refund_request": ("Billing", "Refunds"),
                "return_request": ("Orders", "Returns"),
                "payment_issue": ("Billing", "Payments"),
                "login_issue": ("Account", "Access"),
                "account_recovery": ("Account", "Recovery"),
                "product_complaint": ("Product", "Quality"),
                "technical_support": ("Support", "Technical"),
                "delivery_delay": ("Shipping", "Delays"),
                "warranty_question": ("Product", "Warranty"),
                "cancellation": ("Orders", "Cancellations"),
                "general_inquiry": ("General", "Inquiry"),
            }
            cat, sub = categories.get(intent, ("General", "Other"))
            content = json.dumps({
                "intent": intent,
                "category": cat,
                "subcategory": sub,
                "confidence": round(0.7 + (int(h[2:4], 16) % 30) / 100, 2),
                "entities": {},
            })
        elif "sentiment" in system_prompt.lower():
            if any(w in lower for w in ["angry", "furious", "terrible", "worst", "hate"]):
                sentiment, score = "very_negative", -0.9
            elif any(w in lower for w in ["bad", "poor", "disappointed", "upset"]):
                sentiment, score = "negative", -0.6
            elif any(w in lower for w in ["great", "thanks", "love", "excellent"]):
                sentiment, score = "positive", 0.8
            else:
                sentiment, score = "neutral", 0.1
            content = json.dumps({"sentiment": sentiment, "score": score, "confidence": 0.85})
        elif "summar" in system_prompt.lower():
            content = (
                "Customer reported an issue related to their order. "
                "Key points extracted from conversation. "
                "Recommended next action: verify order status and respond with tracking information."
            )
        elif "suggest" in system_prompt.lower() or "reply" in system_prompt.lower():
            content = (
                "Thank you for contacting us. I understand your concern. "
                "Let me look into this for you right away. "
                "Could you please provide your order number so I can assist you better?"
            )
        elif "rag" in system_prompt.lower() or "knowledge" in system_prompt.lower() or "answer" in system_prompt.lower():
            if "refund" in lower:
                content = (
                    "According to our refund policy, eligible items can be refunded within 30 days of delivery "
                    "if they are in original condition. Please provide your order number to start the process. "
                    "[Source: Refund Policy]"
                )
            elif "track" in lower or "shipping" in lower:
                content = (
                    "You can track your order using the tracking number provided in your shipping confirmation email. "
                    "Orders typically arrive within 3-7 business days. [Source: Shipping FAQ]"
                )
            else:
                content = (
                    "I found relevant information in our knowledge base. "
                    "If this does not fully answer your question, I can connect you with a human agent."
                )
        else:
            content = "I am the SupportIQ AI assistant. How can I help you today?"

        latency = int((time.perf_counter() - start) * 1000) + random.randint(20, 80)
        return LLMResponse(
            content=content,
            model="mock-gpt",
            provider=self.name,
            input_tokens=len(system_prompt.split()) + len(user_prompt.split()),
            output_tokens=len(content.split()),
            latency_ms=latency,
            finish_reason="stop",
        )

    async def health_check(self) -> bool:
        return True


class MockEmbeddingProvider(EmbeddingProvider):
    name = "mock"
    dimensions = settings.embedding_dimension

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        start = time.perf_counter()
        embeddings = []
        for text in texts:
            # Deterministic pseudo-embedding from hash
            h = hashlib.sha256(text.encode()).digest()
            vec = []
            for i in range(self.dimensions):
                # Expand hash into floats in [-1, 1]
                b = h[i % len(h)]
                vec.append((b / 127.5) - 1.0)
            # L2 normalize
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            embeddings.append([x / norm for x in vec])
        latency = int((time.perf_counter() - start) * 1000)
        return EmbeddingResponse(
            embeddings=embeddings,
            model="mock-embed",
            provider=self.name,
            dimensions=self.dimensions,
            latency_ms=latency,
        )

    async def health_check(self) -> bool:
        return True