"""G-03 shapes registry: versioned deployment + startup directory registration.

The registry is the single source of truth for SHACL. `/ontology/import` asks
this table (not the filesystem) which shapes apply to a namespace, so the answer
"which shape set, which version" is always queryable. `data/shapes/` is still
loaded, but only by registering the directory content here.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from rdflib import Graph

from .errors import PortError
from .validation import namespace_segment

TABLE = "platform.shapes_registry"


class ShapesRegistry:
    port = "ShapesRegistry"

    def __init__(self, meta: Any) -> None:
        self._meta = meta

    # ---- deploy ----------------------------------------------------------

    def deploy(
        self,
        namespace: str,
        content: bytes,
        rdf_format: str = "turtle",
        shapes_id: str | None = None,
        version: str | None = None,
        source: str = "api",
        actor: str = "operator",
    ) -> dict[str, Any]:
        if not namespace or not namespace.strip():
            raise PortError(
                code="InvalidArgument",
                message="namespace is required to deploy shapes",
                provider="platform",
                provider_code="E_SHAPES_NAMESPACE",
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PortError(
                code="InvalidArgument",
                message=f"shapes body is not UTF-8: {exc}",
                provider="rdflib",
                provider_code="E_SHAPES_PARSE",
            ) from exc
        graph = Graph()
        try:
            graph.parse(data=text, format=rdf_format)
        except Exception as exc:
            raise PortError(
                code="InvalidArgument",
                message=f"shapes parse failed ({rdf_format}): {exc}",
                provider="rdflib",
                provider_code="E_SHAPES_PARSE",
                details={"format": rdf_format},
            ) from exc
        if len(graph) == 0:
            raise PortError(
                code="InvalidArgument",
                message="shapes graph is empty",
                provider="platform",
                provider_code="E_SHAPES_EMPTY",
            )

        digest = hashlib.sha256(content).hexdigest()
        shapes_id = shapes_id or f"shapes-{namespace_segment(namespace)}"
        resolved_version = version or f"sv-{digest[:12]}"
        existing = self._meta.query(
            f"SELECT created_at, triple_count FROM {TABLE} "
            "WHERE shapes_id = %s AND version = %s",
            (shapes_id, resolved_version),
        )
        if existing:
            created = existing[0]["created_at"]
            return {
                "shapesId": shapes_id,
                "namespace": namespace,
                "version": resolved_version,
                "triples": int(existing[0]["triple_count"]),
                "contentHash": digest,
                "created": False,
                "deployedAt": created.isoformat() if hasattr(created, "isoformat") else created,
            }

        with self._meta.tx() as tx:
            rows = tx.execute_returning(
                f"""
                INSERT INTO {TABLE}
                  (shapes_id, namespace, version, content_hash, triple_count,
                   content, content_format, source, actor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING created_at
                """,
                (
                    shapes_id, namespace, resolved_version, digest, len(graph),
                    text, rdf_format, source, actor,
                ),
            )
        created = rows[0]["created_at"]
        return {
            "shapesId": shapes_id,
            "namespace": namespace,
            "version": resolved_version,
            "triples": len(graph),
            "contentHash": digest,
            "created": True,
            "deployedAt": created.isoformat() if hasattr(created, "isoformat") else created,
        }

    # ---- read ------------------------------------------------------------

    def load_deployed(self, namespace: str) -> dict[str, Any] | None:
        """Latest registered shapes for one namespace (None = nothing deployed)."""
        rows = self._meta.query(
            f"""
            SELECT shapes_id, namespace, version, content_hash, triple_count, content,
                   content_format, created_at
              FROM {TABLE}
             WHERE namespace = %s
             ORDER BY created_at DESC, version DESC
             LIMIT 1
            """,
            (namespace,),
        )
        if not rows:
            return None
        row = rows[0]
        graph = Graph()
        try:
            graph.parse(data=row["content"], format=row["content_format"])
        except Exception as exc:
            raise PortError(
                code="Unavailable",
                message=f"registered shapes {row['shapes_id']} {row['version']} cannot be parsed: {exc}",
                provider="rdflib",
                provider_code="E_SHAPES_REGISTRY_CORRUPT",
                details={"shapesId": row["shapes_id"], "version": row["version"]},
            ) from exc
        return {
            "graph": graph,
            "shapesId": row["shapes_id"],
            "shapesVersion": row["version"],
            "namespace": row["namespace"],
            "digest": row["content_hash"],
            "files": [],
        }

    def list(self) -> dict[str, Any]:
        rows = self._meta.query(
            f"""
            SELECT shapes_id, namespace, version, content_hash, triple_count, source,
                   actor, created_at
              FROM {TABLE}
             ORDER BY namespace, shapes_id, created_at
            """
        )
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            created = row["created_at"]
            created = created.isoformat() if hasattr(created, "isoformat") else created
            item = grouped.setdefault(
                row["shapes_id"],
                {
                    "shapesId": row["shapes_id"],
                    "namespace": row["namespace"],
                    "versions": [],
                },
            )
            item["versions"].append(
                {
                    "version": row["version"],
                    "triples": int(row["triple_count"]),
                    "contentHash": row["content_hash"],
                    "source": row["source"],
                    "actor": row["actor"],
                    "deployedAt": created,
                }
            )
        items = []
        for item in grouped.values():
            current = item["versions"][-1]
            items.append(
                {
                    "shapesId": item["shapesId"],
                    "namespace": item["namespace"],
                    "version": current["version"],
                    "triples": current["triples"],
                    "deployedAt": current["deployedAt"],
                    "versions": item["versions"],
                }
            )
        return {"items": items, "count": len(items)}

    # ---- startup directory registration ----------------------------------

    def load_directory(self, shapes_dir: str | None) -> list[dict[str, Any]]:
        """Register `shapes_dir` content: legacy root set + per-namespace dirs."""
        if not shapes_dir:
            return []
        root = Path(shapes_dir)
        if not root.is_dir():
            return []
        registered: list[dict[str, Any]] = []
        legacy = sorted(root.glob("*.ttl"))
        if legacy:
            content = b"\n".join(path.read_bytes() for path in legacy)
            registered.append(
                self.deploy(
                    "urn:platform:default:",
                    content,
                    shapes_id="shapes-core",
                    source="directory",
                    actor="startup",
                )
            )
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            files = sorted(directory.glob("*.ttl"))
            if not files:
                continue
            manifest: dict[str, Any] = {}
            for name in ("manifest.json", "shapes.json"):
                candidate = directory / name
                if candidate.is_file():
                    try:
                        manifest = json.loads(candidate.read_text(encoding="utf-8"))
                    except ValueError:
                        manifest = {}
                    break
            namespace = manifest.get("namespace") or f"urn:{directory.name}:"
            content = b"\n".join(path.read_bytes() for path in files)
            registered.append(
                self.deploy(
                    str(namespace),
                    content,
                    shapes_id=str(manifest.get("id") or f"shapes-{directory.name}"),
                    version=str(manifest["version"]) if manifest.get("version") else None,
                    source="directory",
                    actor="startup",
                )
            )
        return registered
