"""O-05 T-Box publish gate for terminology governance.

The existing ``termgov`` checks govern *term registry imports* only.  This
module plugs the same checks into the T-Box publish path with three
configurable tiers (``terms.gate`` = off / warn / block):

* ``off``  – no ratio/conflict findings are attached; publish output is
  byte-for-byte unchanged **except** for the vocab-zero guard below.
* ``warn`` – findings are attached to the publish response and evidence pack,
  but publishing is not blocked.
* ``block`` – blocking-level findings abort publishing before any version or
  graph row is written; the caller receives ``E_TERM_GATE_BLOCKED``.

Severity mapping is configurable via ``terms.blocking_codes``.  Codes not in
that list are warnings.  A relative coverage decline larger than
``terms.coverage_decrease_tolerance`` adds a warning-level
``TERM_COVERAGE_DECREASE`` finding.

Vocab-zero guard (not configurable, not tier-dependent): publishing must not
collapse the *effective* term set to zero when the high-water mark was
non-zero.  The only exemption is an explicit ``purpose=smoke`` call, and the
exemption is recorded in the evidence pack with actor / path / baseline.
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
VOCAB_ZERO_CODE = "TERM_VOCAB_ZERO"
VOCAB_ZERO_EXEMPT_CODE = "TERM_VOCAB_ZERO_EXEMPTED"
SMOKE_PURPOSE = "smoke"

# 判据针对"生效术语集"，不针对"T-Box 图内容"：解耦到独立术语命名图/指针后，
# 版本图里没有术语是正常状态；这里比较的是发布后生效术语集相对高水位是否清零。
VOCAB_PREDICATE = (
    "high_water.conceptsInScheme > 0 and effective.conceptsInScheme == 0 "
    "=> blocking, independent of terms.gate; only purpose=smoke may exempt"
)



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
    high_water: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Classify findings and build the publish-gate result.

    ``off`` returns ``None`` unless the vocab-zero guard fires, so callers can
    leave the publish payload byte-for-byte unchanged in the normal case.
    ``baseline`` is a ``termgov.graph_coverage`` report for the currently
    published T-Box (used for decline warnings).  ``high_water`` is the last
    non-zero effective term-set measurement (see ``platform.term_high_water``);
    it is what the zero guard compares against, so multiple consecutive
    collapses are caught even when the current pointer is already empty.
    """
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

    # --- vocab-zero guard: effective term set vs high-water mark -----------
    actual_metric = int(actual.get("conceptsInMetricScheme") or 0)
    actual_aliases = int(actual.get("aliases") or 0)
    hw = high_water if isinstance(high_water, dict) else {}
    hw_metric = int(hw.get("conceptsInScheme") or 0)
    hw_aliases = int(hw.get("aliases") or 0)
    effective = {"conceptsInScheme": actual_metric, "aliases": actual_aliases}
    high_water_block = {
        "conceptsInScheme": hw_metric,
        "aliases": hw_aliases,
        "versionId": hw.get("versionId"),
        "graph": hw.get("graph"),
        "updatedAt": hw.get("updatedAt"),
    }
    zero_fired = hw_metric > 0 and actual_metric == 0
    zero_finding: dict[str, Any] | None = None
    exemption: dict[str, Any] | None = None
    if zero_fired:
        if str((context or {}).get("purpose") or "").strip().lower() == SMOKE_PURPOSE:
            exemption = {
                "purpose": SMOKE_PURPOSE,
                "actor": (context or {}).get("actor"),
                "path": (context or {}).get("path"),
                "versionId": (context or {}).get("versionId"),
                "baseline": high_water_block,
                "current": effective,
                "reason": "purpose=smoke 显式豁免：自检探针允许发布不含术语的 T-Box 版本",
                "exemptedAt": _now(),
            }
            zero_finding = {
                "code": VOCAB_ZERO_EXEMPT_CODE,
                "severity": "warning",
                "blocking": False,
                "defaultBlocking": True,
                "forced": False,
                "exemption": exemption,
                "baseline": high_water_block,
                "current": effective,
                "message": (
                    f"生效术语集从 {hw_metric} 掉到 0，按 purpose=smoke 豁免放行；"
                    "豁免已写入证据包"
                ),
            }
        else:
            zero_finding = {
                "code": VOCAB_ZERO_CODE,
                "severity": "blocking",
                "blocking": True,
                "defaultBlocking": True,
                "forced": True,
                "baseline": high_water_block,
                "current": effective,
                "message": (
                    f"生效术语集的 MetricScheme 概念从 {hw_metric} 掉到 0；"
                    "生产路径一律阻断，不受 terms.gate 档位影响（仅 purpose=smoke 可豁免）"
                ),
            }
        findings.append(zero_finding)

    # ``off`` keeps the original "no findings attached" contract unless the
    # non-configurable vocab guard fires.
    if config.gate == "off":
        if zero_finding is None:
            return None
        findings = [zero_finding]
        declines = []

    blocking = sum(1 for item in findings if item["blocking"])
    warnings = len(findings) - blocking
    forced = sum(1 for item in findings if item.get("forced"))
    blocked = forced > 0 or (config.gate == "block" and blocking > 0)
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
        "enforced": config.gate == "block" or forced > 0,
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
        "vocabGuard": {
            "predicate": VOCAB_PREDICATE,
            "highWater": high_water_block,
            "effective": effective,
            "zeroDrop": zero_fired,
            "forcedBlocking": forced > 0,
            "exemption": exemption,
        },
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
    high_water: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Parse staged T-Box content and evaluate the gate.

    Returns ``None`` only when the gate is off *and* the vocab-zero guard does
    not fire, so the off payload stays byte-for-byte unchanged in the normal
    case.
    """
    snapshot = termgov.parse_skos(content, fmt)
    return evaluate_snapshot(
        snapshot, config, baseline=baseline, high_water=high_water, context=context
    )


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
        reason = "terms.gate=off：不做 ratio/冲突核对，但零术语硬阻断仍然生效（不受档位影响）"
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
