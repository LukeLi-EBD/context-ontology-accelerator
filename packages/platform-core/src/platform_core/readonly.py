"""Read-only freeze guard for the Platform Kernel HTTP surface.

Installed as an ASGI middleware in ``create_app``.  The runtime rule is
"non-GET is a write unless it matches an explicit allow-list"; only this
module knows about individual paths, so the route table stays untouched.

The switch is a sentinel file ``<data_root>/READONLY`` and the mode is
re-read at most once per second, so removing the file restores writes
without a restart.  ``PLATFORM_READ_ONLY=1`` only *seeds* the sentinel at
start-up; after that the file is the single source of truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

# Non-GET endpoints that already refuse writes themselves.  They are passed
# through so their stable 403/200 behaviour survives the freeze unchanged.
_REFUSED_BY_DESIGN = (
    re.compile(r"^/(?:api/)?store$"),
    re.compile(r"^/prov/activities/[^/]+$"),
)

# POST endpoints that only compute a response (no persistent write).
_READ_ONLY_POSTS = (
    re.compile(r"^/answerable$"),
    re.compile(r"^/namespaces/[^/]+/answerable$"),
    re.compile(r"^/validation/run$"),
    re.compile(r"^/context/resolve$"),
    re.compile(r"^/prov/graph/guard$"),
)

# Blocked endpoints that only append a record instead of changing state.
_APPEND_ONLY = frozenset({"/answer", "/ontology/terms/diff"})
# Blocked endpoints whose only side effect is an exported artifact.
_ARTIFACT_ONLY = frozenset({"/governance/bundle/export"})

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_MODE_TTL_SECONDS = 0.5
_BODY_HASH_LIMIT = 64 * 1024
_QUERY_LIMIT = 2048


def _audit_dir(data_root: Path) -> Path:
    override = os.environ.get("PLATFORM_READONLY_AUDIT_DIR")
    return Path(override) if override else data_root / "audit"


def _audit_path(data_root: Path) -> Path:
    return _audit_dir(data_root) / f"readonly-{date.today():%Y%m%d}.jsonl"


def _since_text(sentinel: Path) -> str | None:
    try:
        return datetime.fromtimestamp(sentinel.stat().st_mtime).astimezone().isoformat(
            timespec="seconds"
        )
    except OSError:
        return None


def _seed_sentinel(data_root: Path) -> None:
    """PLATFORM_READ_ONLY=1 means "freeze from the first request"."""
    flag = os.environ.get("PLATFORM_READ_ONLY", "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return
    sentinel = data_root / "READONLY"
    if not sentinel.exists():
        data_root.mkdir(parents=True, exist_ok=True)
        sentinel.touch()


def _classify(path: str) -> str:
    if path in _APPEND_ONLY:
        return "W2"
    if path in _ARTIFACT_ONLY:
        return "A"
    return "W"


def _write_audit(record: dict[str, Any], data_root: Path) -> None:
    path = _audit_path(data_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
    except OSError as exc:  # audit must never break the 409 itself
        print(f"readonly: audit write failed: {exc}", flush=True)


def readonly_status(data_root: str | Path, audit_dir: str | Path | None = None) -> dict[str, Any]:
    """Snapshot for ``GET /readonly`` (reads the sentinel, no cache)."""
    root = Path(data_root)
    sentinel = root / "READONLY"
    frozen = sentinel.exists()
    directory = Path(audit_dir) if audit_dir else _audit_dir(root)
    path = directory / f"readonly-{date.today():%Y%m%d}.jsonl"
    blocked = 0
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if '"event":"blocked"' in line:
                        blocked += 1
        except OSError:
            pass
    return {
        "mode": "read_only" if frozen else "read_write",
        "since": _since_text(sentinel) if frozen else None,
        "sentinel": str(sentinel),
        "auditFile": str(path),
        "blockedToday": blocked,
    }


class ReadOnlyGuard:
    """ASGI middleware: 409 for writes while the sentinel file exists."""

    def __init__(self, app: Any, data_root: str) -> None:
        self.app = app
        self.data_root = Path(data_root)
        self.sentinel = self.data_root / "READONLY"
        _seed_sentinel(self.data_root)
        self._checked_at = 0.0
        self._frozen = self.sentinel.exists()
        self._since = _since_text(self.sentinel) if self._frozen else None

    def _mode(self) -> bool:
        now = time.monotonic()
        if now - self._checked_at < _MODE_TTL_SECONDS:
            return self._frozen
        self._checked_at = now
        try:
            stat = self.sentinel.stat()
            self._frozen = True
            self._since = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(
                timespec="seconds"
            )
        except FileNotFoundError:
            self._frozen = False
            self._since = None
        except OSError:
            # Keep the previous verdict: a permission glitch must not flip the mode.
            pass
        return self._frozen

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", "/"))
        if method in _SAFE_METHODS:
            await self.app(scope, receive, send)
            return

        refused = any(pattern.match(path) for pattern in _REFUSED_BY_DESIGN)
        read_only = any(pattern.match(path) for pattern in _READ_ONLY_POSTS)
        frozen = self._mode()

        if frozen and not refused and not read_only:
            await self._reject(scope, receive, send, method, path)
            return
        if refused or read_only:
            # Allowed non-GET traffic is recorded in both modes, so the audit
            # shows what was let through as well as what was blocked.
            self._audit_allow(scope, method, path, "X" if refused else "R")
        await self.app(scope, receive, send)

    def _audit_allow(self, scope: dict[str, Any], method: str, path: str, rule: str) -> None:
        _write_audit(
            self._record(scope, method, path, "allow_" + ("refused_by_design" if rule == "X" else "read"), rule),
            self.data_root,
        )

    def _record(
        self,
        scope: dict[str, Any],
        method: str,
        path: str,
        event: str,
        rule: str,
        body_bytes: int | None = None,
        body_sha: str | None = None,
    ) -> dict[str, Any]:
        client = scope.get("client") or ("", 0)
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        query = scope.get("query_string", b"").decode("latin-1")
        return {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event": event,
            "mode": "read_only" if self._frozen else "read_write",
            "since": self._since,
            "auditId": uuid.uuid4().hex[:16],
            "method": method,
            "path": path,
            "query": query[:_QUERY_LIMIT],
            "client": f"{client[0]}:{client[1]}",
            "userAgent": headers.get("user-agent", ""),
            "rule": rule,
            "bodyBytes": body_bytes,
            "bodySha256": body_sha,
            "pid": os.getpid(),
        }

    async def _reject(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        method: str,
        path: str,
    ) -> None:
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        declared = headers.get("content-length")
        body_bytes: int | None = None
        body_sha: str | None = None
        try:
            if declared is not None and int(declared) > _BODY_HASH_LIMIT:
                body_bytes = int(declared)
            else:
                hasher = hashlib.sha256()
                size = 0
                while True:
                    message = await receive()
                    if message.get("type") != "http.request":
                        break
                    chunk = message.get("body", b"")
                    if chunk:
                        size += len(chunk)
                        if size <= _BODY_HASH_LIMIT:
                            hasher.update(chunk)
                    if not message.get("more_body", False):
                        break
                body_bytes = size
                body_sha = hasher.hexdigest() if size <= _BODY_HASH_LIMIT else None
        except (OSError, ValueError):
            pass

        record = self._record(scope, method, path, "blocked", _classify(path), body_bytes, body_sha)
        _write_audit(record, self.data_root)

        payload = {
            "error": {
                "code": "Conflict",
                "provider": "platform",
                "providerCode": "E_PLATFORM_READ_ONLY",
                "message": (
                    "platform is in read-only freeze; writes are disabled until "
                    "the freeze is lifted"
                ),
                "retryable": True,
                "details": {
                    "method": method,
                    "path": path,
                    "mode": "read_only",
                    "auditId": record["auditId"],
                    "since": self._since,
                },
            }
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 409,
                "headers": [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"x-platform-mode", b"read-only"),
                    (b"x-audit-id", record["auditId"].encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
