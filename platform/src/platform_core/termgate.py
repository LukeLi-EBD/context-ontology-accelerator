"""O-05 T-Box publish gate for terminology governance.

The existing ``termgov`` checks govern *term registry imports* only.  This
module plugs the same checks into the T-Box publish path with three
configurable tiers (``terms.gate`` = off / warn / block):

* ``off``  – the gate is not evaluated at all; publish output is untouched.
* ``warn`` – findings are attached to the publish response and evidence pack,
  but publishing is not blocked.
* ``block`` – blocking-level findings abort publishing before any version or
  graph row is written; the caller receives ``E_TERM_GATE_BLOCKED``.

Severity mapping is configurable via ``terms.blocking_codes``.  Codes not in
that list are warnings.  A relative coverage decline larger than
``terms.coverage_decrease_tolerance`` adds a warning-level
``TERM_COVERAGE_DECREASE`` finding.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import termgov
from .config import TermsConfig

E_TERM_GATE_BLOCKED = "E_TERM_GATE_BLOCKED"

COVERAGE_METRICS = (
    "conceptPrefCoverage",
    "conceptDefinitionCoverage",
    "conceptNotationCoverage",
    "aliasTargetCoverage",
)
COVERAGE_DECREASE_CODE = "TERM_COVERAGE_DECREASE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def terms_config(obj: Any) -> TermsConfig | None:
    """Return ``obj.config.terms`` when present (runtime or registry)."""
    config = getattr(obj, "config", None)
    terms = getattr(config, "terms", None)
    return terms if isinstance(terms, TermsConfig) else None


def evaluate_snapshot(
    snapshot: dict[str, Any],
    config: TermsConfig,
    *,
    baseline: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Classify findings and build the publish-gate result.

    ``off`` returns ``None`` so callers can leave the publish payload
    byte-for-byte unchanged.  ``baseline`` is a ``termgov.graph_coverage``
    report for the currently published T-Box (used for decline warnings).
    """
    if config.gate == "off":
        return None

    report = termgov.coverage(snapshot, source="publish")
    blocking_codes = {str(code) for code in (config.blocking_codes or [])}
    findings: list[dict[str, Any]] = []
    for item in report["conflicts"]:
        mapped = dict(item)
        is_blocking = mapped.get("code") in blocking_codes
        mapped["defaultBlocking"] = bool(item.get("blocking"))
        mapped["blocking"] = is_blocking
        mapped["severity"] = "blocking" if is_blocking else "warning"
        findings.append(mapped)

    actual = report["actual"]
    baseline_actual = (baseline or {}).get("actual") if baseline else None
    declines: list[dict[str, Any]] = []
    if isinstance(baseline_actual, dict):
        for metric in COVERAGE_METRICS:
            previous = baseline_actual.get(metric)
            current = actual.get(metric)
            if not isinstance(previous, (int, float)) or not isinstance(current, (int, float)):
                continue
            delta = round(float(current) - float(previous), 4)
            if delta < 0 and abs(delta) > float(config.coverage_decrease_tolerance) + 1e-9:
                declines.append({
                    "metric": metric,
                    "previous": previous,
                    "current": current,
                    "delta": delta,
                })
                findings.append({
                    "code": COVERAGE_DECREASE_CODE,
                    "severity": "warning",
                    "blocking": False,
                    "defaultBlocking": False,
                    "metric": metric,
                    "previous": previous,
                    "current": current,
                    "message": f"{metric} decreased from {previous} to {current}",
                })

    blocking = sum(1 for item in findings if item["blocking"])
    warnings = len(findings) - blocking
    blocked = config.gate == "block" and blocking > 0
    if blocked:
        verdict = "blocked"
    elif findings:
        verdict = "warned"
    else:
        verdict = "pass"

    result: dict[str, Any] = {
        "gate": config.gate,
        "verdict": verdict,
        "blocked": blocked,
        "enforced": config.gate == "block",
        "blocking": blocking,
        "warnings": warnings,
        "total": len(findings),
        "blockingCodes": sorted(blocking_codes),
        "coverageDecreaseTolerance": float(config.coverage_decrease_tolerance),
        "coverage": {
            "actual": actual,
            "baseline": {
                metric: baseline_actual.get(metric)
                for metric in COVERAGE_METRICS
                if isinstance(baseline_actual, dict)
            } if isinstance(baseline_actual, dict) else None,
            "declines": declines,
        },
        "findings": findings,
        "checkedAt": _now(),
        "readOnly": True,
    }
    if context:
        result.update({key: value for key, value in context.items() if value is not None})
    return result


def evaluate_content(
    content: str,
    fmt: str,
    config: TermsConfig,
    *,
    baseline: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Parse staged T-Box content and evaluate the gate (``None`` for off)."""
    if config.gate == "off":
        return None
    snapshot = termgov.parse_skos(content, fmt)
    return evaluate_snapshot(snapshot, config, baseline=baseline, context=context)


def remember(target: Any, result: dict[str, Any] | None) -> None:
    """Keep the most recent non-off gate result on the registry instance."""
    if result is None:
        return
    try:
        setattr(target, "_last_terms_gate", result)
    except Exception:  # pragma: no cover - defensive for slotted doubles
        pass


def last_result(target: Any) -> dict[str, Any] | None:
    result = getattr(target, "_last_terms_gate", None)
    return result if isinstance(result, dict) else None


def status(runtime: Any) -> dict[str, Any]:
    """Configured tier + most recent result (``None`` + reason when absent)."""
    config = terms_config(runtime)
    registry = getattr(runtime, "ontology", None)
    last = last_result(registry)
    gate = getattr(config, "gate", None) if config is not None else None
    if config is None:
        reason = "runtime config 中没有 terms 配置块，无法判断当前档位"
    elif gate == "off":
        reason = "terms.gate=off：本进程没有执行术语核对"
    else:
        reason = "本进程尚无发布尝试，未产生术语门禁结果"
    return {
        "configuredGate": gate,
        "blockingCodes": list(config.blocking_codes) if config is not None else None,
        "coverageDecreaseTolerance": (
            float(config.coverage_decrease_tolerance) if config is not None else None
        ),
        "last": last,
        "empty": last is None,
        "emptyReason": None if last is not None else reason,
        "readOnly": True,
        "generatedAt": _now(),
    }
