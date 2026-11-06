"""Build doc/_fsldm/fsldm-metrics.ttl from platform.metric_definition (B-05).

Rules (see doc/_design/50-B05-指标词表入SKOS.md):
  * one skos:Concept per metric row (85 = 79 main + 6 variants);
  * prefLabel@zh = name_zh, altLabel = display_name / unique short forms;
  * notation = metric_id (unique), definition = first sentence of definition;
  * variants carry skos:broader -> family index plus metric:variant true;
  * calculation fields (formula/window/aggregation/grain/unit) stay in PostgreSQL.

Namespace: every concept lives under term: unless its surface collides with one of
the 18 business aliases in fsldm-terms.ttl; colliding metrics move to metric:.

The generator only reads PostgreSQL (via the running platform postgres container)
and rewrites fsldm-metrics.ttl next to this file. It is idempotent: same input
rows produce byte-identical TTL.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMS = HERE / "fsldm-terms.ttl"
OUT = HERE / "fsldm-metrics.ttl"

PSQL = [
    "docker", "exec", "-e", "PGPASSWORD=platform_dev", "agent-platform-postgres",
    "psql", "-U", "platform", "-d", "platform", "-A", "-t", "-c",
    "SELECT json_agg(t) FROM (SELECT metric_id, name_zh, display_name, definition, "
    "variant_of, domain FROM platform.metric_definition ORDER BY metric_id) t;",
]

BRACKET = re.compile(r"〔[^〕]*〕")


def clean_display(value: str) -> str:
    return BRACKET.sub("", value or "").strip()


def base_name(value: str) -> str:
    text = value or ""
    cut = text.find("（")
    if cut < 0:
        cut = text.find("(")
    return (text[:cut] if cut > 0 else text).strip()


def first_sentence(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    for mark in ("。", "；", ";"):
        cut = text.find(mark)
        if cut >= 0 and text[cut + 1:].strip():
            return text[:cut + 1]
    return text


def escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def load_rows() -> list[dict]:
    raw = subprocess.run(PSQL, capture_output=True, check=True).stdout.decode("utf-8").strip()
    return json.loads(raw)


def build(rows: list[dict], term_surfaces: set[str]) -> tuple[str, dict]:
    pref: dict[str, str] = {}
    alts: dict[str, list[str]] = {}
    for row in rows:
        metric_id = row["metric_id"]
        pref[metric_id] = row["name_zh"].strip()
        candidates = []
        display = clean_display(row.get("display_name") or "")
        if display and display != pref[metric_id]:
            candidates.append(display)
        base = base_name(row["name_zh"])
        if base and base != pref[metric_id]:
            candidates.append(base)
        compact = re.sub(r"\s+", "", row["name_zh"])
        if compact and compact != pref[metric_id]:
            candidates.append(compact)
        if "→" in row["name_zh"]:
            candidates.append(row["name_zh"].replace("→", "").strip())
        row["_candidates"] = list(dict.fromkeys(candidates))

    counts: dict[str, int] = {}
    pref_owner = {value: mid for mid, value in pref.items()}
    for row in rows:
        for item in row["_candidates"]:
            counts[item] = counts.get(item, 0) + 1
    dropped: list[str] = []
    for row in rows:
        kept = []
        for item in row["_candidates"]:
            owner = pref_owner.get(item)
            if owner is not None and owner != row["metric_id"]:
                dropped.append(item)
                continue
            if counts[item] > 1 and row.get("variant_of"):
                dropped.append(item)
                continue
            kept.append(item)
        alts[row["metric_id"]] = kept

    colliding = sorted(
        {s for mid in pref for s in ([pref[mid]] + alts[mid]) if s in term_surfaces}
    )

    def concept_iri(metric_id: str) -> str:
        surfaces = {pref[metric_id]} | set(alts[metric_id])
        prefix = "https://w3id.org/fsldm/metrics#" if surfaces & term_surfaces else "https://w3id.org/fsldm/terms#"
        return f"{prefix}M-{metric_id}"

    def subject_of(iri: str) -> str:
        return f"metric:M-{iri.split('#M-')[-1]}" if iri.startswith("https://w3id.org/fsldm/metrics#") else f"term:M-{iri.split('#M-')[-1]}"

    lines = [
        "# =============================================================================",
        "# FS-LDM 指标词表 · SKOS 术语层（B-05）",
        "#",
        f"# 来源：platform.metric_definition（{len(rows)} 行 = "
        f"{len(rows) - sum(1 for row in rows if row.get('variant_of'))} 主 + "
        f"{sum(1 for row in rows if row.get('variant_of'))} 变体）。",
        "# 每行一个 skos:Concept：prefLabel@zh=name_zh，altLabel=display_name/唯一简称，",
        "# notation=metric_id，definition=definition 首句；变体 skos:broader 指向族索引。",
        "# 公式/窗口/聚合/grain/unit/fact_function 等计算字段仍在 PostgreSQL，不入 SKOS。",
        "# 概念默认挂 term: 命名空间；与 18 条业务别名词面冲突者改挂 metric: 命名空间。",
        "# 生成：doc/_fsldm/build_metrics_skos.py（只读 PG，不改 PG）。",
        "# =============================================================================",
        "",
        "@prefix skos:   <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl:    <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix dct:    <http://purl.org/dc/terms/> .",
        "@prefix term:   <https://w3id.org/fsldm/terms#> .",
        "@prefix metric: <https://w3id.org/fsldm/metrics#> .",
        "",
        "# ---- 词表声明 --------------------------------------------------------------",
        "term:MetricScheme a skos:ConceptScheme ;",
        '    skos:prefLabel "FS-LDM 指标词表"@zh ;',
        '    skos:prefLabel "FS-LDM Metric Vocabulary"@en ;',
        '    dct:source "platform.metric_definition" .',
        "",
    ]

    for row in rows:
        metric_id = row["metric_id"]
        subject = subject_of(concept_iri(metric_id))
        lines.append(f"{subject} a skos:Concept ;")
        lines.append("    skos:inScheme term:MetricScheme ;")
        lines.append(f'    skos:prefLabel "{escape(pref[metric_id])}"@zh ;')
        for alt in alts[metric_id]:
            lines.append(f'    skos:altLabel "{escape(alt)}"@zh ;')
        lines.append(f'    skos:notation "{escape(metric_id)}" ;')
        lines.append(f'    skos:definition "{escape(first_sentence(row.get("definition") or ""))}"@zh ;')
        if row.get("domain"):
            lines.append(f'    dct:subject "{escape(row["domain"])}"@zh ;')
        parent = row.get("variant_of")
        if parent:
            lines.append(f"    skos:broader {subject_of(concept_iri(parent))} ;")
            lines.append("    metric:variant true ;")
        lines.append('    dct:source "platform.metric_definition" .')
        lines.append("")

    lines.append("# 变体上界校验标记：6 个变体必须写 skos:broader（见 data/shapes/fsldm/metrics.ttl）")
    lines.append("")

    summary = {
        "rows": len(rows),
        "concepts": len(rows),
        "variants": sum(1 for row in rows if row.get("variant_of")),
        "collisionSurfaces": colliding,
        "collisionCount": len(colliding),
        "metricPrefixed": sorted(
            row["metric_id"] for row in rows
            if concept_iri(row["metric_id"]).startswith("https://w3id.org/fsldm/metrics#")
        ),
        "droppedAmbiguousAltLabels": sorted(set(dropped)),
    }
    return "\n".join(lines), summary


def main() -> None:
    rows = load_rows()
    term_surfaces = {
        match.group(1).strip()
        for match in re.finditer(r'"([^"]+)"@(zh|en)', TERMS.read_text(encoding="utf-8"))
    }
    text, summary = build(rows, term_surfaces)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
