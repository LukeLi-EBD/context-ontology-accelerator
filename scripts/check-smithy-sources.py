#!/usr/bin/env python3
"""Fail when the Smithy sources carry uncommitted changes after a build.

``gradlew build`` depends on the ``:smithyFormat`` task, which rewrites
``models/src/main/smithy/*.smithy`` in place.  If that rewrite is not committed
before generation, the committed contract and the generated artifacts describe
different sources: git says one thing, the generator read another.

A non-git checkout is skipped explicitly: this check is about drift between the
working tree and the committed contract, which only exists in a git checkout.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = ("models/src",)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main() -> int:
    try:
        probe = git("rev-parse", "--is-inside-work-tree")
    except OSError as exc:
        print(f"✗ 无法执行 git（本检查需要 git）：{exc}", file=sys.stderr)
        return 1
    if probe.returncode != 0:
        print("✓ 非 git checkout，跳过源码清洁检查")
        return 0

    status = git("status", "--porcelain", "--", *PATHS)
    if status.returncode != 0:
        print(f"✗ 无法读取 git status：{status.stderr.strip()}", file=sys.stderr)
        return 1

    changed = status.stdout
    if not changed.strip():
        print("✓ models/src 干净")
        return 0

    stat = git("diff", "--stat", "--", *PATHS).stdout.strip()
    print("✗ models/src 有未提交改动（构建后）。", file=sys.stderr)
    print("  gradlew build 的 :smithyFormat 会就地改写源码，", file=sys.stderr)
    print("  此时生成产物对应的契约不在 git 里。", file=sys.stderr)
    print("  出路（三选一）：", file=sys.stderr)
    print("    1) 提交：确认是契约变更后 git add / commit，再重跑生成；", file=sys.stderr)
    print("    2) 暂存：只是临时 WIP 时 git stash，起栈或生成完再恢复；", file=sys.stderr)
    print("    3) 先跑生成再看产物：执行生成并对比 smithy-generated 的 diff，再决定。", file=sys.stderr)
    print("  先看 git diff -- models/src 区分两类差异：", file=sys.stderr)
    print("    格式化差异 -> 直接提交，产物应逐字节一致；", file=sys.stderr)
    print("    语义差异   -> 重跑 Gradle 路径并重生成产物。", file=sys.stderr)
    print("  变更路径：", file=sys.stderr)
    print(changed.rstrip(), file=sys.stderr)
    print("  git diff --stat -- models/src：", file=sys.stderr)
    print(stat or "  （仅未跟踪文件）", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
