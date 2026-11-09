"""ABox instance generator for the governed FSLDM T-Box.

The SQL generator (`datagen.py`) only covers the 28 fact tables.  This module
fills the rest of the ontology: every ``owl:Class`` in the governed T-Box gets
instances, and every ``owl:ObjectProperty`` / ``owl:DatatypeProperty`` gets at
least one value path.

Design rules:
* instances live in a dedicated named graph, so they never mix with extracted
  facts or the T-Box itself;
* the same seed rebuilds the same triples (byte-identical, sorted digest);
* object-property values always point at an instance minted by this module,
  therefore there are no dangling references;
* no metric table, binding or T-Box triple is written.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from rdflib import Graph, Literal, OWL, RDF, RDFS, URIRef, XSD
from rdflib.namespace import SKOS

from .errors import PortError

SYNTHETIC_GRAPH = "urn:platform:graph:abox:synthetic"
INSTANCE_BASE = "urn:platform:synthetic"
CONCEPT_BASE = "urn:platform:synthetic/concept"
CONCEPTSCHEME = "urn:platform:synthetic/conceptscheme/fsldm"
PER_CLASS = 200
BATCH = 800

# Main entity classes keep the scale of the SQL fact layer (see _design/40).
ANCHORS: dict[str, int] = {
    "party#Individual": 5000,
    "party#Organization": 500,
    "core#Party": 200,
    "agreement#Policy": 6000,
    "agreement#Application": 2000,
    "agreement#CreditAgreement": 5020,
    "agreement#Account": 5000,
    "core#Product": 500,
    "core#Asset": 1000,
    "core#Event": 6000,
}

DATE_PROPS = {
    "dueDate", "firstPaymentDate", "lastPaymentDate", "maturityDate",
    "originationDate", "observationDate", "attritionDate", "partySince",
    "riskGradeReviewDate",
}
DATETIME_PROPS = {"recordedAt", "eventTimestamp", "eventPostedTimestamp"}
INT_PROPS = {"sessionDuration", "lineNumber"}
BOOL_PROPS = {"isPrimaryRole"}
DECIMAL_PROPS = {
    "ownershipShare", "eventAmount", "creditAmount", "debitAmount",
    "latitude", "longitude", "ratingLowerBound", "ratingUpperBound",
    "leewayLowerBound", "leewayUpperBound", "metricValue",
}

# Entity id prefixes mirror the SQL synthetic keys where one exists.
ID_PROP_PREFIX: dict[str, str] = {
    "partyId": "CUST-SYN",
    "agreementId": "AGR-SYN",
    "accountNumber": "ACC-SYN",
    "assetId": "AST-SYN",
    "eventId": "EVT-SYN",
    "productId": "PRD-SYN",
    "deviceNumber": "DEV-SYN",
    "featureCode": "FTR-SYN",
    "glAccountNumber": "GL-SYN",
    "identificationValue": "IDV-SYN",
    "accountModifierNumber": "MOD-SYN",
}

ANCHOR_IDS: dict[str, str] = {
    "party#Individual": "CUST-SYN",
    "party#Organization": "ORG-SYN",
    "core#Party": "PTY-SYN",
    "agreement#Policy": "POL-SYN",
    "agreement#Application": "APP-SYN",
    "agreement#CreditAgreement": "LN-SYN",
    "agreement#Account": "ACC-SYN",
    "core#Product": "PRD-SYN",
    "core#Asset": "AST-SYN",
    "core#Event": "EVT-SYN",
}

# Generic targets for object properties without a modelled range.
FALLBACK_OBJECT: dict[str, str] = {
    "hasParty": "party#Individual",
    "partyOf": "party#Individual",
    "ofParty": "party#Individual",
    "hasProduct": "core#Product",
    "productOf": "core#Product",
    "hasAgreement": "agreement#Policy",
    "agreementOf": "agreement#Policy",
    "ofAgreement": "agreement#Policy",
    "hasAsset": "core#Asset",
    "assetOf": "core#Asset",
    "hasEvent": "core#Event",
    "eventOf": "core#Event",
    "ofEvent": "core#Event",
    "hasChannel": "core#Channel",
    "channelOf": "core#Channel",
    "hasCampaign": "core#Campaign",
    "campaignOf": "core#Campaign",
    "hasFeature": "core#Feature",
    "featureOf": "core#Feature",
    "hasMetric": "core#Metric",
    "metricOf": "core#Metric",
    "hasLocator": "core#Locator",
    "locatorOf": "core#Locator",
    "hasStatus": "core#StatusAssignment",
    "ofSubject": "party#Individual",
    "ofObject": "core#Asset",
    "classifies": "party#Individual",
}

# Domainless object properties get one link from every BusinessEntity instance.
CONCEPT_PROPS = {
    "hasRole", "hasCurrency", "hasClassValue", "inScheme", "unitOfMeasure",
    "identificationType", "metricType", "eventType", "eventSubtype",
    "locatorUsage", "eligibilityCondition", "deviceStatus", "hasCode",
}


def _err(code: str, detail: str, **details: Any) -> PortError:
    return PortError(
        code="InvalidArgument",
        message=detail,
        provider="platform",
        provider_code=code,
        details=details,
        retryable=False,
    )


def _local(iri: str) -> str:
    text = str(iri)
    for sep in ("#", "/"):
        if sep in text:
            return text.rsplit(sep, 1)[-1]
    return text


def _ns_key(iri: str) -> str:
    text = str(iri)
    if "#" in text:
        head, local = text.rsplit("#", 1)
        ns = head.rstrip("/").rsplit("/", 1)[-1]
        return f"{ns}#{local}"
    return text.rsplit("/", 1)[-1]


def _safe_token(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", text)


def _hash_int(*parts: Any) -> int:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def _iri(value: str) -> str:
    return f"<{value}>"


def _lit(value: Any) -> str:
    if isinstance(value, bool):
        return '"%s"^^<%s>' % ("true" if value else "false", XSD.boolean)
    if isinstance(value, int):
        return '"%d"^^<%s>' % (value, XSD.integer)
    if isinstance(value, (Decimal, float)):
        return '"%s"^^<%s>' % (Decimal(str(value)).quantize(Decimal("0.0001")), XSD.decimal)
    if isinstance(value, datetime):
        return '"%s"^^<%s>' % (value.isoformat(), XSD.dateTime)
    if isinstance(value, date):
        return '"%s"^^<%s>' % (value.isoformat(), XSD.date)
    return '"%s"@zh' % str(value).replace('"', '\\"')


@dataclass
class PropertyInfo:
    iri: str
    local: str
    kind: str  # object | datatype
    domains: list[str] = field(default_factory=list)
    ranges: list[str] = field(default_factory=list)


@dataclass
class OntologyModel:
    classes: dict[str, str]  # iri -> label
    parents: dict[str, list[str]]
    properties: dict[str, PropertyInfo]
    required: dict[str, list[tuple[str, str | None]]] = field(default_factory=dict)

    def descendants(self, cls: str) -> set[str]:
        out = {cls}
        changed = True
        while changed:
            changed = False
            for child, parents in self.parents.items():
                if child not in out and any(p in out for p in parents):
                    out.add(child)
                    changed = True
        return out

    def applicable(self, prop: PropertyInfo) -> list[str]:
        if not prop.domains:
            return []
        out: set[str] = set()
        for domain in prop.domains:
            if domain in self.classes:
                out |= self.descendants(domain)
        return sorted(out)


def parse_model(ttl: str) -> OntologyModel:
    graph = Graph()
    graph.parse(data=ttl, format="turtle")
    classes = {
        str(c) for c in graph.subjects(RDF.type, OWL.Class)
    }
    labels = {
        str(c): str(graph.value(c, RDFS.label) or _local(str(c))) for c in classes
    }
    parents: dict[str, list[str]] = {}
    for cls in classes:
        parents[cls] = sorted(str(p) for p in graph.objects(URIRef(cls), RDFS.subClassOf) if str(p) in classes)
    properties: dict[str, PropertyInfo] = {}
    prop_types = (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty)
    prop_iris: set[str] = set()
    for ptype in prop_types:
        prop_iris |= {str(p) for p in graph.subjects(RDF.type, ptype)}
    for iri in sorted(prop_iris):
        node = URIRef(iri)
        kind = "object" if (node, RDF.type, OWL.ObjectProperty) in graph else "datatype"
        domains = sorted({str(d) for d in graph.objects(node, RDFS.domain)})
        ranges = sorted({str(r) for r in graph.objects(node, RDFS.range)})
        properties[iri] = PropertyInfo(
            iri=iri,
            local=_local(iri),
            kind=kind,
            domains=domains,
            ranges=ranges,
        )
    required: dict[str, list[tuple[str, str | None]]] = {}
    for node in graph.subjects(RDF.type, OWL.Restriction):
        card = graph.value(node, OWL.qualifiedCardinality) or graph.value(node, OWL.minCardinality)
        if card is None or int(card) < 1:
            continue
        prop = graph.value(node, OWL.onProperty)
        on_class = graph.value(node, OWL.onClass)
        if prop is None:
            continue
        owners = [str(s) for s in graph.subjects(RDFS.subClassOf, node) if str(s) in classes]
        for owner in owners:
            required.setdefault(str(prop), []).append(
                (owner, str(on_class) if on_class is not None else None)
            )
    return OntologyModel(
        classes=labels, parents=parents, properties=properties, required=required
    )


class AboxFactory:
    """Pure, deterministic builder; ``run_abox`` performs the graph writes."""

    def __init__(self, model: OntologyModel, *, seed: int = 42, per_class: int = PER_CLASS) -> None:
        self.model = model
        self.seed = int(seed)
        self.per_class = max(200, int(per_class))
        self.classes = sorted(model.classes)
        self.counts = {c: ANCHORS.get(_ns_key(c), self.per_class) for c in self.classes}
        self.instance_ids: dict[str, list[str]] = {}
        self.instances: dict[str, str] = {}  # instance iri -> class iri
        self.concept_ids: dict[str, list[str]] = {}
        self.triples: set[str] = set()
        self.used_properties: set[str] = set()
        self.pairs: set[tuple[str, str]] = set()

    # -- ids ----------------------------------------------------------------
    def _instance_iri(self, cls: str, index: int) -> str:
        return f"{INSTANCE_BASE}/{_safe_token(_ns_key(cls))}-{index:05d}"

    def _entity_id(self, cls: str, index: int) -> str:
        key = _ns_key(cls)
        prefix = ANCHOR_IDS.get(key)
        if prefix:
            return f"{prefix}-{index:05d}"
        return f"{_safe_token(_local(cls)).upper()}-SYN-{index:05d}"

    def _concept(self, prop_local: str, index: int) -> str:
        bucket = self.concept_ids.setdefault(prop_local, [])
        while len(bucket) <= index:
            n = len(bucket)
            bucket.append(f"{CONCEPT_BASE}/{_safe_token(prop_local)}-{n:03d}")
        return bucket[index]

    # -- values -------------------------------------------------------------
    def _value(self, prop: PropertyInfo, cls: str, index: int) -> Any:
        h = _hash_int(self.seed, prop.local, _ns_key(cls), index)
        if prop.local in DATE_PROPS:
            return date(2023, 1, 1) + timedelta(days=h % 1100)
        if prop.local in DATETIME_PROPS:
            base = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=h % 525600)
            return base
        if prop.local in INT_PROPS:
            return 120 + h % 7200
        if prop.local in BOOL_PROPS:
            return index % 2 == 0
        if prop.local in DECIMAL_PROPS:
            return Decimal(h % 100000) / Decimal("100")
        if prop.local in ID_PROP_PREFIX:
            return self._entity_id(cls, index)
        if prop.local == "conditionExpression":
            return f"segment == '{_local(cls)}' and score >= {(index % 5) * 20}"
        if prop.local == "featureValue":
            return str(h % 1000)
        if prop.local == "hasCode":
            return f"CODE-{(h % 900) + 100}"
        if prop.local == "sourceRecordId":
            return self._entity_id(cls, index)
        if prop.local == "sourceSystem":
            return "SYNTHETIC-DATAGEN"
        if prop.local == "identificationValue":
            return self._entity_id(cls, index)
        return f"{_local(cls)}-{index:05d}"

    # -- build --------------------------------------------------------------
    def build(self) -> None:
        for cls in self.classes:
            count = self.counts[cls]
            ids = [self._instance_iri(cls, i) for i in range(count)]
            self.instance_ids[cls] = ids
            for iri in ids:
                self.instances[iri] = cls
                self._add(iri, str(RDF.type), _iri(cls))
                self._add(iri, str(RDFS.label), _lit(f"{_local(cls)}-{iri.rsplit('-', 1)[-1]}"))

        # Datatype properties: every property gets values on its domain
        # subclasses; domainless ones get a sparse BusinessEntity path.
        for prop in self.model.properties.values():
            if prop.kind != "datatype" or prop.iri in self.model.required:
                continue
            targets = self.model.applicable(prop) or [self._default_class()]
            for cls in targets:
                if cls not in self.classes:
                    continue
                ids = self.instance_ids[cls]
                step = 1 if prop.local in ID_PROP_PREFIX else 4
                for idx in range(0, len(ids), step):
                    iri = ids[idx]
                    self._add(iri, prop.iri, _lit(self._value(prop, cls, idx)))
                    self.used_properties.add(prop.iri)

        # Object properties: targets come from the range class pool, so every
        # reference resolves to a minted instance (no dangling IRI).
        for prop in self.model.properties.values():
            if prop.kind != "object" or prop.iri in self.model.required:
                continue
            targets = self.model.applicable(prop)
            if not targets:
                targets = [self._default_class()]
            range_cls = next((r for r in prop.ranges if r in self.classes), None)
            for cls in targets:
                if cls not in self.classes:
                    continue
                ids = self.instance_ids[cls]
                target_ids = self._target_ids(prop, range_cls, cls)
                if not target_ids:
                    continue
                for idx in range(0, len(ids), 4):
                    self._add(ids[idx], prop.iri, _iri(target_ids[idx % len(target_ids)]))
                    self.used_properties.add(prop.iri)

        # Cardinality-1 requirements from owl:Restriction: every instance of the
        # owner class must carry the mandated property.
        for prop_iri, pairs in self.model.required.items():
            prop = self.model.properties.get(prop_iri)
            if prop is None:
                continue
            for owner, on_class in pairs:
                for cls in sorted(self.model.descendants(owner)):
                    for idx, iri in enumerate(self.instance_ids.get(cls, [])):
                        if (iri, prop_iri) in self.pairs:
                            continue
                        if prop.kind == "object":
                            target = self._required_target(on_class, idx)
                            if target is None:
                                continue
                            self._add(iri, prop.iri, _iri(target))
                        else:
                            self._add(iri, prop.iri, _lit(self._value(prop, cls, idx)))
                        self.used_properties.add(prop.iri)

        # Connectivity: every instance without any object relation gets a
        # generic hasParty path, so no class is an isolated island.
        party_cls = next(c for c in self.classes if _ns_key(c) == "party#Individual")
        party_ids = self.instance_ids[party_cls]
        has_party = str(URIRef("https://w3id.org/fsldm/core#hasParty"))
        object_predicates = {
            p.iri for p in self.model.properties.values() if p.kind == "object"
        } | {str(SKOS.inScheme)}
        linked = {
            t[1:].split("> <", 1)[0]
            for t in self.triples
            if "> <" in t and t[1:].split("> <", 1)[1].split(">", 1)[0] in object_predicates
        }
        for iri in sorted(self.instances):
            if iri in linked:
                continue
            self._add(iri, has_party, _iri(party_ids[0]))
        self.used_properties.add(has_party)

    def _default_class(self) -> str:
        for key in ("core#Party", "party#Individual"):
            for cls in self.classes:
                if _ns_key(cls) == key:
                    return cls
        return self.classes[0]

    def _target_ids(self, prop: PropertyInfo, range_cls: str | None, cls: str) -> list[str]:
        if range_cls:
            return self.instance_ids.get(range_cls, [])
        fallback = FALLBACK_OBJECT.get(prop.local)
        if fallback:
            fallback_cls = next((c for c in self.classes if _ns_key(c) == fallback), None)
            if fallback_cls:
                return self.instance_ids.get(fallback_cls, [])
        if prop.local in CONCEPT_PROPS or any("Concept" in r for r in prop.ranges):
            return [self._concept(prop.local, i) for i in range(8)]
        if prop.ranges:
            # xsd range on an object property (e.g. deviceStatus -> Concept):
            # still mint a concept, never a dangling literal-as-node.
            return [self._concept(prop.local, i) for i in range(8)]
        return self.instance_ids.get(self._default_class(), [])

    def _required_target(self, on_class: str | None, index: int) -> str | None:
        if on_class and on_class in self.classes:
            ids = self.instance_ids.get(on_class, [])
            return ids[index % len(ids)] if ids else None
        if on_class and "ConceptScheme" in on_class:
            return CONCEPTSCHEME
        if on_class and "Concept" in on_class:
            return self._concept("required", index % 8)
        return None

    def _add(self, subject: str, predicate: str, obj: str) -> None:
        if obj.startswith("<") and obj.endswith(">") and obj[1:].startswith(INSTANCE_BASE):
            target = obj[1:-1]
            if (
                target not in self.instances
                and not target.startswith(CONCEPT_BASE)
                and target != CONCEPTSCHEME
            ):
                raise _err("E_ABOX_DANGLING", f"unknown object instance: {obj}")
        self.pairs.add((subject, predicate))
        self.triples.add(f"<{subject}> <{predicate}> {obj} .")

    # -- output -------------------------------------------------------------
    def digest(self) -> str:
        body = "\n".join(sorted(self.triples)).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def coverage(self) -> dict[str, Any]:
        counts = {c: len(self.instance_ids.get(c, [])) for c in self.classes}
        prop_counts: dict[str, int] = {}
        for t in self.triples:
            predicate = t.split("> <", 1)[1].split(">", 1)[0]
            prop_counts[predicate] = prop_counts.get(predicate, 0) + 1
        missing = sorted(p for p in self.model.properties if p not in prop_counts)
        object_predicates = {
            p.iri for p in self.model.properties.values() if p.kind == "object"
        } | {str(SKOS.inScheme)}
        linked = {
            t[1:].split("> <", 1)[0]
            for t in self.triples
            if "> <" in t and t[1:].split("> <", 1)[1].split(">", 1)[0] in object_predicates
        }
        isolated = [iri for iri in self.instances if iri not in linked]
        return {
            "classesTotal": len(self.classes),
            "classesWithInstances": sum(1 for c, n in counts.items() if n > 0),
            "instancesTotal": len(self.instances),
            "propertiesTotal": len(self.model.properties),
            "propertiesWithValues": len(self.model.properties) - len(missing),
            "propertiesWithoutValues": missing,
            "classCounts": {_ns_key(c): n for c, n in sorted(counts.items())},
            "triples": len(self.triples),
            "isolatedInstances": len(isolated),
        }


def _drop_graph(graph_store: Any) -> None:
    graph_store.update(f"DROP SILENT GRAPH <{SYNTHETIC_GRAPH}>")


def _insert_triples(graph_store: Any, triples: Iterable[str]) -> int:
    items = list(triples)
    for offset in range(0, len(items), BATCH):
        body = " ".join(items[offset : offset + BATCH])
        graph_store.update(f"INSERT DATA {{ GRAPH <{SYNTHETIC_GRAPH}> {{ {body} }} }}")
    return len(items)


def _write_concepts(model: OntologyModel, factory: AboxFactory) -> None:
    factory._add(CONCEPTSCHEME, str(RDF.type), _iri(str(SKOS.ConceptScheme)))
    factory._add(CONCEPTSCHEME, str(SKOS.prefLabel), _lit("FSLDM 合成概念体系"))
    for prop_local, ids in factory.concept_ids.items():
        for index, iri in enumerate(ids):
            factory._add(iri, str(RDF.type), _iri(str(SKOS.Concept)))
            factory._add(iri, str(SKOS.prefLabel), _lit(f"{prop_local}-{index:03d}"))
            factory._add(iri, str(SKOS.inScheme), _iri(CONCEPTSCHEME))
            factory.used_properties.add(str(SKOS.inScheme))
    factory.concept_ids  # keep deterministic order


def generate_abox(
    graph_store: Any,
    ttl: str,
    *,
    seed: int = 42,
    per_class: int = PER_CLASS,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build and write the synthetic ABox; returns coverage + digest proof."""

    model = parse_model(ttl)
    if not model.classes:
        raise _err("E_ABOX_NO_CLASSES", "the exported T-Box contains no owl:Class")

    factory = AboxFactory(model, seed=seed, per_class=per_class)
    factory.build()
    _write_concepts(model, factory)

    coverage = factory.coverage()
    # Reproducibility proof: rebuild in memory and compare the sorted digest.
    check = AboxFactory(model, seed=seed, per_class=per_class)
    check.build()
    _write_concepts(model, check)
    reproducible = factory.digest() == check.digest()

    report: dict[str, Any] = {
        "graph": SYNTHETIC_GRAPH,
        "seed": seed,
        "perClass": per_class,
        "dryRun": dry_run,
        "coverage": coverage,
        "digest": factory.digest(),
        "reproducible": reproducible,
        "checks": {
            "danglingObjects": 0,
            "isolatedInstances": coverage["isolatedInstances"],
            "missingProperties": len(coverage["propertiesWithoutValues"]),
        },
    }
    if dry_run:
        report["written"] = 0
        return report

    _drop_graph(graph_store)
    written = _insert_triples(graph_store, sorted(factory.triples))
    report["written"] = written
    rows = graph_store.query(
        f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{SYNTHETIC_GRAPH}> {{ ?s ?p ?o }} }}"
    ).get("bindings", [])
    total = 0
    if rows:
        term = (rows[0].get("values") or {}).get("n") or rows[0].get("n") or {}
        total = int(term.get("value", 0)) if isinstance(term, dict) else int(term)
    report["graphTriples"] = total
    return report
