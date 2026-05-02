#!/usr/bin/env python3
"""CLI for safe WeChat MP draft and published article management."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO


def _load_modules() -> tuple[Any, Any]:
    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from draft_manager import DraftManager
        from wechat_client import WeChatClient
    else:
        from .draft_manager import DraftManager
        from .wechat_client import WeChatClient

    return DraftManager, WeChatClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage WeChat MP drafts and published articles.")
    subparsers = parser.add_subparsers(dest="resource", required=True)

    draft = subparsers.add_parser("draft", help="Manage drafts.")
    draft_subparsers = draft.add_subparsers(dest="action", required=True)
    draft_list = draft_subparsers.add_parser("list", help="List drafts.")
    draft_list.add_argument("--offset", type=int, default=0)
    draft_list.add_argument("--count", type=int, default=20)
    draft_list.add_argument("--no-content", action="store_true")
    draft_get = draft_subparsers.add_parser("get", help="Get a draft by media_id.")
    draft_get.add_argument("--media-id", required=True)
    draft_delete = draft_subparsers.add_parser("delete", help="Delete a draft.")
    draft_delete.add_argument("--media-id", required=True)
    draft_delete.add_argument("--confirm-media-id")
    draft_publish = draft_subparsers.add_parser("publish", help="Publish a draft.")
    draft_publish.add_argument("--media-id", required=True)
    draft_publish.add_argument("--confirm-media-id")

    published = subparsers.add_parser("published", help="Manage published articles.")
    published_subparsers = published.add_subparsers(dest="action", required=True)
    published_list = published_subparsers.add_parser("list", help="List published articles.")
    published_list.add_argument("--offset", type=int, default=0)
    published_list.add_argument("--count", type=int, default=20)
    published_list.add_argument("--no-content", action="store_true")
    published_delete = published_subparsers.add_parser("delete", help="Delete a published article.")
    published_delete.add_argument("--article-id", required=True)
    published_delete.add_argument("--index", type=int, default=0)
    published_delete.add_argument("--confirm-article-id")

    return parser


def _json_print(payload: Any, stdout: TextIO) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=stdout)


def main(
    argv: list[str] | None = None,
    *,
    client: Any | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        DraftManager, WeChatClient = _load_modules()
        manager = DraftManager(client if client is not None else WeChatClient())

        if args.resource == "draft" and args.action == "list":
            _json_print(
                manager.list_drafts(
                    offset=args.offset, count=args.count, no_content=args.no_content
                ),
                stdout,
            )
            return 0
        if args.resource == "draft" and args.action == "get":
            _json_print(manager.get_draft(args.media_id), stdout)
            return 0
        if args.resource == "draft" and args.action == "delete":
            manager.delete_draft(args.media_id, confirm_media_id=args.confirm_media_id)
            _json_print({"ok": True}, stdout)
            return 0
        if args.resource == "draft" and args.action == "publish":
            publish_id = manager.publish_draft(
                args.media_id, confirm_media_id=args.confirm_media_id
            )
            _json_print({"publish_id": publish_id}, stdout)
            return 0
        if args.resource == "published" and args.action == "list":
            _json_print(
                manager.list_published(
                    offset=args.offset, count=args.count, no_content=args.no_content
                ),
                stdout,
            )
            return 0
        if args.resource == "published" and args.action == "delete":
            manager.delete_published(
                args.article_id,
                index=args.index,
                confirm_article_id=args.confirm_article_id,
            )
            _json_print({"ok": True}, stdout)
            return 0

        parser.error("unsupported command")
        return 2
    except Exception as exc:
        print(str(exc), file=stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
