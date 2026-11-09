"""Acceptance runner: full unittest discovery with a discovered/executed self-check.

Why this exists
---------------
`python -m unittest discover` alone cannot prove that everything it found was
actually run: a `-k` filter, an import error or a silently skipped case can all
leave a green "OK" behind. This runner loads the whole test tree, counts the
discovered cases, removes only explicitly named files, runs the rest, and
reports discovered / excluded / executed / passed / failed / skipped as one
machine-readable line for the PowerShell acceptance scripts.

Exit codes
------------
0  executed == discovered (after exclusions), no failures, no errors, no skips
1  at least one failure / error / skip
2  discovery or execution mismatch (some discovered case never ran), or the
   runner itself crashed
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
import unittest


class RecordingResult(unittest.TextTestResult):
    """TextTestResult that also records executed ids and skip reasons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executed_ids: list[str] = []
        self.skip_details: list[dict[str, str]] = []

    def startTest(self, test):
        super().startTest(test)
        self.executed_ids.append(test.id())

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.skip_details.append({"test": test.id(), "reason": str(reason)})


def _iter_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_cases(item)
        else:
            yield item


def _module_name(case) -> str:
    """File stem that defines `case`; import failures carry the module as name."""
    if isinstance(case, unittest.loader._FailedTest):
        return case._testMethodName
    return case.__class__.__module__.rsplit(".", 1)[-1]


def _failed_test_reason(case) -> str:
    detail = getattr(case, "_exception", None)
    return f"{type(detail).__name__}: {detail}" if detail else "import failed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-dir", default="/hosttests")
    parser.add_argument("--top-level", default="/hosttests")
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument(
        "--exclude",
        default="",
        help="comma-separated module stems (e.g. test_bundle,test_sqlsplit)",
    )
    args = parser.parse_args()

    excludes = [x.strip() for x in args.exclude.split(",") if x.strip()]
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=args.start_dir, pattern=args.pattern, top_level_dir=args.top_level
    )
    cases = list(_iter_cases(suite))
    discovered_total = len(cases)

    excluded_by_file: dict[str, int] = {}
    kept = []
    for case in cases:
        module = _module_name(case)
        if module in excludes:
            excluded_by_file[module] = excluded_by_file.get(module, 0) + 1
        else:
            kept.append(case)

    unknown_excludes = sorted(set(excludes) - set(excluded_by_file))
    import_failures = [
        {"test": _module_name(c), "reason": _failed_test_reason(c)}
        for c in kept
        if isinstance(c, unittest.loader._FailedTest)
    ]

    run_suite = unittest.TestSuite(kept)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=RecordingResult)
    result = runner.run(run_suite)

    executed = result.testsRun
    discovered = len(kept)
    not_executed = sorted(set(c.id() for c in kept if not isinstance(c, unittest.loader._FailedTest)) - set(result.executed_ids))
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = executed - failures - errors - skipped

    summary = {
        "discovered_total": discovered_total,
        "excluded": excluded_by_file,
        "unknown_excludes": unknown_excludes,
        "discovered": discovered,
        "executed": executed,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "import_failures": import_failures,
        "not_executed": not_executed,
        "skip_details": result.skip_details,
    }
    print("ACCEPTANCE_RESULT " + json.dumps(summary, ensure_ascii=False))

    for test, tb in result.failures:
        print(f"ACCEPTANCE_FAILURE {test.id()} :: {tb.strip().splitlines()[-1]}")
    for test, tb in result.errors:
        print(f"ACCEPTANCE_ERROR {test.id()} :: {tb.strip().splitlines()[-1]}")
    for item in result.skip_details:
        print(f"ACCEPTANCE_SKIP {item['test']} :: {item['reason']}")
    for item in import_failures:
        print(f"ACCEPTANCE_IMPORT_FAIL {item['test']} :: {item['reason']}")
    for test_id in not_executed:
        print(f"ACCEPTANCE_NOT_EXECUTED {test_id}")

    if discovered != executed:
        print(
            f"ACCEPTANCE_MISMATCH discovered={discovered} executed={executed} "
            f"missing={len(not_executed)}"
        )
    if unknown_excludes:
        print(f"ACCEPTANCE_UNKNOWN_EXCLUDE {','.join(unknown_excludes)}")

    if discovered != executed or unknown_excludes:
        return 2
    if failures or errors or skipped or import_failures:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a crash must be a non-zero runner result
        traceback.print_exc()
        raise SystemExit(2)
