"""Bootstrap ontology on serve startup (`ontology.init_mode`).

S1 uses a polling thread, not file-system events (Windows bind mounts do not
report events reliably). Failures never block the platform: they are recorded in
`platform.ontology_job` and surfaced through /status.
"""

from __future__ import annotations

import logging
import threading

from .assembly import Runtime

log = logging.getLogger(__name__)

_stop = threading.Event()
_thread: threading.Thread | None = None


def run_once(runtime: Runtime) -> dict:
    cfg = runtime.config.ontology
    try:
        result = runtime.ontology.bootstrap(cfg.init_source, cfg.init_semver)
        log.info(
            "ontology init finished",
            extra={"event": {"event": "ontology_init", "result": result}},
        )
        return result
    except Exception as exc:  # keep serve alive; the pointer stays unchanged
        log.warning(
            "ontology init failed",
            extra={"event": {"event": "ontology_init_failed", "error": str(exc)}},
        )
        return {"status": "failed", "error": str(exc)}


def start(runtime: Runtime) -> dict:
    global _thread
    cfg = runtime.config.ontology
    if cfg.init_mode == "off":
        return {"mode": "off"}
    state = {"mode": cfg.init_mode, "initial": run_once(runtime)}
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
