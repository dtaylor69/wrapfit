"""Command-line entry point for wrapfit."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .core import check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wrapfit",
        description="Check whether text can be wrapped to a given width without breaking a word.",
    )
    parser.add_argument("file", nargs="?", help="text file to check (default: stdin)")
    parser.add_argument("-w", "--width", type=int, default=72, help="target column width (default: 72)")
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="allow long words to be broken instead of failing; report the resulting line count",
    )
    return parser


def read_input(path: Optional[str]) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = read_input(args.file)
    except OSError as exc:
        print(f"wrapfit: {exc}", file=sys.stderr)
        return 2

    try:
        report = check(text, args.width, lenient=args.lenient)
    except ValueError as exc:
        print(f"wrapfit: {exc}", file=sys.stderr)
        return 2

    if not report.violations:
        print(f"fits: every word fits within {args.width} columns")
    else:
        label = "would be broken" if args.lenient else "too long"
        for v in report.violations:
            print(f"line {v.line}: {label} — '{v.word}' is {v.length} columns, {v.excess} over width")
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
