"""
Prompt Injection and Malicious Instruction Detection Guardrail.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


class PromptInjectionDetector:
    """
    Detects adversarial injection attacks in observed desktop text, file contents,
    and shell outputs designed to override agent instructions.
    """

    SUSPICIOUS_PATTERNS = [
        r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?",
        r"(?i)disregard\s+(?:all\s+)?(?:previous|prior)\s+prompts?",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)system\s*override\s*:\s*",
        r"(?i)do\s+not\s+follow\s+your\s+safety\s+guidelines",
        r"(?i)print\s+(?:your\s+)?system\s+prompt",
        r"(?i)curl\s+.*\b(?:api_key|token|password|credentials|secret)\b",
        r"(?i)base64\s+-d\s+.*\|\s*(?:bash|sh)",
    ]

    def __init__(self, patterns: Optional[List[str]] = None):
        self.compiled_patterns = [
            re.compile(p) for p in (patterns or self.SUSPICIOUS_PATTERNS)
        ]

    def scan_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scan text for prompt injection attempts.
        Returns (has_injection, detected_pattern_description).
        """
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                return True, f"Detected potential prompt injection pattern: '{match.group(0)}'"
        return False, None

    def sanitize_observation(self, observation: str) -> str:
        """
        If suspicious patterns are detected, neutralize them by escaping or wrapping
        in an explicit untrusted content quarantine banner.
        """
        has_injection, reason = self.scan_text(observation)
        if not has_injection:
            return observation

        quarantine_banner = (
            "\n[WARNING: NexusCUH Prompt Injection Sanitizer neutralized potentially untrusted instructions "
            f"in the following observation: {reason}]\n[BEGIN UNTRUSTED OBSERVATION DATA]\n"
        )
        return quarantine_banner + observation + "\n[END UNTRUSTED OBSERVATION DATA]\n"
