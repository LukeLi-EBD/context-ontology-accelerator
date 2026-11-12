#!/usr/bin/env python3
"""Watchdog: tracked files that exist in HEAD but are gone from disk, checked in every worktree.

Standard library only. This is the real implementation; check-missing-tracked.ps1
and check-missing-tracked.sh are thin launchers that find Python and forward argv.

Why this exists: on 2026-11-11 11:14 the main worktree lost 9 tracked files under
libs/ts-shared to an external process. There was no checkout / reset / stash / reflog
trace, the directory was left empty, and the actor could not be identified. This script
is meant to shout immediately the next time something like that happens.

Per worktree (git worktree list --porcelain):
  1. `git ls-files -d`  - tracked but missing on disk
  2. own index mtime (.git/index, or .git/worktrees/<name>/index) and whether it moved
     within the last IndexMinutes minutes (someone touched the index behind our back)
  3. current branch and HEAD
  4. in-progress merge / cherry-pick / revert / rebase / sequencer (MERGE_HEAD, ...)

Repo-wide:
  5. `git stash list` entries

Exit codes:
  0  clean - no output at all
  1  tracked files missing (CRIT)
  2  other anomaly - index touched recently, merge/rebase in progress, stash entries,
     or a listed worktree whose directory is gone
  3  usage / environment error

Options (both spellings work, so old runbook commands keep working verbatim):
  -RepoPath / --repo-path          any worktree of the repo; defaults to the parent of
                                   the directory holding this script
  -IndexMinutes / --index-minutes  freshness threshold for the per-worktree index mtime,
                                   in minutes (default 15); 0 disables the check
  -Fix / --fix                     restore missing files that are still identical to
                                   HEAD in the index, via `git checkout HEAD -- <path>`
  -WorktreePath / --worktree-path  limit the check (and -Fix) to one worktree

Examples:
  python scripts/check-missing-tracked.py
  python scripts/check-missing-tracked.py -IndexMinutes 0 -Fix
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MARKERS = (
    ('MERGE_HEAD', 'merge'),
    ('CHERRY_PICK_HEAD', 'cherry-pick'),
    ('REVERT_HEAD', 'revert'),
    ('rebase-merge', 'rebase'),
    ('rebase-apply', 'rebase'),
    ('sequencer', 'sequencer'),
)

INDEX_ENTRY_RE = re.compile(r'^(?P<mode>\d{6}) (?P<sha>[0-9a-fA-F]{40}) (?P<stage>\d)\t')


def write_err(message):
    sys.stderr.write('[COA-WATCH][ERR] %s\n' % message)


def ps_number(value):
    """Format a rounded double the way PowerShell stringifies it (3.0 -> '3')."""
    if value == int(value):
        return str(int(value))
    return repr(value)


def git(repo, *args):
    return subprocess.run(
        ['git', '-C', repo] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding='utf-8',
        errors='replace',
    )


def resolve_path(path):
    return os.path.normpath(os.path.abspath(path))


def list_worktrees(repo):
    result = git(repo, 'worktree', 'list', '--porcelain')
    if result.returncode != 0:
        return None
    worktrees = []
    current = None
    for line in result.stdout.splitlines():
        match = re.match(r'^worktree (.+)$', line)
        if match:
            if current is not None:
                worktrees.append(current)
            current = {'path': match.group(1), 'head': '', 'branch': '(detached)'}
            continue
        if current is None:
            continue
        match = re.match(r'^HEAD (.+)$', line)
        if match:
            current['head'] = match.group(1)
            continue
        match = re.match(r'^branch refs/heads/(.+)$', line)
        if match:
            current['branch'] = match.group(1)
    if current is not None:
        worktrees.append(current)
    return worktrees


def get_worktree_state(worktree):
    path = worktree['path']
    exists = os.path.exists(path)
    missing = []
    ops = []
    ls_failed = False
    index_age = None
    index_path = ''

    if exists:
        result = git(path, 'ls-files', '-d')
        if result.returncode != 0:
            ls_failed = True
        else:
            missing = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # "gitdir" is not part of the porcelain output, so ask git directly. This is
    # .git for the main worktree and .git/worktrees/<name> for linked ones.
    git_dir = ''
    if exists:
        result = git(path, 'rev-parse', '--absolute-git-dir')
        if result.returncode == 0 and result.stdout.strip():
            git_dir = result.stdout.strip()

    if git_dir:
        for marker, op in MARKERS:
            if os.path.exists(os.path.join(git_dir, marker)):
                ops.append(op)
        # normpath because PowerShell's Join-Path flattens '/' to '\' in the output
        index_path = os.path.normpath(os.path.join(git_dir, 'index'))
        if os.path.exists(index_path):
            age_minutes = (time.time() - os.stat(index_path).st_mtime) / 60.0
            index_age = round(age_minutes, 1)

    return {
        'path': path,
        'branch': worktree['branch'],
        'head': worktree['head'][:8],
        'exists': exists,
        'ls_failed': ls_failed,
        'missing': missing,
        'ops': ops,
        'index_age': index_age,
        'index_path': index_path,
    }


def repairable(worktree_path, relative_path):
    """Return 'ok' when the file can be restored from HEAD without touching anyone's work."""
    if os.path.exists(os.path.join(worktree_path, relative_path)):
        return 'present-on-disk'

    head_sha = git(worktree_path, 'rev-parse', '--verify', '--quiet', 'HEAD:' + relative_path)
    if head_sha.returncode != 0 or not head_sha.stdout.strip():
        return 'head-blob-missing'

    entry = git(worktree_path, 'ls-files', '-s', '--', relative_path)
    if entry.returncode != 0 or not entry.stdout.strip():
        return 'not-in-index'
    line = entry.stdout.splitlines()[0]
    match = INDEX_ENTRY_RE.match(line)
    if not match:
        return 'index-entry-unparsed'
    if match.group('stage') != '0':
        return 'index-stage-' + match.group('stage')
    if match.group('sha').lower() != head_sha.stdout.strip().lower():
        return 'index-differs-from-head'

    return 'ok'


def collect_stash(repo):
    result = git(repo, 'stash', 'list')
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]


def build_parser():
    parser = argparse.ArgumentParser(
        prog='check-missing-tracked',
        description='Watchdog for tracked files that disappeared from disk in any worktree.',
    )
    parser.add_argument('-RepoPath', '--repo-path', dest='repo_path', default='')
    parser.add_argument('-IndexMinutes', '--index-minutes', dest='index_minutes', type=int, default=15)
    parser.add_argument('-Fix', '--fix', dest='fix', action='store_true')
    parser.add_argument('-WorktreePath', '--worktree-path', dest='worktree_path', default='')
    return parser


def main(argv):
    options = build_parser().parse_args(argv)

    repo_path = options.repo_path or os.path.join(SCRIPT_DIR, '..')
    if not os.path.exists(repo_path):
        write_err('repo path not found: %s' % repo_path)
        return 3
    repo_path = resolve_path(repo_path)

    try:
        check = git(repo_path, 'rev-parse', '--git-dir')
    except FileNotFoundError:
        write_err('git not found on PATH')
        return 3
    if check.returncode != 0:
        write_err('not a git repository: %s' % repo_path)
        return 3

    worktrees = list_worktrees(repo_path)
    if not worktrees:
        write_err('git worktree list returned nothing for %s' % repo_path)
        return 3

    if options.worktree_path:
        if not os.path.exists(options.worktree_path):
            write_err('worktree path not found: %s' % options.worktree_path)
            return 3
        want = resolve_path(options.worktree_path).replace('\\', '/').rstrip('/').lower()
        matched = [
            worktree for worktree in worktrees
            if worktree['path'].replace('\\', '/').rstrip('/').lower() == want
        ]
        if not matched:
            write_err('%s is not in git worktree list' % options.worktree_path)
            return 3
        worktrees = matched

    states = [get_worktree_state(worktree) for worktree in worktrees]

    stash = collect_stash(repo_path)
    if stash is None:
        write_err('git stash list failed')
        return 3

    # --- optional repair ---------------------------------------------------
    fix_lines = []
    fix_applied = False
    if options.fix:
        for state in states:
            if not state['missing']:
                continue
            if not state['exists']:
                fix_lines.append('skip  %s (worktree dir missing)' % state['path'])
                continue
            if state['ops']:
                fix_lines.append('skip  %s (%s in progress)' % (state['path'], ','.join(state['ops'])))
                continue
            for path in state['missing']:
                verdict = repairable(state['path'], path)
                if verdict != 'ok':
                    fix_lines.append('skip  %s/%s (%s)' % (state['path'], path, verdict))
                    continue
                checkout = git(state['path'], 'checkout', 'HEAD', '--', path)
                if checkout.stdout:
                    sys.stdout.write(checkout.stdout)
                if checkout.returncode != 0:
                    fix_lines.append('fail  %s/%s (git checkout exit %s)' % (state['path'], path, checkout.returncode))
                else:
                    fix_lines.append('fixed %s/%s' % (state['path'], path))
                    fix_applied = True

        # Re-scan after the repair so the report is about the current truth.
        states = [get_worktree_state(worktree) for worktree in worktrees]
        stash = collect_stash(repo_path)
        if stash is None:
            write_err('git stash list failed')
            return 3

    # --- evaluate ----------------------------------------------------------
    missing_total = 0
    missing_files = []
    real_warnings = []
    index_warnings = []
    detail_lines = []

    for state in states:
        flags = []
        if not state['exists']:
            flags.append('worktree-dir-missing')
            real_warnings.append('%s: worktree dir missing' % state['path'])
        if state['ls_failed']:
            flags.append('ls-files-failed')
            real_warnings.append('%s: git ls-files -d failed' % state['path'])
        if state['ops']:
            flags.append('op:' + ','.join(state['ops']))
            real_warnings.append('%s: %s in progress' % (state['path'], ','.join(state['ops'])))
        if (
            options.index_minutes > 0
            and state['index_age'] is not None
            and state['index_age'] <= options.index_minutes
        ):
            age = ps_number(state['index_age'])
            flags.append('index-touched-%sm' % age)
            index_warnings.append(
                '%s: index touched %sm ago (%s)' % (state['path'], age, state['index_path'])
            )
        if state['missing']:
            missing_total += len(state['missing'])
            for path in state['missing']:
                missing_files.append(os.path.join(state['path'], path).replace('\\', '/'))
            flags.append('missing=%s' % len(state['missing']))

        if flags:
            age_text = 'n/a' if state['index_age'] is None else '%sm' % ps_number(state['index_age'])
            detail_lines.append(
                'wt=%s branch=%s head=%s index_age=%s [%s]'
                % (state['path'], state['branch'], state['head'], age_text, ' '.join(flags))
            )
            for path in state['missing']:
                detail_lines.append('  missing: %s' % path)

    for line in stash:
        real_warnings.append('stash: %s' % line)

    warning_total = len(real_warnings) + len(index_warnings)
    if missing_total == 0 and warning_total == 0 and not fix_lines:
        return 0

    # --- report ------------------------------------------------------------
    if fix_lines:
        print('[COA-WATCH] fix pass (%s decision(s))' % len(fix_lines))
        for line in fix_lines:
            print('  %s' % line)

    if missing_total > 0 or warning_total > 0:
        for line in detail_lines:
            print(line)
        for line in real_warnings:
            print('WARN %s' % line)
        for line in index_warnings:
            print('WARN %s' % line)

        stamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        repo_display = repo_path.replace('\\', '/')
        if missing_total > 0:
            shown = ';'.join(missing_files[:5])
            more = ' +%s more' % (len(missing_files) - 5) if len(missing_files) > 5 else ''
            summary = (
                '[COA-WATCH][CRIT] %s repo=%s worktrees=%s missing=%s warn=%s stash=%s files=%s%s'
                % (stamp, repo_display, len(states), missing_total, warning_total, len(stash), shown, more)
            )
        else:
            summary = (
                '[COA-WATCH][WARN] %s repo=%s worktrees=%s missing=0 warn=%s stash=%s'
                % (stamp, repo_display, len(states), warning_total, len(stash))
            )
        print(summary)

    # --- exit code ---------------------------------------------------------
    if missing_total > 0:
        return 1
    if real_warnings:
        return 2
    if index_warnings:
        # A fresh index that this very -Fix run caused is not an alarm; anything else is.
        if fix_applied:
            print('[COA-WATCH] note: the index freshness above was caused by this -Fix run; pass -IndexMinutes 0 to silence it')
            return 0
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
