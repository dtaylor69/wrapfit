"""Command-line entry point for wrapfit."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional, Tuple

from .core import Report, check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wrapfit",
        description="Check whether text can be wrapped to a given width without breaking a word.",
    )
    parser.add_argument("file", nargs="?", help="text file or directory to check (default: stdin)")
    parser.add_argument("-w", "--width", type=int, default=72, help="target column width (default: 72)")
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="allow long words to be broken instead of failing; report the resulting line count",
    )
    parser.add_argument(
        "--tabsize",
        type=int,
        default=8,
        help="columns per tab stop, for lines indented with tabs (default: 8)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the result as a single JSON object instead of text, for scripting",
    )
    return parser


def read_input(path: Optional[str]) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def iter_files(root: str) -> List[str]:
    """All regular files under root, in a stable, walkable order."""
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            paths.append(os.path.join(dirpath, name))
    return paths


def check_directory(root: str, width: int, *, lenient: bool, tabsize: int) -> List[Tuple[str, Report]]:
    results = []
    for path in iter_files(root):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            # Not readable as text (permissions, or a binary file) — nothing to check.
            continue
        results.append((path, check(text, width, lenient=lenient, tabsize=tabsize)))
    return results


def run_directory(args: argparse.Namespace) -> int:
    results = check_directory(args.file, args.width, lenient=args.lenient, tabsize=args.tabsize)
    ok = all(report.ok for _, report in results)

    if args.json:
        print(json.dumps([{"path": path, **report.to_dict()} for path, report in results]))
        return 0 if ok else 1

    files_with_violations = 0
    for path, report in results:
        if not report.violations:
            continue
        files_with_violations += 1
        label = "would be broken" if args.lenient else "too long"
        for v in report.violations:
            print(
                f"{path}:{v.line}, paragraph {v.paragraph}: {label} — "
                f"'{v.word}' is {v.length} columns, {v.excess} over width"
            )
        if report.lenient and report.wrapped_line_count is not None:
            print(f"{path}: lenient wrap would produce {report.wrapped_line_count} line(s)")

    if files_with_violations == 0:
        print(f"fits: every word in {len(results)} file(s) fits within {args.width} columns")
    elif not args.lenient:
        total = sum(len(report.violations) for _, report in results)
        print(
            f"\n{total} word(s) exceed {args.width} columns across {files_with_violations} file(s). "
            "Widen the column, shorten the word, or pass --lenient to allow breaking it.",
            file=sys.stderr,
        )

    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file is not None and args.file != "-" and os.path.isdir(args.file):
        try:
            return run_directory(args)
        except ValueError as exc:
            print(f"wrapfit: {exc}", file=sys.stderr)
            return 2

    try:
        text = read_input(args.file)
    except OSError as exc:
        print(f"wrapfit: {exc}", file=sys.stderr)
        return 2

    try:
        report = check(text, args.width, lenient=args.lenient, tabsize=args.tabsize)
    except ValueError as exc:
        print(f"wrapfit: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict()))
        return 0 if report.ok else 1

    if not report.violations:
        print(f"fits: every word fits within {args.width} columns")
    else:
        label = "would be broken" if args.lenient else "too long"
        for v in report.violations:
            print(
                f"line {v.line}, paragraph {v.paragraph}: {label} — "
                f"'{v.word}' is {v.length} columns, {v.excess} over width"
            )
        if not args.lenient:
            print(
                f"\n{len(report.violations)} word(s) exceed {args.width} columns. "
                "Widen the column, shorten the word, or pass --lenient to allow breaking it.",
                file=sys.stderr,
            )

    if report.lenient and report.wrapped_line_count is not None:
        print(f"lenient wrap would produce {report.wrapped_line_count} line(s)")

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
