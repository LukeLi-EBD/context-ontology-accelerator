"""CLI: serve | check-config | probe | smoke | smoke-s1..s11 | ontology | facts-export | facts-verify | facts-replay."""

from __future__ import annotations

import argparse
import json
import sys
import traceback

from . import __version__
from .assembly import assemble
from .bootstrap import run_self_check
from .config import load_config
from .errors import EXIT_INTERNAL, EXIT_OK, EXIT_USAGE, PlatformError, PortError, port_error_exit_code
from .logging_setup import configure_logging


def _report_error(exc: Exception) -> int:
    if isinstance(exc, PlatformError):
        print(exc.render(), file=sys.stderr)
        return exc.exit_code
    if isinstance(exc, PortError):
        code = exc.provider_code or exc.code
        print(f"{code} provider={exc.provider} detail: {exc.message}", file=sys.stderr)
        return port_error_exit_code(exc)
    print(f"E_INTERNAL detail: {exc}", file=sys.stderr)
    traceback.print_exc()
    return EXIT_INTERNAL


def _run_ontology(runtime, args) -> int:
    action = args.action
    if action == "import":
        if not args.file:
            print("E_USAGE ontology import requires --file", file=sys.stderr)
            return EXIT_USAGE
        import_format = args.format if args.format in ("turtle", "trig") else None
        result = runtime.ontology.import_source(
            args.file, args.semver, args.label, import_format,
            on_conflict=args.on_conflict, graph_iri=args.graph_iri,
        )
    elif action == "propose":
        if not args.version:
            print("E_USAGE ontology propose requires --version", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.propose(
            args.version, args.summary or "", actor=args.actor,
            against_version=args.against,
        )
    elif action == "approve":
        if not args.proposal:
            print("E_USAGE ontology approve requires --proposal", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.approve(
            args.proposal, actor=args.actor, reason=args.reason
        )
    elif action == "publish":
        if not args.version:
            print("E_USAGE ontology publish requires --version", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.publish(
            args.version, proposal_id=args.proposal,
            acknowledge_breaking=args.acknowledge_breaking,
            actor=args.actor, reason=args.reason,
            activate_existing=bool(args.publish_existing),
        )
    elif action == "diff":
        if not args.version:
            print("E_USAGE ontology diff requires --version (to)", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.diff(args.against, args.version)
    elif action == "rollback":
        if not args.to:
            print("E_USAGE ontology rollback requires --to", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.rollback(args.to)
    elif action == "rollback-to":
        if not args.to:
            print("E_USAGE ontology rollback-to requires --to", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.rollback_to(
            args.to, actor=args.actor, reason=args.reason
        )
    elif action == "export":
        if not args.version:
            print("E_USAGE ontology export requires --version", file=sys.stderr)
            return EXIT_USAGE
        export_format = args.format if args.format in ("turtle", "nquads") else "turtle"
        result = runtime.ontology.export_version(args.version, export_format)
        if args.out:
            from pathlib import Path

            Path(args.out).write_text(result["content"], encoding="utf-8")
            result = {key: result[key] for key in ("versionId", "format", "graph", "triples")}
            result["out"] = args.out
        else:
            sys.stdout.write(result["content"])
            return EXIT_OK
    elif action == "events":
        result = runtime.ontology.events(args.version)
    elif action == "verify":
        result = runtime.ontology.verify_events()
    elif action == "proposals":
        result = runtime.ontology.list_proposals(args.version)
    elif action == "show":
        if not args.version:
            print("E_USAGE ontology show requires --version", file=sys.stderr)
            return EXIT_USAGE
        result = runtime.ontology.get(args.version)
        result["graphTripleCount"] = runtime.ontology.graph_count(args.version)
    else:
        result = runtime.ontology.status()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platform", description="Platform kernel (S0 skeleton)")
    parser.add_argument("--version", action="version", version=f"platform {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run self-check then the HTTP server")
    serve.add_argument("--config", default="/data/platform.yaml")
    serve.add_argument("--retry-seconds", type=float, default=60.0)

    check = sub.add_parser("check-config", help="validate configuration only (no dependencies)")
    check.add_argument("--config", default="/data/platform.yaml")

    probe = sub.add_parser("probe", help="run the startup self-check and exit")
    probe.add_argument("--config", default="/data/platform.yaml")
    probe.add_argument("--retry-seconds", type=float, default=60.0)

    caps = sub.add_parser("graph-capabilities", help="measure GSP/SPARQL capabilities (S1, read-only-ish)")
    caps.add_argument("--config", default="/data/platform.yaml")
    caps.add_argument("--endpoint", default=None)
    caps.add_argument("--json", action="store_true")
    caps.add_argument(
        "--allow-destructive",
        action="store_true",
        help="allow GSP writes/deletes on the default graph even when it is not empty",
    )

    count = sub.add_parser(
        "graph-count",
        help="run a SPARQL COUNT query and print the numeric binding (read-only)",
    )
    count.add_argument("--config", default="/data/platform.yaml")
    count.add_argument("--query", required=True)
    count.add_argument("--var", default="n", help="result variable holding the count")

    ontology = sub.add_parser("ontology", help="ontology versions, proposals, publish, rollback")
    ontology.add_argument(
        "action",
        choices=[
            "import", "propose", "approve", "publish", "diff", "rollback",
            "rollback-to", "export", "events", "verify", "proposals", "status", "show",
        ],
    )
    ontology.add_argument("--config", default="/data/platform.yaml")
    ontology.add_argument("--file", default=None)
    ontology.add_argument("--semver", default="0.0.0")
    ontology.add_argument("--label", default=None)
    ontology.add_argument(
        "--format", choices=["turtle", "trig", "nquads"], default=None,
        help="import: turtle/trig; export: turtle/nquads",
    )
    ontology.add_argument("--version", default=None, help="target version id")
    ontology.add_argument("--to", default=None, help="rollback target version id")
    ontology.add_argument("--from", dest="against", default=None, help="diff base version id")
    ontology.add_argument("--against", dest="against", default=None, help="diff base version id")
    ontology.add_argument("--proposal", default=None, help="proposal id")
    ontology.add_argument("--summary", default=None, help="change summary for propose")
    ontology.add_argument("--actor", default="operator")
    ontology.add_argument("--reason", default=None)
    ontology.add_argument(
        "--acknowledge-breaking", dest="acknowledge_breaking", action="store_true"
    )
    ontology.add_argument(
        "--existing",
        dest="publish_existing",
        action="store_true",
        help=(
            "publish: forward-publish the existing version with the same canonical "
            "hash (OQ-65); full gates still run"
        ),
    )
    ontology.add_argument(
        "--on-conflict", dest="on_conflict", choices=["reject", "new_version"], default="reject"
    )
    ontology.add_argument("--graph-iri", dest="graph_iri", default=None)
    ontology.add_argument("--out", default=None, help="export output path")

    smoke_s1 = sub.add_parser("smoke-s1", help="run the S1 acceptance suite")
    smoke_s1.add_argument("--config", default="/data/platform.yaml")

    smoke_s2 = sub.add_parser("smoke-s2", help="run the S2 document-ingest acceptance suite")
    smoke_s2.add_argument("--config", default="/data/platform.yaml")
    smoke_s2.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke_s2.add_argument(
        "--bad-config", default="/app/tests/bad_config_documents.yaml"
    )

    smoke_s3 = sub.add_parser("smoke-s3", help="run the S3 retrieval acceptance suite")
    smoke_s3.add_argument("--config", default="/data/platform.yaml")
    smoke_s3.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke_s3.add_argument(
        "--bad-config", default="/app/tests/bad_config_search.yaml"
    )

    smoke_s4 = sub.add_parser("smoke-s4", help="run the S4 extraction acceptance suite")
    smoke_s4.add_argument("--config", default="/data/platform.yaml")
    smoke_s4.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke_s4.add_argument(
        "--bad-config", default="/app/tests/bad_config_extraction.yaml"
    )

    smoke_s5 = sub.add_parser("smoke-s5", help="run the S5 reasoning/SHACL acceptance suite")
    smoke_s5.add_argument("--config", default="/data/platform.yaml")
    smoke_s5.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke_s5.add_argument(
        "--bad-config", default="/app/tests/bad_config_reasoning.yaml"
    )

    smoke_s6 = sub.add_parser("smoke-s6", help="run the S6 context assembly acceptance suite")
    smoke_s6.add_argument("--config", default="/data/platform.yaml")
    smoke_s6.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke_s6.add_argument(
        "--bad-config", default="/app/tests/bad_config_context.yaml"
    )

    smoke_s7 = sub.add_parser("smoke-s7", help="run the S7 Web UI acceptance suite")
    smoke_s7.add_argument("--config", default="/data/platform.yaml")
    smoke_s7.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s8 = sub.add_parser("smoke-s8", help="run the S8 fact-governance acceptance suite")
    smoke_s8.add_argument("--config", default="/data/platform.yaml")
    smoke_s8.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s9 = sub.add_parser("smoke-s9", help="run the S9 adjudication/export acceptance suite")
    smoke_s9.add_argument("--config", default="/data/platform.yaml")
    smoke_s9.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s10 = sub.add_parser("smoke-s10", help="run the S10 reversible-adjudication/replay suite")
    smoke_s10.add_argument("--config", default="/data/platform.yaml")
    smoke_s10.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s11 = sub.add_parser("smoke-s11", help="run the S11 T-Box governance acceptance suite")
    smoke_s11.add_argument("--config", default="/data/platform.yaml")
    smoke_s11.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s12 = sub.add_parser("smoke-s12", help="run the S12 integrity acceptance suite")
    smoke_s12.add_argument("--config", default="/data/platform.yaml")
    smoke_s12.add_argument("--base-url", default="http://127.0.0.1:8080")

    smoke_s13 = sub.add_parser("smoke-s13", help="run the S13 bulk-import acceptance suite")
    smoke_s13.add_argument("--config", default="/data/platform.yaml")
    smoke_s13.add_argument("--base-url", default="http://127.0.0.1:8080")

    imp = sub.add_parser("import", help="bulk import a directory tree (resumable)")
    imp.add_argument("directory")
    imp.add_argument("--config", default="/data/platform.yaml")
    imp.add_argument("--dry-run", dest="dry_run", action="store_true")
    imp.add_argument("--retry-failed", dest="retry_failed", action="store_true")
    imp.add_argument("--parse-concurrency", type=int, default=2)
    imp.add_argument("--embed-concurrency", type=int, default=1)
    imp.add_argument(
        "--progress-seconds", type=float, default=30.0,
        help="progress cadence in seconds (0 disables)",
    )
    imp.add_argument(
        "--batch-size", dest="batch_size", type=int, default=30,
        help="max files per invocation; the next run resumes (0 = unlimited)",
    )
    imp.add_argument(
        "--max-seconds", dest="max_seconds", type=float, default=180.0,
        help="wall-clock budget per invocation; stops submitting new files "
             "after this many seconds (0 = unlimited)",
    )

    imports = sub.add_parser("imports", help="list import batches / item states")
    imports.add_argument("--config", default="/data/platform.yaml")
    imports.add_argument("--batch", default=None, help="batch id (items only)")
    imports.add_argument(
        "--status", default=None,
        choices=["pending", "parsing", "chunked", "indexed", "failed"],
    )
    imports.add_argument("--limit", type=int, default=20)

    reindex = sub.add_parser(
        "reindex", help="rebuild one embedding partition, then switch the pointer"
    )
    reindex.add_argument("--config", default="/data/platform.yaml")
    reindex.add_argument(
        "--provider", required=True, choices=["local-bge", "ark", "fake"],
        help="target partition provider (local-bge = default 1024d, ark = 2048d)",
    )
    reindex.add_argument(
        "--batch-size", dest="batch_size", type=int, default=32,
        help="chunks per segment; rerun resumes the rest",
    )
    reindex.add_argument(
        "--max-seconds", dest="max_seconds", type=float, default=180.0,
        help="wall-clock budget per invocation (0 = unlimited)",
    )
    reindex.add_argument(
        "--activate-only", dest="activate_only", action="store_true",
        help="only switch embedding.active_model to the existing partition",
    )

    smoke_embed = sub.add_parser(
        "smoke-embed", help="run the embedding-partition contract suite"
    )
    smoke_embed.add_argument("--config", default="/data/platform.yaml")

    bench_embed = sub.add_parser(
        "bench-embed", help="measure embedding throughput split by chunk tier"
    )
    bench_embed.add_argument("--config", default="/data/platform.yaml")
    bench_embed.add_argument("--short", type=int, default=20)
    bench_embed.add_argument("--long", type=int, default=10)

    export = sub.add_parser("facts-export", help="export the fact audit chain (NDJSON + Markdown)")
    export.add_argument("--config", default="/data/platform.yaml")
    export.add_argument("--out", required=True)
    export.add_argument("--from", dest="start", default=None)
    export.add_argument("--to", dest="end", default=None)
    export.add_argument("--source-document", dest="source_document", default=None)

    verify = sub.add_parser("facts-verify", help="verify an exported NDJSON audit chain offline")
    verify.add_argument("--config", default="/data/platform.yaml")
    verify.add_argument("--file", required=True)

    replay = sub.add_parser(
        "facts-replay",
        help="replay an exported NDJSON chain into a throw-away empty database",
    )
    replay.add_argument("--config", default="/data/platform.yaml")
    replay.add_argument("--file", required=True)
    replay.add_argument("--snapshot", default=None)
    replay.add_argument("--dry-run", dest="dry_run", action="store_true")
    replay.add_argument("--keep-db", dest="keep_db", action="store_true")

    bundle_export = sub.add_parser(
        "export-bundle",
        help="export a migration-friendly bundle to _freeze/<tag> (read-only)",
    )
    bundle_export.add_argument("--config", default="/data/platform.yaml")
    bundle_export.add_argument("--out", required=True, help="bundle root, e.g. /freeze")
    bundle_export.add_argument("--tag", required=True, help="bundle tag, e.g. v1-20261105")
    bundle_export.add_argument(
        "--include-blobs", dest="include_blobs", action="store_true",
        help="copy referenced CAS blobs into bundle/blobs (default: metadata only)",
    )

    bundle_import = sub.add_parser(
        "import-bundle",
        help="restore a bundle into a throw-away test database",
    )
    bundle_import.add_argument("--config", default="/data/platform.yaml")
    bundle_import.add_argument("--bundle", required=True)
    bundle_import.add_argument("--database", default="platform_restore_test")
    bundle_import.add_argument("--replace", action="store_true")
    bundle_import.add_argument(
        "--keep-db-on-failure", dest="keep_db_on_failure", action="store_true"
    )

    smoke = sub.add_parser("smoke", help="run the S0 acceptance smoke suite")
    smoke.add_argument("--config", default="/data/platform.yaml")
    smoke.add_argument("--base-url", default="http://127.0.0.1:8080")
    smoke.add_argument(
        "--bad-config",
        action="append",
        default=None,
        help="config expected to fail-fast with exit 78 (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        bundle = load_config(args.config)
    except PlatformError as exc:
        print(exc.render(), file=sys.stderr)
        return exc.exit_code

    if args.command == "graph-capabilities":
        from .capabilities import run_probe

        endpoint = args.endpoint or bundle.config.graph.endpoint
        report = run_probe(endpoint, allow_destructive=args.allow_destructive)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            for group in ("gsp", "sparql"):
                print(f"[{group}] support={report[group].get('support', 'measured')}")
                for item in report[group]["checks"]:
                    flag = "SKIP" if item["skipped"] else ("PASS" if item["passed"] else "FAIL")
                    print(f"  [{flag}] {item['id']}: {item['detail']}")
        return EXIT_OK

    if args.command == "check-config":
        print(
            f"OK config_version={bundle.config.config_version} mode={bundle.config.mode} "
            f"runtime_mode={bundle.config.runtime.mode} file={bundle.path}"
        )
        for warning in bundle.warnings:
            print(f"WARN {warning}")
        return EXIT_OK

    configure_logging(bundle.config.log.level, bundle.config.log.format)

    if args.command == "facts-replay":
        from .replay import replay_file

        result = replay_file(
            args.file,
            snapshot_path=args.snapshot,
            dry_run=args.dry_run,
            database_url=bundle.config.database.url,
            keep_db=args.keep_db,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return EXIT_OK if result.get("ok") else 1

    if args.command == "export-bundle":
        from .bundle import export_bundle

        runtime = assemble(bundle)
        try:
            # Read-only: no migrate(), no advisory DDL on the production DB.
            runtime.metadata.open(retry_seconds=10.0)
            result = export_bundle(runtime, args.out, args.tag, args.include_blobs)
        except (PortError, PlatformError) as exc:
            return _report_error(exc)
        finally:
            runtime.close()
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return EXIT_OK

    if args.command == "import-bundle":
        from .bundle import import_bundle

        result = import_bundle(
            bundle,
            args.bundle,
            database=args.database,
            replace=args.replace,
            keep_db_on_failure=args.keep_db_on_failure,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return EXIT_OK if result.get("ok") else 1

    # Ontology/verification commands only need PG + graph + CAS; skip the 11MB
    # storage probe that `serve` performs.
    if args.command in (
        "ontology",
        "smoke-s1",
        "smoke-s2",
        "smoke-s3",
        "smoke-s4",
        "smoke-s5",
        "smoke-s6",
        "smoke-s7",
        "smoke-s8",
        "smoke-s9",
        "smoke-s10",
        "smoke-s11",
        "smoke-s12",
        "smoke-s13",
        "facts-export",
        "facts-verify",
        "import",
        "imports",
        "reindex",
        "smoke-embed",
        "bench-embed",
        "graph-count",
    ):
        runtime = assemble(bundle)
        try:
            runtime.metadata.open(retry_seconds=10.0)
            runtime.metadata.migrate()
            if args.command == "graph-count":
                result = runtime.graph.query(args.query)
                bindings = result.get("bindings", [])
                value = (
                    bindings[0].get("values", {}).get(args.var, {}).get("value")
                    if bindings
                    else "0"
                )
                print(json.dumps({"count": int(value or 0)}, ensure_ascii=False))
                return EXIT_OK
            if args.command == "smoke-s1":
                from .smoke_s1 import run_smoke_s1

                return run_smoke_s1(runtime)
            if args.command == "smoke-s2":
                from .smoke_s2 import run_smoke_s2

                return run_smoke_s2(runtime, args.base_url, args.bad_config)
            if args.command == "smoke-s3":
                from .smoke_s3 import run_smoke_s3

                return run_smoke_s3(runtime, args.base_url, args.bad_config)
            if args.command == "smoke-s4":
                from .smoke_s4 import run_smoke_s4

                return run_smoke_s4(runtime, args.base_url, args.bad_config)
            if args.command == "smoke-s5":
                from .smoke_s5 import run_smoke_s5

                return run_smoke_s5(runtime, args.base_url, args.bad_config)
            if args.command == "smoke-s6":
                from .smoke_s6 import run_smoke_s6

                return run_smoke_s6(runtime, args.base_url, args.bad_config)
            if args.command == "smoke-s7":
                from .smoke_s7 import run_smoke_s7

                return run_smoke_s7(runtime, args.base_url)
            if args.command == "smoke-s8":
                from .smoke_s8 import run_smoke_s8

                return run_smoke_s8(runtime, args.base_url)
            if args.command == "smoke-s9":
                from .smoke_s9 import run_smoke_s9

                return run_smoke_s9(runtime, args.base_url)
            if args.command == "smoke-s10":
                from .smoke_s10 import run_smoke_s10

                return run_smoke_s10(runtime, args.base_url)
            if args.command == "smoke-s11":
                from .smoke_s11 import run_smoke_s11

                return run_smoke_s11(runtime, args.base_url)
            if args.command == "smoke-s12":
                from .smoke_s12 import run_smoke_s12

                return run_smoke_s12(runtime, args.base_url)
            if args.command == "smoke-s13":
                from .smoke_s13 import run_smoke_s13

                return run_smoke_s13(runtime, args.base_url)
            if args.command == "import":
                from .importer import Importer, dry_run

                if args.dry_run:
                    print(json.dumps(dry_run(runtime, args.directory),
                                     ensure_ascii=False, indent=2))
                    return EXIT_OK
                result = Importer(
                    runtime,
                    parse_concurrency=args.parse_concurrency,
                    embed_concurrency=args.embed_concurrency,
                    progress_seconds=args.progress_seconds,
                    max_files=args.batch_size,
                    max_seconds=args.max_seconds,
                ).run(args.directory, retry_failed=args.retry_failed)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return int(result.get("exitCode") or EXIT_OK)
            if args.command == "imports":
                from .importer import batches_overview, list_items

                if args.batch:
                    print(json.dumps(
                        list_items(runtime, args.batch, args.status, args.limit),
                        ensure_ascii=False, indent=2,
                    ))
                else:
                    overview = batches_overview(runtime, args.limit)
                    if args.status:
                        overview["items"] = list_items(
                            runtime, None, args.status, args.limit
                        )
                    print(json.dumps(overview, ensure_ascii=False, indent=2))
                return EXIT_OK
            if args.command == "reindex":
                from .reindex import ReindexService

                service = ReindexService(
                    runtime.metadata, runtime.embedding, runtime.vectors
                )
                print(json.dumps(
                    service.run(
                        args.provider,
                        batch_size=args.batch_size,
                        max_seconds=args.max_seconds,
                        activate_only=args.activate_only,
                    ),
                    ensure_ascii=False,
                    indent=2,
                ))
                return EXIT_OK
            if args.command == "smoke-embed":
                from .smoke_embed import run_smoke_embed

                return run_smoke_embed(runtime)
            if args.command == "bench-embed":
                from .bench_embed import run_bench_embed

                return run_bench_embed(runtime, args.short, args.long)
            if args.command == "facts-export":
                from .fact_export import export_meta, write_export

                exported = runtime.facts.export_events(
                    args.start, args.end, args.source_document
                )
                conflicts = runtime.facts.conflicts(include_accepted=True)
                # Views (summary + assertions) use the window only; the NDJSON is
                # always the complete prefix chain so it stays verifiable.
                fact_ids = [
                    item["factId"]
                    for item in exported["windowItems"]
                    if item.get("factId")
                ]
                snapshot = runtime.facts.snapshot(fact_ids=fact_ids)
                meta = export_meta(
                    exported, snapshot, runtime.facts.assertion_count(),
                    {
                        "from": args.start,
                        "to": args.end,
                        "sourceDocumentId": args.source_document,
                    },
                )
                written = write_export(
                    exported["items"], args.out, conflicts, snapshot=snapshot,
                    meta=meta,
                )
                written["chain"] = exported["chain"]
                print(json.dumps(written, ensure_ascii=False, indent=2))
                return EXIT_OK if exported["chain"].get("ok") else 1
            if args.command == "facts-verify":
                from .fact_export import verify_file

                result = verify_file(args.file)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return EXIT_OK if result.get("ok") else 1
            return _run_ontology(runtime, args)
        except Exception as exc:  # noqa: BLE001 - normalized below
            return _report_error(exc)
        finally:
            runtime.close()

    runtime = assemble(bundle)

    try:
        checks = run_self_check(
            runtime, retry_seconds=getattr(args, "retry_seconds", 30.0)
        )
    except PlatformError as exc:
        runtime.close()
        print(exc.render(), file=sys.stderr)
        return exc.exit_code

    if args.command == "probe":
        for item in checks:
            print(f"[OK] {item.stage}: {item.detail}")
        for item in runtime.degraded:
            print(f"[DEGRADED] {item}")
        runtime.close()
        return EXIT_OK

    if args.command == "smoke":
        from .smoke import run_smoke

        bad = args.bad_config or [
            "/app/tests/bad_config.yaml",
            "/app/tests/bad_config_unsupported_provider.yaml",
        ]
        try:
            return run_smoke(bundle, args.base_url, bad)
        finally:
            runtime.close()

    if args.command == "serve":
        import uvicorn

        from .api import create_app
        from .ontology_init import start as start_ontology, stop as stop_ontology

        start_ontology(runtime)
        app = create_app(runtime, checks)
        try:
            uvicorn.run(
                app,
                host=bundle.config.http.bind,
                port=bundle.config.http.port,
                log_config=None,
                access_log=False,
            )
        except Exception as exc:  # bind errors, unexpected crashes
            print(f"E_SERVER_START stage=http detail: {exc}", file=sys.stderr)
            return EXIT_INTERNAL
        finally:
            stop_ontology()
            runtime.close()
        return EXIT_OK

    return EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
