#!/usr/bin/env python3
"""CLI for submitting a prepared HTML article to WeChat MP drafts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Submit a WeChat MP-compatible HTML article to the draft box."
    )
    parser.add_argument("html", help="HTML file to submit.")
    parser.add_argument("--cover", required=True, help="Cover image path.")
    parser.add_argument("--title", help="Article title. Defaults to <title>.")
    parser.add_argument("--author", help="Author name.")
    parser.add_argument("--digest", help="Article digest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local files and article fields without calling WeChat APIs.",
    )
    args = parser.parse_args(argv)

    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from html_submitter import inspect_html_draft, submit_html_draft
    else:
        from .html_submitter import inspect_html_draft, submit_html_draft

    try:
        if args.dry_run:
            info = inspect_html_draft(
                args.html,
                args.cover,
                title=args.title,
                author=args.author,
                digest=args.digest,
            )
            print(json.dumps(info, ensure_ascii=False, indent=2))
            return 0

        media_id = submit_html_draft(
            args.html,
            args.cover,
            title=args.title,
            author=args.author,
            digest=args.digest,
        )
        print(media_id)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
