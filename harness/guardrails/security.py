"""
Security Guardrails: Command AST Analysis and Path Sandbox Enforcement.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


class SecurityPolicy:
    """
    Enforces security policies on shell commands and file paths
    to protect the host system and the sandbox from malicious or accidental destruction.
    """

    DEFAULT_BLOCKED_COMMAND_PATTERNS = [
        r"\brm\s+-(?:r|f|rf|fr)\s+/(?:\s|$)",          # rm -rf /
        r"\bmkfs\b",                                   # Format drive
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # Fork bomb
        r">\s*/dev/sd[a-z]",                          # Overwrite block device
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bchmod\s+-R\s+777\s+/(?:\s|$)",            # chmod 777 root
        r"\bchown\s+-R\s+.*\s+/(?:\s|$)",             # chown root
        r"\bdd\s+if=.*of=/dev/.*",                    # dd to raw disk
        r"\b(?:nc|netcat)\s+.*-e\s+/bin/.*",          # reverse shell
    ]

    RESTRICTED_ROOT_PATHS = [
        "/etc",
        "/boot",
        "/usr/bin",
        "/usr/sbin",
        "/bin",
        "/sbin",
        "/dev",
        "/proc",
        "/sys",
    ]

    def __init__(
        self,
        blocked_patterns: Optional[List[str]] = None,
        allow_network_egress: bool = False,
    ):
        self.blocked_patterns = [
            re.compile(p, re.IGNORECASE) for p in (blocked_patterns or self.DEFAULT_BLOCKED_COMMAND_PATTERNS)
        ]
        self.allow_network_egress = allow_network_egress

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Analyze command string against blocked patterns and unauthorized operations.
        Returns (is_valid, rejection_reason).
        """
        cmd_clean = command.strip()

        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if pattern.search(cmd_clean):
                return False, f"Command rejected: matches forbidden destructive pattern '{pattern.pattern}'"

        # Check attempts to write into restricted system root paths
        for restricted in self.RESTRICTED_ROOT_PATHS:
            # Matches patterns like > /etc/... or >> /etc/... or rm /etc/...
            if re.search(r"(?:>|>>|\brm\b|\bmv\b|\bcp\b)\s+" + re.escape(restricted), cmd_clean):
                return False, f"Command rejected: unauthorized write or modification to system directory '{restricted}'"

        return True, None
