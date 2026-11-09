"""Error model shared by CLI, bootstrap and adapters.

Source of truth: _design/03 section 16.1 (exit codes) and _design/04 section 2.1
(PortError codes). Nothing here is provider specific.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_UNAVAILABLE = 69
EXIT_INTERNAL = 70
EXIT_CREATE = 73
EXIT_IO = 74
EXIT_CONFIG = 78


@dataclass
class PlatformError(Exception):
    """Startup / configuration failure with a stable code and exit code."""

    code: str
    detail: str
    stage: str = "general"
    key: str | None = None
    provider: str | None = None
    hint: str = ""
    exit_code: int = EXIT_INTERNAL
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        Exception.__init__(self, self.detail)

    def render(self) -> str:
        parts = [f"{self.code} stage={self.stage}"]
        if self.key:
            parts.append(f"key={self.key}")
        if self.provider:
            parts.append(f"provider={self.provider}")
        lines = [" ".join(parts), f"  detail: {self.detail}"]
        if self.hint:
            lines.append(f"  hint: {self.hint}")
        lines.append(f"  log_id: {self.log_id}   exit: {self.exit_code}")
        return "\n".join(lines)


@dataclass
class PortError(Exception):
    """Uniform adapter error (04 section 2.1)."""

    code: str
    message: str
    provider: str | None = None
    provider_code: str | None = None
    retryable: bool = False
    details: dict | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


def port_error_exit_code(err: PortError) -> int:
    """Map a port error to the process exit code used during self-check."""
    if err.code in ("Unavailable", "DeadlineExceeded", "Aborted"):
        return EXIT_UNAVAILABLE
    if err.code == "ResourceExhausted":
        return EXIT_IO
    if err.code == "PermissionDenied":
        return EXIT_IO
    if err.code in ("InvalidArgument", "Unsupported", "PolicyRejected"):
        return EXIT_CONFIG
    if err.code == "DataLoss":
        return EXIT_UNAVAILABLE
    return EXIT_INTERNAL


UNSUPPORTED_PORT = "E_PORT_NOT_IMPLEMENTED"
