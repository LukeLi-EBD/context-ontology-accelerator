"""Prove the catalog is S1's JsonDataSourceLookup *consumed by* coa_metrics.validator.

Builds the lookup from ``COA_PROVIDER_SOURCE_CATALOG=json``, wraps it in a recorder,
then calls the real ``validate_metric``. Prints the consumer's file, the call chain
and per-method call counts — no private copy of the validation rules anywhere.

    docker run --rm --network platform-acceptance_default --entrypoint python \
      -e COA_SOURCE_CATALOG_JSON_PATH=/repo/doc/_evidence-coa-integration/s1-2026-11-08/snapshot/catalog.json \
      -e PYTHONPATH=/repo/libs/common/src:/repo/packages/context-manager/src:/repo/packages/metric-service/src:/repo/packages/local-providers/src:/repo/packages/coa-gateway/src \
      -v <repo>:/repo:ro coa-gateway-verify:0.1 \
      /repo/packages/coa-gateway/scripts/prove_catalog_validator.py
"""

from __future__ import annotations

import inspect
import json
import os
import sys
from collections import Counter
from typing import Any

from coa_gateway import ProviderSettings, build_gateway

DEFAULT_SNAPSHOT = "/repo/doc/_evidence-coa-integration/s1-2026-11-08/snapshot/catalog.json"

BODY = {
    "dataSourceId": "platform",
    "sourceTable": "platform.bank_collection_case",
    "expression": {
        "dialects": [
            {
                "dialect": "TRINO",
                "expression": "SELECT case_id, case_status FROM platform.bank_collection_case",
            }
        ]
    },
}


class RecordingLookup:
    """Transparent proxy: forwards everything, records who called from where."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.calls: Counter[str] = Counter()
        self.frames: set[str] = set()

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.calls[name] += 1
            for frame in inspect.stack():
                if "validator.py" in frame.filename and "metric-service" in frame.filename:
                    self.frames.add(frame.function)
            return attr(*args, **kwargs)

        return wrapper


def main() -> int:
    import coa_metrics.validator as validator_module
    from coa_metrics.validator import validate_metric
    from coa_local_providers.json_lookup import JsonDataSourceLookup

    snapshot = os.environ.get("COA_SOURCE_CATALOG_JSON_PATH", DEFAULT_SNAPSHOT)
    gateway = build_gateway(
        ProviderSettings.from_mapping(
            {
                "COA_PROVIDER_SOURCE_CATALOG": "json",
                "COA_SOURCE_CATALOG_JSON_PATH": snapshot,
                "COA_PROVIDER_GRAPH": "none",
                "COA_PROVIDER_VECTOR": "none",
            }
        )
    )
    lookup = gateway.source_catalog
    recorder = RecordingLookup(lookup)
    result = validate_metric(BODY, data_sources_lookup=recorder)

    payload = {
        "catalog": {
            "built_by": "COA_PROVIDER_SOURCE_CATALOG=json",
            "class": f"{type(lookup).__module__}.{type(lookup).__qualname__}",
            "is_s1_class": type(lookup) is JsonDataSourceLookup,
            "snapshot": snapshot,
        },
        "validator": {
            "module": validator_module.__name__,
            "file": validator_module.__file__,
            "function": "validate_metric",
        },
        "call_chain": sorted(recorder.frames),
        "call_counts": {"total": sum(recorder.calls.values()), "by_method": dict(recorder.calls)},
        "result": {"valid": result.valid, "errors": result.errors, "warnings": [w["check"] for w in result.warnings]},
    }
    checks = {
        "is_s1_class": payload["catalog"]["is_s1_class"],
        "consumer_is_coa_metrics": "coa_metrics.validator" in payload["validator"]["module"],
        "validator_frames_seen": {"validate_metric", "_check_table_references"}.issubset(recorder.frames),
        "lookup_was_called": sum(recorder.calls.values()) > 0,
        "validation_valid": result.valid,
    }
    payload["checks"] = checks
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    ok = all(checks.values())
    print("NO_REWRITE OK" if ok else "NO_REWRITE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
