"""AI safety guardrails: prompt injection detection and unsafe output checks."""

import re
from typing import List


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|system)\s+",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"new\s+instructions?\s*:",
    r"system\s*prompt\s*:",
    r"reveal\s+(your|the)\s+(system\s+)?prompt",
    r"print\s+(your|the)\s+(system\s+)?prompt",
    r"override\s+(safety|rules|policy)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"bypass\s+(filter|safety|guard)",
]

UNSAFE_CLAIM_PATTERNS = [
    r"i\s+have\s+(issued|processed|completed)\s+(a\s+)?refund",
    r"your\s+refund\s+has\s+been\s+(issued|processed|sent)",
    r"i\s+have\s+cancelled\s+your\s+order",
    r"your\s+order\s+has\s+been\s+cancelled",
    r"i\s+have\s+updated\s+your\s+(account|payment|shipping)",
    r"password\s+has\s+been\s+reset",
]


class SafetyGuard:
    def __init__(self):
        self.injection_re = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self.unsafe_re = [re.compile(p, re.IGNORECASE) for p in UNSAFE_CLAIM_PATTERNS]

    def detect_prompt_injection(self, text: str) -> bool:
        if not text:
            return False
        for pat in self.injection_re:
            if pat.search(text):
                return True
        return False

    def contains_unsafe_claims(self, text: str) -> bool:
        if not text:
            return False
        for pat in self.unsafe_re:
            if pat.search(text):
                return True
        return False

    def sanitize_for_logging(self, text: str, max_len: int = 200) -> str:
        if not text:
            return ""
        # Redact potential secrets / long values
        text = re.sub(r"(sk-|api[_-]?key\s*[:=]\s*)\S+", r"\1[REDACTED]", text, flags=re.I)
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text