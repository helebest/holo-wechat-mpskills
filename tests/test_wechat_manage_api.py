from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from holo_wechat_wpskills.validate import ROOT


MANAGE_SCRIPTS = ROOT / "skills/wechat-mp-manage/scripts"


def manage_module(name: str):
    if str(MANAGE_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(MANAGE_SCRIPTS))
    return importlib.import_module(name)


class FakeResponse:
    def __init__(
        self,
        payload: dict | None = None,
        *,
        content: bytes = b"",
        headers: dict | None = None,
        json_error: Exception | None = None,
        status_code: int = 200,
        text: str = "",
    ):
        self.payload = payload or {}
        self.content = content
        self.headers = headers or {"Content-Type": "application/json"}
        self.json_error = json_error
        self.status_code = status_code
        self.text = text

    def json(self) -> dict:
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, *, get_responses: list[FakeResponse] | None = None):
        self.get_responses = get_responses or []
        self.request_responses: list[FakeResponse] = []
        self.post_responses: list[FakeResponse] = []
        self.get_calls: list[dict] = []
        self.request_calls: list[dict] = []
        self.post_calls: list[dict] = []

    def get(self, url: str, params: dict | None = None, **kwargs) -> FakeResponse:
        self.get_calls.append({"url": url, "params": dict(params or {}), "kwargs": kwargs})
        return self.get_responses.pop(0)

    def request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        files: dict | None = None,
        data=None,
    ) -> FakeResponse:
        self.request_calls.append(
            {
                "method": method,
                "url": url,
                "params": dict(params or {}),
                "headers": headers,
                "files": files,
                "data": data,
            }
        )
        return self.request_responses.pop(0)

    def post(self, url: str, params: dict | None = None, json=None, **kwargs) -> FakeResponse:
        self.post_calls.append(
            {"url": url, "params": dict(params or {}), "json": json, "kwargs": kwargs}
        )
        return self.post_responses.pop(0)


class ConsumingUploadSession(FakeSession):
    def request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        files: dict | None = None,
        data=None,
    ) -> FakeResponse:
        if files:
            file_obj = next(iter(files.values()))[1]
            self.request_calls.append({"file_position_before_send": file_obj.tell()})
            file_obj.read()
        return super().request(method, url, params=params, headers=headers, files=files, data=data)


class RecordingApiClient:
    def __init__(self):
        self.uploads: list[dict] = []
        self.posts: list[dict] = []

    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        file_field: str = "media",
        extra_data: dict | None = None,
    ) -> dict:
        self.uploads.append(
            {
                "endpoint": endpoint,
                "file_path": file_path,
                "file_field": file_field,
                "extra_data": extra_data,
            }
        )
        if endpoint == "/cgi-bin/material/add_material":
            return {"media_id": "cover-media-id"}
        if endpoint == "/cgi-bin/media/uploadimg":
            return {"url": "https://mmbiz.qpic.cn/body-image.png"}
        raise AssertionError(f"unexpected upload endpoint: {endpoint}")

    def post(self, endpoint: str, json_data: dict | None = None, **kwargs) -> dict:
        self.posts.append({"endpoint": endpoint, "json_data": json_data, "kwargs": kwargs})
        if endpoint == "/cgi-bin/draft/add":
            return {"media_id": "draft-media-id"}
        if endpoint == "/cgi-bin/freepublish/submit":
            return {"publish_id": "publish-id"}
        return {}

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        return {"endpoint": endpoint, "params": params}


def test_wechat_client_gets_and_caches_access_token(tmp_path: Path) -> None:
    wechat_client = manage_module("wechat_client")
    session = FakeSession(
        get_responses=[FakeResponse({"access_token": "token-1", "expires_in": 7200})]
    )
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=session
    )

    assert client.get_access_token() == "token-1"
    assert client.get_access_token() == "token-1"
    assert len(session.get_calls) == 1
    assert session.get_calls[0]["params"]["appid"] == "appid"


def test_wechat_client_reads_wechat_mp_environment_variables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wechat_client = manage_module("wechat_client")
    monkeypatch.delenv("WECHAT_" + "APPID", raising=False)
    monkeypatch.delenv("WECHAT_" + "APPSECRET", raising=False)
    monkeypatch.setenv("WECHAT_MP_APPID", "env-appid")
    monkeypatch.setenv("WECHAT_MP_APPSECRET", "env-secret")
    session = FakeSession(
        get_responses=[FakeResponse({"access_token": "token-1", "expires_in": 7200})]
    )
    client = wechat_client.WeChatClient(token_cache_dir=str(tmp_path), session=session)

    assert client.get_access_token() == "token-1"
    assert session.get_calls[0]["params"]["appid"] == "env-appid"
    assert session.get_calls[0]["params"]["secret"] == "env-secret"


def test_wechat_client_ignores_legacy_environment_variable_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wechat_client = manage_module("wechat_client")
    monkeypatch.delenv("WECHAT_MP_APPID", raising=False)
    monkeypatch.delenv("WECHAT_MP_APPSECRET", raising=False)
    monkeypatch.setenv("WECHAT_" + "APPID", "legacy-appid")
    monkeypatch.setenv("WECHAT_" + "APPSECRET", "legacy-secret")

    with pytest.raises(ValueError, match="WECHAT_MP_APPID"):
        wechat_client.WeChatClient(token_cache_dir=str(tmp_path), session=FakeSession())


def test_wechat_client_explicit_credentials_override_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wechat_client = manage_module("wechat_client")
    monkeypatch.setenv("WECHAT_MP_APPID", "env-appid")
    monkeypatch.setenv("WECHAT_MP_APPSECRET", "env-secret")
    session = FakeSession(
        get_responses=[FakeResponse({"access_token": "token-1", "expires_in": 7200})]
    )
    client = wechat_client.WeChatClient(
        appid="explicit-appid",
        appsecret="explicit-secret",
        token_cache_dir=str(tmp_path),
        session=session,
    )

    assert client.get_access_token() == "token-1"
    assert session.get_calls[0]["params"]["appid"] == "explicit-appid"
    assert session.get_calls[0]["params"]["secret"] == "explicit-secret"


def test_wechat_client_token_response_errors_are_explicit(tmp_path: Path) -> None:
    wechat_client = manage_module("wechat_client")

    bad_json = FakeSession(
        get_responses=[
            FakeResponse(json_error=ValueError("not json"), status_code=502, text="<html>")
        ]
    )
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=bad_json
    )
    with pytest.raises(wechat_client.WeChatAPIError, match="non-JSON"):
        client.get_access_token()

    missing_token = FakeSession(get_responses=[FakeResponse({"expires_in": 7200})])
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=missing_token
    )
    with pytest.raises(wechat_client.WeChatAPIError, match="missing access_token"):
        client.get_access_token()


def test_wechat_client_refreshes_expired_token_once(tmp_path: Path) -> None:
    wechat_client = manage_module("wechat_client")
    session = FakeSession(
        get_responses=[
            FakeResponse({"access_token": "old-token", "expires_in": 7200}),
            FakeResponse({"access_token": "new-token", "expires_in": 7200}),
        ]
    )
    session.request_responses.extend(
        [
            FakeResponse({"errcode": 40001, "errmsg": "invalid credential"}),
            FakeResponse({"errcode": 0, "ok": True}),
        ]
    )
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=session
    )

    assert client.post("/cgi-bin/draft/count") == {"errcode": 0, "ok": True}
    assert [call["params"]["access_token"] for call in session.request_calls] == [
        "old-token",
        "new-token",
    ]
    assert len(session.get_calls) == 2


def test_wechat_client_rewinds_upload_files_before_token_retry(tmp_path: Path) -> None:
    wechat_client = manage_module("wechat_client")
    upload = tmp_path / "cover.png"
    upload.write_bytes(b"cover-bytes")
    session = ConsumingUploadSession(
        get_responses=[
            FakeResponse({"access_token": "old-token", "expires_in": 7200}),
            FakeResponse({"access_token": "new-token", "expires_in": 7200}),
        ]
    )
    session.request_responses.extend(
        [
            FakeResponse({"errcode": 40001, "errmsg": "invalid credential"}),
            FakeResponse({"errcode": 0, "media_id": "cover-media-id"}),
        ]
    )
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=session
    )

    assert client.upload_file("/cgi-bin/material/add_material", str(upload)) == {
        "errcode": 0,
        "media_id": "cover-media-id",
    }
    assert [
        call["file_position_before_send"]
        for call in session.request_calls
        if "file_position_before_send" in call
    ] == [0, 0]


def test_wechat_client_preserves_non_retryable_api_errors(tmp_path: Path) -> None:
    wechat_client = manage_module("wechat_client")
    session = FakeSession(
        get_responses=[FakeResponse({"access_token": "token-1", "expires_in": 7200})]
    )
    session.request_responses.append(
        FakeResponse({"errcode": 40164, "errmsg": "invalid ip 111.196.221.200"})
    )
    client = wechat_client.WeChatClient(
        appid="appid", appsecret="secret", token_cache_dir=str(tmp_path), session=session
    )

    with pytest.raises(wechat_client.WeChatAPIError) as exc:
        client.post("/cgi-bin/material/add_material")
    assert exc.value.errcode == 40164
    assert "invalid ip" in exc.value.errmsg


def test_material_manager_uploads_cover_and_article_images(tmp_path: Path) -> None:
    material_manager = manage_module("material_manager")
    image = tmp_path / "image.png"
    image.write_bytes(b"png")
    api = RecordingApiClient()
    manager = material_manager.MaterialManager(api)

    assert manager.upload_permanent("image", str(image)) == "cover-media-id"
    assert manager.upload_article_image(str(image)) == "https://mmbiz.qpic.cn/body-image.png"
    assert [upload["endpoint"] for upload in api.uploads] == [
        "/cgi-bin/material/add_material",
        "/cgi-bin/media/uploadimg",
    ]
    assert api.uploads[0]["extra_data"] == {"type": "image"}


def test_draft_manager_creates_expected_draft_payload() -> None:
    draft_manager = manage_module("draft_manager")
    api = RecordingApiClient()
    manager = draft_manager.DraftManager(api)
    article = draft_manager.create_simple_article(
        title="Title", content="<p>Body</p>", thumb_media_id="cover-media-id", author="holo"
    )

    assert manager.create_draft([article]) == "draft-media-id"
    assert api.posts == [
        {
            "endpoint": "/cgi-bin/draft/add",
            "json_data": {"articles": [article]},
            "kwargs": {},
        }
    ]


def test_submit_html_draft_uploads_images_rewrites_html_and_creates_draft(tmp_path: Path) -> None:
    html_submitter = manage_module("html_submitter")
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"cover")
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    body_image = image_dir / "body.png"
    body_image.write_bytes(b"body")
    html = tmp_path / "article.html"
    html.write_text(
        '<html><head><title>Draft</title></head><body><p>Body</p><img src="images/body.png"></body></html>',
        encoding="utf-8",
    )
    api = RecordingApiClient()

    media_id = html_submitter.submit_html_draft(
        str(html), str(cover), author="holo", digest="digest", client=api
    )

    assert media_id == "draft-media-id"
    draft_payload = api.posts[0]["json_data"]["articles"][0]
    assert draft_payload["thumb_media_id"] == "cover-media-id"
    assert draft_payload["author"] == "holo"
    assert "https://mmbiz.qpic.cn/body-image.png" in draft_payload["content"]
    assert "images/body.png" not in draft_payload["content"]


def test_submit_html_draft_local_validation_blocks_api_calls(tmp_path: Path) -> None:
    html_submitter = manage_module("html_submitter")
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"cover")
    html = tmp_path / "article.html"
    html.write_text(
        '<html><head><title>Draft</title></head><body><img src="missing.png"></body></html>',
        encoding="utf-8",
    )
    api = RecordingApiClient()

    with pytest.raises(html_submitter.ImageUploadError, match="文件不存在"):
        html_submitter.submit_html_draft(str(html), str(cover), client=api)
    assert api.uploads == []
    assert api.posts == []

    html.write_text("<html><body><p>Body</p></body></html>", encoding="utf-8")
    with pytest.raises(html_submitter.HtmlSubmitError, match="标题长度不能超过64个字符"):
        html_submitter.submit_html_draft(str(html), str(cover), title="长" * 65, client=api)
    assert api.uploads == []
    assert api.posts == []


def test_draft_high_risk_actions_require_explicit_confirmation() -> None:
    draft_manager = manage_module("draft_manager")
    api = RecordingApiClient()
    manager = draft_manager.DraftManager(api)

    with pytest.raises(ValueError, match="confirm_media_id"):
        manager.publish_draft("draft-media-id")
    with pytest.raises(ValueError, match="confirm_media_id"):
        manager.delete_draft("draft-media-id")
    with pytest.raises(ValueError, match="confirm_article_id"):
        manager.delete_published("article-id")
    assert api.posts == []


def test_draft_high_risk_actions_call_api_when_confirmed() -> None:
    draft_manager = manage_module("draft_manager")
    api = RecordingApiClient()
    manager = draft_manager.DraftManager(api)

    assert (
        manager.publish_draft("draft-media-id", confirm_media_id="draft-media-id") == "publish-id"
    )
    assert manager.delete_draft("draft-media-id", confirm_media_id="draft-media-id") is True
    assert manager.delete_published("article-id", confirm_article_id="article-id") is True
    assert [post["endpoint"] for post in api.posts] == [
        "/cgi-bin/freepublish/submit",
        "/cgi-bin/draft/delete",
        "/cgi-bin/freepublish/delete",
    ]
