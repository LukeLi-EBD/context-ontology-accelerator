"""Bootstrap ontology on serve startup (`ontology.init_mode`).

S1 uses a polling thread, not file-system events (Windows bind mounts do not
report events reliably).

Startup gate (05 section 1.3): on the initial run, a failed import/publish or a
missing T-Box (no source and no published pointer) keeps the platform from
starting (`E_ONTOLOGY_INIT_FAILED` -> 78, `E_ONTOLOGY_TBOX_MISSING` -> 69).
A benign skip - unchanged content, or a pointer managed outside the init source
- is not a failure, and an existing published T-Box never blocks startup just
because the bootstrap file was removed. Watch-loop failures after a successful
start are logged and retried; they never take serve down.
"""

from __future__ import annotations

import logging
import threading

from .assembly import Runtime
from .errors import EXIT_CONFIG, EXIT_UNAVAILABLE, PlatformError

log = logging.getLogger(__name__)

TBOX_MISSING_REASON = "source missing"
BENIGN_SKIP_REASONS = ("unchanged", "pointer managed outside init source")

_stop = threading.Event()
_thread: threading.Thread | None = None


def run_once(runtime: Runtime) -> dict:
    """One attempt for the watch loop: never raises, failures are returned."""
    cfg = runtime.config.ontology
    try:
        result = runtime.ontology.bootstrap(cfg.init_source, cfg.init_semver)
    except Exception as exc:  # noqa: BLE001 - watch must survive every failure
        log.warning(
            "ontology init failed",
            extra={"event": {"event": "ontology_init_failed", "error": str(exc)}},
        )
        return {"status": "failed", "error": str(exc)}
    log.info(
        "ontology init finished",
        extra={"event": {"event": "ontology_init", "result": result}},
    )
    return result


def _has_published_tbox(runtime: Runtime) -> bool:
    try:
        return bool(runtime.ontology.current())
    except Exception:  # noqa: BLE001 - only used to soften the missing-source gate
        return False


def enforce_startup(runtime: Runtime, result: dict) -> None:
    """Turn the initial result into a blocking error when 05 section 1.3 says so."""
    cfg = runtime.config.ontology
    if result.get("status") == "failed":
        raise PlatformError(
            code="E_ONTOLOGY_INIT_FAILED",
            detail=str(result.get("error") or "ontology bootstrap failed"),
            stage="ontology",
            key="ontology.init_source",
            provider="platform",
            hint=(
                "Fix the T-Box at ontology.init_source or align ontology.init_semver; "
                "serve does not start with an invalid T-Box"
            ),
            exit_code=EXIT_CONFIG,
        )
    if (
        result.get("status") == "skipped"
        and result.get("reason") == TBOX_MISSING_REASON
        and not _has_published_tbox(runtime)
    ):
        raise PlatformError(
            code="E_ONTOLOGY_TBOX_MISSING",
            detail=f"T-Box source missing and no published pointer: {cfg.init_source}",
            stage="ontology",
            key="ontology.init_source",
            provider="platform",
            hint=(
                "Provide the T-Box file, or set ontology.init_mode=off only when a "
                "published pointer already exists"
            ),
            exit_code=EXIT_UNAVAILABLE,
        )


def start(runtime: Runtime) -> dict:
    global _thread
    cfg = runtime.config.ontology
    if cfg.init_mode == "off":
        return {"mode": "off", "initial": None}
    initial = run_once(runtime)
    enforce_startup(runtime, initial)
    state = {"mode": cfg.init_mode, "initial": initial}
    if cfg.init_mode != "watch":
        return state

    _stop.clear()

    def loop() -> None:
        while not _stop.wait(cfg.watch_interval_seconds):
            run_once(runtime)

    if _thread is None or not _thread.is_alive():
        _thread = threading.Thread(target=loop, name="ontology-watch", daemon=True)
        _thread.start()
    return state


def stop() -> None:
    global _thread
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=2.0)
        _thread = None
