import base64
import json
import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "WeChat MP Illustrate Skill",
        }

    def _validate_response(self, data: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Validate API response contains expected 'choices' field."""
        if "choices" in data and data["choices"]:
            return data

        error_msg = data.get("error", {}).get("message", "Unknown error")
        print(f"[ERROR] {context}API Response missing 'choices'. Error: {error_msg}")
        if "content_filter" in str(data):
            print("[WARN] Content filter might have blocked the response.")
        raise ValueError(f"API Error: {error_msg}. Full response: {json.dumps(data)}")

    async def chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{BASE_URL}/chat/completions"
        payload = {"model": model, "messages": messages, **kwargs}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"Error from OpenRouter: {response.status_code} - {response.text}")
                response.raise_for_status()
            data = self._validate_response(response.json())
            return data["choices"][0]["message"]["content"]

    async def generate_image(
        self,
        prompt: str,
        model: str = "google/gemini-3-pro-image-preview",
        aspect_ratio: str = "1:1",
    ) -> bytes:
        """Generate image using OpenRouter. Returns the image content as bytes."""
        url = f"{BASE_URL}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
        }

        if "banana" in model or "image" in model:
            payload["aspect_ratio"] = aspect_ratio

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"Error from OpenRouter (Image): {response.status_code} - {response.text}")
                response.raise_for_status()

            data = self._validate_response(response.json(), context="Image ")
            message = data["choices"][0]["message"]

            if "images" not in message or not message["images"]:
                raise ValueError("No image generated in response")

            img_data = message["images"][0]["image_url"]["url"]
            return await self._decode_image(client, img_data)

    async def _decode_image(self, client: httpx.AsyncClient, img_data: str) -> bytes:
        """Decode image from base64 data URI or fetch from URL."""
        if img_data.startswith("data:image"):
            _, encoded = img_data.split(",", 1)
            return base64.b64decode(encoded)

        img_response = await client.get(img_data)
        img_response.raise_for_status()
        return img_response.content
