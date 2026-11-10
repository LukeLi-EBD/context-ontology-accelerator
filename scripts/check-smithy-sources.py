#!/usr/bin/env python3
"""Fail when the Smithy sources carry uncommitted changes after a build.

``gradlew build`` depends on the ``:smithyFormat`` task, which rewrites
``models/src/main/smithy/*.smithy`` in place.  If that rewrite is not committed
before generation, the committed contract and the generated artifacts describe
different sources: git says one thing, the generator read another.

Run this after the Gradle build and before copying artifacts.  A formatting-only
diff (the ``smithyFormat`` output) is safe to commit as-is; a semantic diff means
the contract changed and needs the full Gradle + regeneration path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = ("models/src",)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def main() -> int:
    try:
        changed = git("status", "--porcelain", "--", *PATHS)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"✗ could not read git status: {exc}", file=sys.stderr)
        return 1

    if not changed.strip():
        print("✓ models/src is clean")
        return 0

    stat = git("diff", "--stat", "--", *PATHS).rstrip()
    print("✗ models/src has uncommitted changes after the build.", file=sys.stderr)
    print("  gradlew build runs :smithyFormat and rewrites sources in place,", file=sys.stderr)
    print("  so generation would emit artifacts for a contract that is not in git.", file=sys.stderr)
    print("  Inspect `git diff -- models/src` before deciding:", file=sys.stderr)
    print(
        "    formatting only -> commit the result (semantics unchanged; artifacts stay identical)",
        file=sys.stderr,
    )
    print(
        "    semantic change -> rerun the Gradle path and regenerate artifacts",
        file=sys.stderr,
    )
    print("  changed paths:", file=sys.stderr)
    print(changed.rstrip(), file=sys.stderr)
    print("  git diff --stat -- models/src:", file=sys.stderr)
    print(stat or "  (untracked files only)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
