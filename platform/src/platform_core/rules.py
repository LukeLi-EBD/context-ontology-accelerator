"""Generic rule-set executor (output_mode = rule_set).

The executor reads ``platform.metric_definition.rule_set_json``. Rules written
before v6 carry only human wording; v6 added a machine-readable ``spec`` object
next to each rule, so the executor evaluates declared fields only and never
parses Chinese thresholds. Missing fields are reported as "unevaluated"; they
never silently count as "not triggered".

No facts in -> typed "no data" error. There is no default 0.
"""

from __future__ import annotations

from typing import Any

from .adapters.metadata_pg import MetadataPg
from .errors import PortError

NOT_RULE_SET = "E_METRIC_NOT_RULE_SET"
NO_DATA = "E_METRIC_NO_DATA"


class RuleExecutor:
    port = "RuleExecutor"

    def __init__(self, metadata: MetadataPg) -> None:
        self._meta = metadata

    def execute(
        self,
        metric_id: str,
        facts: list[dict[str, Any]],
        as_of: str | None = None,
    ) -> dict[str, Any]:
        rows = self._meta.query(
            "SELECT metric_id, output_mode, rule_set_json "
            "FROM platform.metric_definition WHERE metric_id = %s",
            (metric_id,),
        )
        if not rows:
            raise PortError(
                code="NotFound",
                message=f"unknown metric: {metric_id}",
                provider="platform",
                provider_code="E_METRIC_NOT_FOUND",
                details={"metricId": metric_id},
            )
        row = rows[0]
        if row["output_mode"] != "rule_set" or not isinstance(row["rule_set_json"], list):
            raise PortError(
                code="InvalidArgument",
                message=f"metric is not a rule-set metric: {metric_id}",
                provider="platform",
                provider_code=NOT_RULE_SET,
                details={"metricId": metric_id, "missing": "rule_set"},
            )
        rules = row["rule_set_json"]
        if not facts:
            raise PortError(
                code="InvalidArgument",
                message="no facts supplied; rule set cannot be evaluated",
                provider="platform",
                provider_code=NO_DATA,
                details={"metricId": metric_id, "missing": "data"},
            )

        hits: list[dict[str, Any]] = []
        customers: list[dict[str, Any]] = []
        skipped: dict[str, list[str]] = {}
        for fact in facts:
            fact_date = fact.get("asOf") or fact.get("as_of")
            if as_of and fact_date and str(fact_date) != as_of:
                continue
            triggered: list[str] = []
            for rule in rules:
                spec = rule.get("spec")
                if not isinstance(spec, dict):
                    continue
                ok, detail, missing = _evaluate(spec, fact)
                if missing:
                    skipped.setdefault(rule["id"], []).append(
                        fact.get("customerId") or fact.get("customer_no") or "?"
                    )
                    continue
                if ok:
                    triggered.append(rule["id"])
                    hits.append(
                        {
                            "ruleId": rule["id"],
                            "level": rule.get("level"),
                            "signal": rule.get("signal"),
                            "customerId": fact.get("customerId")
                            or fact.get("customer_no"),
                            "fields": detail,
                        }
                    )
            customers.append(
                {
                    "customerId": fact.get("customerId") or fact.get("customer_no"),
                    "level": _aggregate_level(triggered, rules),
                    "triggered": triggered,
                }
            )

        level = _aggregate_level(
            [hit["ruleId"] for hit in hits], rules
        )
        return {
            "metricId": metric_id,
            "outputMode": "rule_set",
            "asOf": as_of,
            "ruleCount": len(rules),
            "triggeredCount": len(hits),
            "level": level,
            "hits": hits,
            "customers": customers,
            "unevaluatedRules": sorted(skipped),
            "factsEvaluated": len(customers),
        }


def _aggregate_level(rule_ids: list[str], rules: list[dict]) -> str | None:
    levels = {rule["id"]: rule.get("level") for rule in rules}
    hit_levels = [levels.get(rule_id) for rule_id in rule_ids]
    if "L3" in hit_levels:
        return "L3"
    l2 = sum(1 for level in hit_levels if level == "L2")
    l1 = sum(1 for level in hit_levels if level == "L1")
    if l2 >= 2 or (l2 >= 1 and l1 >= 2):
        return "L2"
    if l1 >= 1:
        return "L1"
    return None


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _evaluate(
    spec: dict[str, Any], fact: dict[str, Any]
) -> tuple[bool, dict[str, Any], bool]:
    """Return (triggered, observed fields, missing_field?)."""
    op = spec.get("op")
    if op == "gte":
        value = _num(fact.get(spec["field"]))
        if value is None:
            return False, {}, True
        return value >= float(spec["value"]), {spec["field"]: value}, False
    if op == "lte":
        value = _num(fact.get(spec["field"]))
        if value is None:
            return False, {}, True
        return value <= float(spec["value"]), {spec["field"]: value}, False
    if op == "equals":
        value = fact.get(spec["field"])
        if value is None:
            return False, {}, True
        return str(value) == str(spec["value"]), {spec["field"]: value}, False
    if op == "ratio_gte" or op == "ratio_lte":
        numerator = _num(fact.get(spec["numerator"]))
        denominator = _num(fact.get(spec["denominator"]))
        if numerator is None or denominator is None:
            return False, {}, True
        ratio = None if denominator == 0 else numerator / denominator
        if ratio is None:
            return False, {"numerator": numerator, "denominator": denominator}, False
        ok = ratio >= float(spec["value"]) if op == "ratio_gte" else ratio <= float(spec["value"])
        return ok, {
            spec["numerator"]: numerator,
            spec["denominator"]: denominator,
            "ratio": round(ratio, 6),
        }, False
    if op == "any_true":
        values = {field: fact.get(field) for field in spec["fields"]}
        if all(value is None for value in values.values()):
            return False, {}, True
        return any(bool(value) for value in values.values()), values, False
    if op == "downgrade":
        prev = fact.get(spec["prev"])
        curr = fact.get(spec["curr"])
        if prev is None or curr is None:
            return False, {}, True
        if "scale" in spec:
            scale = list(spec["scale"])
            if prev not in scale or curr not in scale:
                return False, {spec["prev"]: prev, spec["curr"]: curr}, False
            drop = scale.index(curr) - scale.index(prev)
        else:
            prev_n, curr_n = _num(prev), _num(curr)
            if prev_n is None or curr_n is None:
                return False, {}, True
            drop = prev_n - curr_n
        return drop >= float(spec["value"]), {
            spec["prev"]: prev,
            spec["curr"]: curr,
            "drop": drop,
        }, False
    if op == "band_cross":
        start = _num(fact.get(spec["start"]))
        end = _num(fact.get(spec["end"]))
        if start is None or end is None:
            return False, {}, True
        return (
            start >= float(spec["from"]) and end >= float(spec["to"])
        ), {spec["start"]: start, spec["end"]: end}, False
    if op == "drop_gte":
        current = _num(fact.get(spec["field"]))
        baseline = _num(fact.get(spec["baseline"]))
        if current is None or baseline is None or baseline == 0:
            return False, {}, True
        drop = (baseline - current) / baseline
        return drop >= float(spec["value"]), {
            spec["field"]: current,
            spec["baseline"]: baseline,
            "dropRatio": round(drop, 6),
        }, False
    if op == "any_of":
        observed: dict[str, Any] = {}
        missing = True
        hit = False
        for clause in spec["clauses"]:
            ok, detail, was_missing = _evaluate(clause, fact)
            if not was_missing:
                missing = False
            observed.update(detail)
            hit = hit or ok
        if missing:
            return False, {}, True
        return hit, observed, False
    raise PortError(
        code="InvalidArgument",
        message=f"unsupported rule op: {op}",
        provider="platform",
        provider_code="E_METRIC_RULE_INVALID",
        details={"op": op},
    )
