"""Bridge between COA's OSI model and ``coa_metrics.validator``.

``parse_osi_yaml`` yields :class:`OsiMetric` objects; ``validate_metric``
expects the camelCase body shape the metric API uses. This module is the only
translation step, so the validator's input is demonstrably derived from the
parsed OSI document rather than from an HTTP response.
"""

from __future__ import annotations

from typing import Any

from coa_metrics.osi_parser import OsiMetric


def metric_body_from_osi(metric: OsiMetric) -> dict[str, Any]:
    """Convert a parsed OSI metric into the validator's ``metric_body`` shape."""
    extension = metric.custom_extensions
    return {
        "dataSourceId": extension.data_source_id if extension else "",
        "sourceTable": extension.source_table if extension else "",
        "expression": {
            "dialects": [
                {"dialect": item.dialect, "expression": item.expression}
                for item in metric.expression
            ]
        },
        "ontologyConcepts": list(extension.ontology_concepts) if extension else [],
    }


__all__ = ["metric_body_from_osi"]
