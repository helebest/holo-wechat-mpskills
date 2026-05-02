#!/usr/bin/env python3
"""CLI for converting Markdown articles into WeChat MP-compatible HTML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def list_themes() -> int:
    themes_dir = Path(__file__).resolve().parent.parent / "assets" / "themes"
    for theme_file in sorted(themes_dir.glob("*.json")):
        try:
            data = json.loads(theme_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        name = data.get("name", theme_file.stem)
        description = data.get("description", "")
        print(f"{name}\t{description}")
    return 0


def wrap_document(content: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
</head>
<body>
{content}
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Markdown to WeChat MP-compatible inline-style HTML."
    )
    parser.add_argument("input", nargs="?", help="Input Markdown file.")
    parser.add_argument("-o", "--output", help="Output HTML path.")
    parser.add_argument("--preview", help="Optional local preview HTML path.")
    parser.add_argument("--theme", default="minimal", help="Bundled theme name.")
    parser.add_argument("--theme-file", help="Custom theme JSON path.")
    parser.add_argument("--raw", action="store_true", help="Write only the styled HTML fragment.")
    parser.add_argument("--list-themes", action="store_true", help="List bundled themes.")
    args = parser.parse_args(argv)

    if args.list_themes:
        return list_themes()

    if not args.input:
        parser.error("input Markdown file is required unless --list-themes is used")

    if __package__ in (None, ""):
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from markdown_converter import MarkdownConverter
        from preview_generator import PreviewGenerator
        from style_engine import ThemeEngine
    else:
        from .markdown_converter import MarkdownConverter
        from .preview_generator import PreviewGenerator
        from .style_engine import ThemeEngine

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    converter = MarkdownConverter()
    engine = ThemeEngine(theme_path=args.theme_file, theme_name=args.theme)
    parsed = converter.parse(str(input_path))
    styled_html = engine.apply_styles(parsed.raw_html)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_html = styled_html if args.raw else wrap_document(styled_html, parsed.meta.title)
    output_path.write_text(output_html, encoding="utf-8")
    print(f"HTML written to: {output_path.resolve()}")

    if args.preview:
        preview = PreviewGenerator(theme_path=args.theme_file, theme_name=args.theme)
        preview_path = preview.save(str(input_path), args.preview)
        print(f"Preview written to: {preview_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
