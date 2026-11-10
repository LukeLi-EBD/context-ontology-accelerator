"""External-status judgement for governed metrics.

The report manifest and the metric card must answer "can this metric leave the
building?" the same way. This module is the single source of that rule: both
call sites read the same `platform.metric_definition` row through it instead of
re-implementing the branches.
"""

from __future__ import annotations

from typing import Any

# 行业公式没有监管原文，只能作为内部基线使用。
INDUSTRY_NOTICE = "内部基线、不外报"


def text(value: Any) -> str:
    """Render a possibly-null definition field without inventing content."""
    if value is None:
        return "口径未给出"
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, ensure_ascii=False)
    rendered = str(value).strip()
    return rendered or "口径未给出"


def evidence(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise evidence_basis into a code, label, source and notice."""
    basis = (row.get("evidence_basis") or "none").strip() or "none"
    provenance = (row.get("provenance_label") or "").strip()
    if basis == "regulatory":
        return {
            "code": basis,
            "basisLabel": "监管原文",
            "source": provenance or "监管原文",
            "hasRegulatoryText": True,
        }
    if basis == "industry":
        return {
            "code": basis,
            "basisLabel": "行业通行（未获监管原文）",
            "source": provenance or "行业通行",
            "hasRegulatoryText": False,
            "notice": INDUSTRY_NOTICE,
        }
    return {
        "code": basis,
        "basisLabel": "无证据",
        "source": provenance or "未给出",
        "hasRegulatoryText": False,
    }


def judgement(
    row: dict[str, Any], execution: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return the external status, label, reason and eligibility for one row.

    `execution` is optional: the card does not probe facts, so it gets the
    eligibility-only wording; the manifest passes the execution path so the
    reason can name the blocking reason code.
    """
    tier = (row.get("computability_tier") or "unknown").strip() or "unknown"
    ev = evidence(row)
    publishable = bool(row.get("publishable"))
    eligible = bool(
        publishable and ev["code"] == "regulatory" and tier == "structurally_computable"
    )

    if eligible:
        status = "external_candidate"
        label = "对外可出数候选（需事实与观测）"
        if execution is not None and not execution["executable"]:
            reason = (
                "证据为监管原文、publishable=true、口径结构性可算；"
                f"但当前不可直接 compute（{execution['reasonCode']}）：{execution['reason']}"
            )
        else:
            reason = (
                "证据为监管原文、publishable=true、口径结构性可算；"
                "资格判定未含观测与窗口，实际可执行性见 executionPath"
            )
    elif ev["code"] == "industry":
        status = "internal_baseline"
        label = INDUSTRY_NOTICE
        reason = f"行业公式未获监管原文：{INDUSTRY_NOTICE}"
    elif not publishable:
        status = "unpublishable"
        label = "不可发布"
        reason = "publishable=false"
    else:
        status = "blocked"
        label = "不可对外"
        reason = f"口径未达结构性可算：{tier}"

    return {
        "status": status,
        "label": label,
        "reason": reason,
        "eligible": eligible,
        "tier": tier,
        "evidence": ev,
    }
