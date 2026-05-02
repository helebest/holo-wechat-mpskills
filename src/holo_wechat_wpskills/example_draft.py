"""Prepare an example article and optionally create a real WeChat draft."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .validate import ROOT

DEFAULT_SLUG = "wechat-draft-workflow"
DEFAULT_THEME = "pier"
DEFAULT_WORK_DIR = ROOT / ".tmp" / "examples"


class ExampleDraftError(Exception):
    """Raised when local example draft validation cannot continue."""


@dataclass(frozen=True)
class PreparedExample:
    slug: str
    theme: str
    article_dir: Path
    markdown_path: Path
    html_path: Path
    preview_path: Path
    cover_path: Path
    title: str
    author: str | None
    digest: str | None


def _add_script_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _load_typeset_modules() -> tuple[Any, Any, Any, Any]:
    _add_script_path(ROOT / "skills" / "wechat-mp-typeset" / "scripts")
    from markdown_converter import MarkdownConverter
    from preview_generator import PreviewGenerator
    from style_engine import ThemeEngine
    from typeset import wrap_document

    return MarkdownConverter, PreviewGenerator, ThemeEngine, wrap_document


def _load_manage_modules() -> tuple[Any, Any, Any]:
    _add_script_path(ROOT / "skills" / "wechat-mp-manage" / "scripts")
    from html_submitter import inspect_html_draft, submit_html_draft
    from wechat_client import WeChatAPIError, WeChatClient

    return inspect_html_draft, submit_html_draft, (WeChatAPIError, WeChatClient)


def prepare_example(slug: str, theme: str, work_dir: Path = DEFAULT_WORK_DIR) -> PreparedExample:
    """Copy an example article into a generated work directory and create HTML outputs."""
    source_dir = ROOT / "examples" / "articles" / slug
    if not source_dir.exists():
        raise ExampleDraftError(f"example not found: {slug}")

    article_dir = work_dir / slug
    if article_dir.exists():
        shutil.rmtree(article_dir)
    article_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, article_dir)

    markdown_path = article_dir / "article.md"
    html_path = article_dir / "article.html"
    preview_path = article_dir / "article.preview.html"

    MarkdownConverter, PreviewGenerator, ThemeEngine, wrap_document = _load_typeset_modules()
    converter = MarkdownConverter()
    parsed = converter.parse(str(markdown_path))

    if not parsed.meta.cover:
        raise ExampleDraftError(f"{markdown_path} is missing front matter cover")

    engine = ThemeEngine(theme_name=theme)
    html_path.write_text(
        wrap_document(engine.apply_styles(parsed.raw_html), parsed.meta.title),
        encoding="utf-8",
    )
    PreviewGenerator(theme_name=theme).save(str(markdown_path), str(preview_path))

    return PreparedExample(
        slug=slug,
        theme=theme,
        article_dir=article_dir,
        markdown_path=markdown_path,
        html_path=html_path,
        preview_path=preview_path,
        cover_path=Path(parsed.meta.cover),
        title=parsed.meta.title,
        author=parsed.meta.author,
        digest=parsed.meta.summary,
    )


def inspect_prepared_example(prepared: PreparedExample) -> dict[str, Any]:
    """Run the same local validation used by submit_html_draft --dry-run."""
    inspect_html_draft, _, _ = _load_manage_modules()
    info = inspect_html_draft(
        str(prepared.html_path),
        str(prepared.cover_path),
        title=prepared.title,
        author=prepared.author,
        digest=prepared.digest,
    )
    info.update(
        {
            "mode": "dry-run",
            "slug": prepared.slug,
            "theme": prepared.theme,
            "article_dir": str(prepared.article_dir.resolve()),
            "preview_path": str(prepared.preview_path.resolve()),
        }
    )
    return info


def ensure_ignored_env(env_file: Path) -> Path:
    """Require a local repository .env file that Git explicitly ignores."""
    env_path = env_file.resolve()
    root = ROOT.resolve()

    if not env_path.exists():
        raise ExampleDraftError(
            f"missing credential file: {env_path}\n"
            r'copy it locally with: Copy-Item -LiteralPath "C:\Users\HE LE\Project\holotalks\.env" -Destination .env -Force'
        )
    if not env_path.is_relative_to(root):
        raise ExampleDraftError(f"credential file must live inside this repository: {env_path}")

    relative_env = env_path.relative_to(root)
    result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "--quiet", "--", str(relative_env)],
        check=False,
    )
    if result.returncode == 1:
        raise ExampleDraftError(f"credential file is not ignored by git: {relative_env}")
    if result.returncode != 0:
        raise ExampleDraftError(f"unable to verify git ignore status for: {relative_env}")

    return env_path


def create_real_draft(prepared: PreparedExample, env_file: Path) -> str:
    """Create a real WeChat draft after local validation and ignored .env checks."""
    env_path = ensure_ignored_env(env_file)
    load_dotenv(env_path, override=True)

    _, submit_html_draft, client_modules = _load_manage_modules()
    _, WeChatClient = client_modules
    client = WeChatClient(env_file=str(env_path), token_cache_dir=str(ROOT))

    return submit_html_draft(
        str(prepared.html_path),
        str(prepared.cover_path),
        title=prepared.title,
        author=prepared.author,
        digest=prepared.digest,
        client=client,
    )


def _format_wechat_error(exc: Exception) -> str:
    errcode = getattr(exc, "errcode", None)
    if errcode == 40164 or "40164" in str(exc):
        return (
            "WeChat API returned 40164 invalid ip. Add the public egress IP shown in "
            f"the original error to the Official Account API whitelist, then rerun.\n{exc}"
        )
    return str(exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a WeChat MP example HTML/preview pair, run dry-run validation, "
            "and optionally create a real draft."
        )
    )
    parser.add_argument(
        "slug",
        nargs="?",
        default=DEFAULT_SLUG,
        help=f"Example slug under examples/articles/. Defaults to {DEFAULT_SLUG}.",
    )
    parser.add_argument(
        "--theme", default=DEFAULT_THEME, help=f"Bundled theme name. Default: {DEFAULT_THEME}."
    )
    parser.add_argument(
        "--work-dir",
        default=str(DEFAULT_WORK_DIR),
        help="Generated work directory. Default: .tmp/examples.",
    )
    parser.add_argument(
        "--env-file",
        default=str(ROOT / ".env"),
        help="Local credential file for --create-draft. Must be ignored by git.",
    )
    parser.add_argument(
        "--create-draft",
        action="store_true",
        help="After dry-run validation, call WeChat APIs and print only the draft media_id.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        prepared = prepare_example(args.slug, args.theme, Path(args.work_dir))
        dry_run_info = inspect_prepared_example(prepared)

        if args.create_draft:
            media_id = create_real_draft(prepared, Path(args.env_file))
            print(media_id)
        else:
            print(json.dumps(dry_run_info, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(_format_wechat_error(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
