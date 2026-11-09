"""SHACL gate (S5). pySHACL does all validation; this module only loads shapes,
extracts a compact report and maps failures. Boundary: D18 (no home-grown checks).

G-03 adds per-namespace shape sets: shapes may live in subdirectories named after
the namespace segment (`shapes/fsldm/*.ttl` for `https://w3id.org/fsldm/`), with
an optional `manifest.json` carrying `namespace` and `version`. The legacy
root-level set (`shapes/*.ttl`) is kept for A-Box validation with no namespace.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import rdflib
from pyshacl import validate as shacl_validate

from .config import ReasoningConfig
from .errors import PortError

log = logging.getLogger(__name__)

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")


def namespace_segment(namespace: str) -> str:
    """Map a namespace IRI to its shapes subdirectory name.

    `https://w3id.org/fsldm/` -> `fsldm`, `urn:fsldm:` -> `fsldm`.
    """
    text = namespace.strip().rstrip("/#>")
    tail = text.replace("urn:", "").split(":")[-1]
    tail = tail.rsplit("/", 1)[-1]
    return tail or "default"


class ShaclValidator:
    port = "ValidationService"

    def __init__(self, config: ReasoningConfig) -> None:
        self._config = config

    # ---- shape discovery -------------------------------------------------

    def _root(self) -> Path:
        return Path(self._config.shapes_dir)

    def shapes(self, namespace: str | None = None) -> list[Path]:
        root = self._root()
        if not root.is_dir():
            return []
        if namespace:
            return sorted((root / namespace_segment(namespace)).glob("*.ttl"))
        return sorted(root.glob("*.ttl"))

    def registries(self) -> list[dict[str, Any]]:
        """Describe every deployed shape set (namespace / files / version).

        Root-level shapes stay visible as the legacy set with no namespace.
        Subdirectories without a manifest are still listed with an inferred
        namespace (`urn:<dir>:`) so a deployment is never silently invisible.
        """
        root = self._root()
        items: list[dict[str, Any]] = []
        if not root.is_dir():
            return items
        root_files = sorted(root.glob("*.ttl"))
        if root_files:
            items.append(
                {
                    "namespace": None,
                    "dir": ".",
                    "files": [p.name for p in root_files],
                    "version": self._digest(root_files),
                    "manifest": False,
                }
            )
        for sub in sorted(p for p in root.iterdir() if p.is_dir()):
            files = sorted(sub.glob("*.ttl"))
            if not files:
                continue
            manifest: dict[str, Any] = {}
            for name in ("manifest.json", "shapes.json"):
                candidate = sub / name
                if candidate.is_file():
                    try:
                        manifest = json.loads(candidate.read_text("utf-8"))
                    except (OSError, ValueError):
                        manifest = {}
                    break
            namespace = manifest.get("namespace") or f"urn:{sub.name}:"
            items.append(
                {
                    "namespace": namespace,
                    "dir": sub.name,
                    "files": [p.name for p in files],
                    "version": manifest.get("version") or self._digest(files),
                    "manifest": bool(manifest),
                    "source": manifest.get("source"),
                    "deployedAt": manifest.get("deployedAt"),
                }
            )
        return items

    def namespaces(self) -> list[str]:
        return [item["namespace"] for item in self.registries() if item["namespace"]]

    def shapes_version(self, namespace: str | None = None) -> str:
        return self._digest(self.shapes(namespace))

    @staticmethod
    def _digest(paths: list[Path]) -> str:
        digest = hashlib.sha256()
        for path in paths:
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def load_shapes(self, namespace: str | None = None) -> tuple[rdflib.Graph, list[str]]:
        paths = self.shapes(namespace)
        if not paths:
            where = f"namespace {namespace}" if namespace else self._config.shapes_dir
            raise PortError(
                code="Unsupported",
                message=f"no SHACL shapes found for {where}",
                provider="pyshacl",
                provider_code="E_SHACL_SHAPES_MISSING",
                details={"shapesDir": self._config.shapes_dir, "namespace": namespace},
            )
        graph = rdflib.Graph()
        for path in paths:
            try:
                graph.parse(path.as_posix(), format="turtle")
            except Exception as exc:
                raise PortError(
                    code="DataLoss",
                    message=f"cannot parse SHACL shapes {path.name}: {exc}",
                    provider="pyshacl",
                    provider_code="E_SHACL_BAD_SHAPES",
                    details={"file": path.name},
                ) from exc
        return graph, [p.name for p in paths]

    # ---- validation ------------------------------------------------------

    def validate(
        self, data_nt: bytes, graph_iri: str, namespace: str | None = None
    ) -> dict[str, Any]:
        if not data_nt.strip():
            raise PortError(
                code="InvalidArgument",
                message=f"graph {graph_iri} is empty: nothing to validate",
                provider="pyshacl",
                provider_code="E_VALIDATE_EMPTY_GRAPH",
                details={"graph": graph_iri},
            )
        shapes_graph, shape_files = self.load_shapes(namespace)
        data_graph = rdflib.Graph()
        try:
            data_graph.parse(data=data_nt.decode("utf-8"), format="nt")
        except Exception as exc:
            raise PortError(
                code="DataLoss",
                message=f"cannot parse data graph {graph_iri}: {exc}",
                provider="pyshacl",
                provider_code="E_VALIDATE_BAD_DATA",
                details={"graph": graph_iri},
            ) from exc

        conforms, report_graph, report_text = shacl_validate(
            data_graph,
            shacl_graph=shapes_graph,
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
        )
        violations = self._extract(report_graph)
        log.info(
            "shacl validated",
            extra={
                "event": {
                    "event": "shacl.validate",
                    "graph": graph_iri,
                    "namespace": namespace,
                    "conforms": bool(conforms),
                    "violations": len(violations),
                }
            },
        )
        return {
            "conforms": bool(conforms),
            "graph": graph_iri,
            "namespace": namespace,
            "violations": violations[: self._config.max_violations],
            "violationCount": len(violations),
            "truncated": len(violations) > self._config.max_violations,
            "shapes": shape_files,
            "shapesVersion": self.shapes_version(namespace),
            "report": report_text[:20000],
        }

    def _extract(self, report_graph: rdflib.Graph) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for result in report_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
            items.append(
                {
                    "focusNode": self._term(report_graph, result, SH.focusNode),
                    "path": self._term(report_graph, result, SH.resultPath),
                    "severity": self._term(report_graph, result, SH.resultSeverity),
                    "message": self._term(report_graph, result, SH.resultMessage),
                    "sourceShape": self._term(report_graph, result, SH.sourceShape),
                }
            )
        return items

    @staticmethod
    def _term(
        graph: rdflib.Graph, subject: rdflib.term.Node, predicate: rdflib.term.Node
    ) -> str | None:
        value = graph.value(subject, predicate)
        if value is None:
            return None
        text = str(value)
        if isinstance(value, rdflib.Literal) and value.language:
            return f"{text}@{value.language}"
        return text
