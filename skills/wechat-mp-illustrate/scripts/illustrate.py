#!/usr/bin/env python3
"""CLI for generating and inserting illustrations into a Markdown article."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate illustrations for a Markdown article using OpenRouter."
    )
    parser.add_argument("markdown", help="Input Markdown article.")
    parser.add_argument("--output", default="output", help="Output directory.")
    parser.add_argument("--style", default="", help="Custom illustration style or requirements.")
    args = parser.parse_args(argv)

    if not Path(args.markdown).exists():
        print(f"Input file not found: {args.markdown}", file=sys.stderr)
        return 1

    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from illustrator import ArticleIllustrator
    else:
        from .illustrator import ArticleIllustrator

    async def run() -> int:
        result = await ArticleIllustrator().run(args.markdown, args.output, args.style)
        print(result.output_path)
        return 0

    try:
        return asyncio.run(run())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
