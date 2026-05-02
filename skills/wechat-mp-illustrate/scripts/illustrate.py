#!/usr/bin/env python3
"""CLI for generating one image from a prompt with OpenRouter."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _load_client_class():
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from api import OpenRouterImageClient
    else:
        from .api import OpenRouterImageClient

    return OpenRouterImageClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a text-to-image or image-to-image asset with OpenRouter. "
            "The script reads OPENROUTER_API_KEY and OPENROUTER_IMAGE_MODEL from the "
            "process environment unless explicit arguments are provided."
        )
    )
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Image prompt text.")
    prompt_group.add_argument("--prompt-file", help="UTF-8 file containing the image prompt.")
    parser.add_argument("--output", required=True, help="Output image path, for example cover.png.")
    parser.add_argument(
        "--model",
        help="OpenRouter image model. Overrides OPENROUTER_IMAGE_MODEL.",
    )
    parser.add_argument(
        "--openrouter-api-key",
        help="OpenRouter API key. Overrides OPENROUTER_API_KEY.",
    )
    parser.add_argument(
        "--reference-image",
        action="append",
        default=[],
        help="Local image path or remote URL for image-to-image. Can be repeated.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio, for example 1:1, 16:9, or 4:3.",
    )
    return parser


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        return args.prompt
    return Path(args.prompt_file).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        prompt = _read_prompt(args)
        client_class = _load_client_class()
        client = client_class(api_key=args.openrouter_api_key, model=args.model)

        async def run() -> Path:
            return await client.generate_image_file(
                prompt,
                Path(args.output),
                aspect_ratio=args.aspect_ratio,
                reference_images=args.reference_image,
            )

        output_path = asyncio.run(run())
        print(output_path)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
