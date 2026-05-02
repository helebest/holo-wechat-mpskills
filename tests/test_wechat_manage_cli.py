from __future__ import annotations

import importlib
import io
import json
import sys

from holo_wechat_wpskills.validate import ROOT


MANAGE_SCRIPTS = ROOT / "skills/wechat-mp-manage/scripts"


def manage_module(name: str):
    if str(MANAGE_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(MANAGE_SCRIPTS))
    return importlib.import_module(name)


class RecordingClient:
    def __init__(self):
        self.posts: list[dict] = []

    def post(self, endpoint: str, json_data: dict | None = None) -> dict:
        self.posts.append({"endpoint": endpoint, "json_data": json_data})
        if endpoint == "/cgi-bin/draft/batchget":
            return {"total_count": 1, "item_count": 1, "item": [{"media_id": "draft-1"}]}
        if endpoint == "/cgi-bin/draft/get":
            return {"news_item": [{"title": "Draft title"}]}
        if endpoint == "/cgi-bin/draft/delete":
            return {"errcode": 0}
        if endpoint == "/cgi-bin/freepublish/submit":
            return {"publish_id": "publish-1"}
        if endpoint == "/cgi-bin/freepublish/batchget":
            return {"total_count": 1, "item_count": 1, "item": [{"article_id": "article-1"}]}
        if endpoint == "/cgi-bin/freepublish/delete":
            return {"errcode": 0}
        raise AssertionError(f"unexpected endpoint: {endpoint}")


def run_cli(argv: list[str], client: RecordingClient) -> tuple[int, str, str]:
    manage = manage_module("manage")
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = manage.main(argv, client=client, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_draft_list_outputs_json_and_calls_batchget() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["draft", "list"], client)

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {
        "total_count": 1,
        "item_count": 1,
        "item": [{"media_id": "draft-1"}],
    }
    assert client.posts == [
        {
            "endpoint": "/cgi-bin/draft/batchget",
            "json_data": {"offset": 0, "count": 20, "no_content": 0},
        }
    ]


def test_draft_get_outputs_json_and_calls_get_endpoint() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["draft", "get", "--media-id", "draft-1"], client)

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"news_item": [{"title": "Draft title"}]}
    assert client.posts == [
        {"endpoint": "/cgi-bin/draft/get", "json_data": {"media_id": "draft-1"}}
    ]


def test_draft_delete_requires_matching_confirmation_before_api_call() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["draft", "delete", "--media-id", "draft-1"], client)

    assert code == 1
    assert stdout == ""
    assert "confirm_media_id" in stderr
    assert client.posts == []


def test_draft_delete_calls_api_when_confirmation_matches() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(
        [
            "draft",
            "delete",
            "--media-id",
            "draft-1",
            "--confirm-media-id",
            "draft-1",
        ],
        client,
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"ok": True}
    assert client.posts == [
        {"endpoint": "/cgi-bin/draft/delete", "json_data": {"media_id": "draft-1"}}
    ]


def test_draft_publish_requires_matching_confirmation_before_api_call() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["draft", "publish", "--media-id", "draft-1"], client)

    assert code == 1
    assert stdout == ""
    assert "confirm_media_id" in stderr
    assert client.posts == []


def test_draft_publish_calls_api_when_confirmation_matches() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(
        [
            "draft",
            "publish",
            "--media-id",
            "draft-1",
            "--confirm-media-id",
            "draft-1",
        ],
        client,
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"publish_id": "publish-1"}
    assert client.posts == [
        {"endpoint": "/cgi-bin/freepublish/submit", "json_data": {"media_id": "draft-1"}}
    ]


def test_published_list_outputs_json_and_calls_batchget() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["published", "list", "--no-content"], client)

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {
        "total_count": 1,
        "item_count": 1,
        "item": [{"article_id": "article-1"}],
    }
    assert client.posts == [
        {
            "endpoint": "/cgi-bin/freepublish/batchget",
            "json_data": {"offset": 0, "count": 20, "no_content": 1},
        }
    ]


def test_published_delete_requires_matching_confirmation_before_api_call() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(["published", "delete", "--article-id", "article-1"], client)

    assert code == 1
    assert stdout == ""
    assert "confirm_article_id" in stderr
    assert client.posts == []


def test_published_delete_calls_api_when_confirmation_matches() -> None:
    client = RecordingClient()

    code, stdout, stderr = run_cli(
        [
            "published",
            "delete",
            "--article-id",
            "article-1",
            "--index",
            "2",
            "--confirm-article-id",
            "article-1",
        ],
        client,
    )

    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {"ok": True}
    assert client.posts == [
        {
            "endpoint": "/cgi-bin/freepublish/delete",
            "json_data": {"article_id": "article-1", "index": 2},
        }
    ]
