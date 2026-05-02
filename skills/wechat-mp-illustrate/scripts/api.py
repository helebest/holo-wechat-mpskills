from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

import httpx


BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_IMAGE_MODEL = "google/gemini-3-pro-image-preview"


class OpenRouterImageError(RuntimeError):
    """Raised when OpenRouter does not return a usable image."""


class OpenRouterImageClient:
    """Small OpenRouter image-generation client for text-to-image and image-to-image."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set; pass --openrouter-api-key or set "
                "OPENROUTER_API_KEY in the process environment"
            )

        self.model = model or os.getenv("OPENROUTER_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL
        self.transport = transport
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "WeChat MP Illustrate Skill",
        }

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        aspect_ratio: str = "1:1",
        reference_images: list[str | Path] | None = None,
    ) -> bytes:
        """Generate image bytes from a prompt and optional reference images."""
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("prompt is required")

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": [
                {
                    "role": "user",
                    "content": self._build_message_content(prompt, reference_images or []),
                }
            ],
            "modalities": ["image", "text"],
        }
        if aspect_ratio:
            payload["image_config"] = {"aspect_ratio": aspect_ratio}

        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            if response.status_code >= 400:
                raise OpenRouterImageError(
                    f"OpenRouter image request failed: {response.status_code} "
                    f"{self._response_error_message(response)}"
                )

            data = self._read_json(response)
            image_url = self._extract_image_url(data)
            return await self._decode_image(client, image_url)

    async def generate_image_file(
        self,
        prompt: str,
        output_path: str | Path,
        *,
        model: str | None = None,
        aspect_ratio: str = "1:1",
        reference_images: list[str | Path] | None = None,
    ) -> Path:
        """Generate an image and write it to output_path."""
        output = Path(output_path)
        image_bytes = await self.generate_image(
            prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            reference_images=reference_images,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image_bytes)
        return output

    def _build_message_content(
        self,
        prompt: str,
        reference_images: list[str | Path],
    ) -> str | list[dict[str, Any]]:
        if not reference_images:
            return prompt

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for reference in reference_images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._reference_image_url(reference)},
                }
            )
        return content

    def _reference_image_url(self, reference: str | Path) -> str:
        reference_text = str(reference)
        if reference_text.startswith(("http://", "https://", "data:image/")):
            return reference_text

        path = Path(reference)
        if not path.exists():
            raise FileNotFoundError(f"Reference image not found: {path}")

        mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _read_json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise OpenRouterImageError("OpenRouter returned a non-JSON response") from exc

        if not isinstance(data, dict):
            raise OpenRouterImageError("OpenRouter returned a JSON response that is not an object")
        return data

    def _extract_image_url(self, data: dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            message = self._error_message_from_data(data)
            raise OpenRouterImageError(f"No choices returned from OpenRouter: {message}")

        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        images = message.get("images") if isinstance(message, dict) else None
        if not isinstance(images, list) or not images:
            raise OpenRouterImageError("No image generated in OpenRouter response")

        image = images[0]
        if not isinstance(image, dict):
            raise OpenRouterImageError("OpenRouter image response has an invalid image entry")

        image_url = image.get("image_url") or image.get("imageUrl")
        if isinstance(image_url, dict):
            image_url = image_url.get("url")

        if not isinstance(image_url, str) or not image_url:
            raise OpenRouterImageError("OpenRouter image response did not include an image URL")
        return image_url

    async def _decode_image(self, client: httpx.AsyncClient, image_url: str) -> bytes:
        if image_url.startswith("data:image"):
            try:
                _prefix, encoded = image_url.split(",", 1)
                return base64.b64decode(encoded)
            except ValueError as exc:
                raise OpenRouterImageError("OpenRouter returned an invalid data URI") from exc

        response = await client.get(image_url)
        if response.status_code >= 400:
            raise OpenRouterImageError(
                f"Generated image download failed: {response.status_code} "
                f"{self._response_error_message(response)}"
            )
        return response.content

    def _response_error_message(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text
        return self._error_message_from_data(data)

    def _error_message_from_data(self, data: Any) -> str:
        if isinstance(data, dict):
            error = data.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str):
                    return message
            message = data.get("message")
            if isinstance(message, str):
                return message
        return "Unknown error"
