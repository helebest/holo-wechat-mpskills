from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import httpx
import pytest

from holo_wechat_wpskills.validate import ROOT


SCRIPTS = ROOT / "skills/wechat-mp-illustrate/scripts"


def load_script_module(module_name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(coro):
    return asyncio.run(coro)


def test_openrouter_image_client_uses_explicit_key_or_environment(monkeypatch: pytest.MonkeyPatch):
    api = load_script_module("wechat_illustrate_api_credentials", "api.py")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        api.OpenRouterImageClient()

    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    assert api.OpenRouterImageClient().api_key == "env-key"
    assert api.OpenRouterImageClient(api_key="explicit-key").api_key == "explicit-key"


def test_openrouter_image_model_uses_explicit_value_or_environment(
    monkeypatch: pytest.MonkeyPatch,
):
    api = load_script_module("wechat_illustrate_api_model", "api.py")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "env/image-model")

    assert api.OpenRouterImageClient().model == "env/image-model"
    assert api.OpenRouterImageClient(model="explicit/image-model").model == ("explicit/image-model")


def test_generate_text_to_image_posts_openrouter_payload_and_decodes_base64():
    api = load_script_module("wechat_illustrate_api_text_to_image", "api.py")
    image_bytes = b"fake png bytes"
    seen_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": "data:image/png;base64,"
                                        + base64.b64encode(image_bytes).decode("ascii")
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = api.OpenRouterImageClient(
        api_key="test-key",
        model="openrouter/image-model",
        transport=httpx.MockTransport(handler),
    )

    result = run(client.generate_image("A clean editorial cover", aspect_ratio="16:9"))

    assert result == image_bytes
    assert seen_payloads == [
        {
            "model": "openrouter/image-model",
            "messages": [{"role": "user", "content": "A clean editorial cover"}],
            "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "16:9"},
        }
    ]


def test_generate_image_with_local_and_remote_references(tmp_path: Path):
    api = load_script_module("wechat_illustrate_api_image_to_image", "api.py")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"reference bytes")
    seen_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": "data:image/png;base64,"
                                        + base64.b64encode(b"generated").decode("ascii")
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = api.OpenRouterImageClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    result = run(
        client.generate_image(
            "Turn this into a WeChat article cover",
            reference_images=[reference, "https://example.com/reference.jpg"],
        )
    )

    assert result == b"generated"
    content = seen_payloads[0]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "Turn this into a WeChat article cover"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[2] == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/reference.jpg"},
    }


def test_generate_image_file_writes_bytes(tmp_path: Path):
    api = load_script_module("wechat_illustrate_api_file", "api.py")
    output = tmp_path / "cover.png"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "images": [
                                {
                                    "image_url": {
                                        "url": "data:image/png;base64,"
                                        + base64.b64encode(b"generated file").decode("ascii")
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = api.OpenRouterImageClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    path = run(client.generate_image_file("A cover", output))

    assert path == output
    assert output.read_bytes() == b"generated file"


def test_openrouter_image_errors_are_explicit():
    api = load_script_module("wechat_illustrate_api_errors", "api.py")

    def http_error(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    client = api.OpenRouterImageClient(
        api_key="bad-key",
        transport=httpx.MockTransport(http_error),
    )
    with pytest.raises(api.OpenRouterImageError, match="401"):
        run(client.generate_image("A cover"))

    def missing_image(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "no image"}}]})

    client = api.OpenRouterImageClient(
        api_key="test-key",
        transport=httpx.MockTransport(missing_image),
    )
    with pytest.raises(api.OpenRouterImageError, match="No image"):
        run(client.generate_image("A cover"))

    def non_json(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not-json")

    client = api.OpenRouterImageClient(
        api_key="test-key",
        transport=httpx.MockTransport(non_json),
    )
    with pytest.raises(api.OpenRouterImageError, match="non-JSON"):
        run(client.generate_image("A cover"))


def test_cli_passes_prompt_model_key_reference_and_output_to_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    cli = load_script_module("wechat_illustrate_cli", "illustrate.py")
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("A precise prompt from file", encoding="utf-8")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"reference")
    output = tmp_path / "cover.png"
    seen: dict = {}

    class FakeClient:
        def __init__(self, api_key: str | None = None, model: str | None = None):
            seen["api_key"] = api_key
            seen["model"] = model

        async def generate_image_file(
            self,
            prompt: str,
            output_path: str | Path,
            *,
            aspect_ratio: str,
            reference_images: list[str],
        ) -> Path:
            seen["prompt"] = prompt
            seen["output_path"] = Path(output_path)
            seen["aspect_ratio"] = aspect_ratio
            seen["reference_images"] = reference_images
            Path(output_path).write_bytes(b"fake image")
            return Path(output_path)

    monkeypatch.setattr(cli, "_load_client_class", lambda: FakeClient)

    result = cli.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--output",
            str(output),
            "--model",
            "openrouter/image-model",
            "--openrouter-api-key",
            "explicit-key",
            "--reference-image",
            str(reference),
            "--aspect-ratio",
            "16:9",
        ]
    )

    assert result == 0
    assert output.read_bytes() == b"fake image"
    assert seen == {
        "api_key": "explicit-key",
        "model": "openrouter/image-model",
        "prompt": "A precise prompt from file",
        "output_path": output,
        "aspect_ratio": "16:9",
        "reference_images": [str(reference)],
    }
    assert str(output) in capsys.readouterr().out
