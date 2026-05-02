import asyncio
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

try:
    from .api import OpenRouterClient
    from .models import ArticleIllustratorOutput, SceneDescription, StoryAnalysis
    from .prompts import SYSTEM_PROMPT_STORY_ANALYSIS, USER_PROMPT_STORY_ANALYSIS
except ImportError:
    from api import OpenRouterClient
    from models import ArticleIllustratorOutput, SceneDescription, StoryAnalysis
    from prompts import SYSTEM_PROMPT_STORY_ANALYSIS, USER_PROMPT_STORY_ANALYSIS

load_dotenv()

DEFAULT_TEXT_MODEL = "google/gemini-3-pro-preview"
DEFAULT_IMAGE_MODEL = "google/gemini-3-pro-image-preview"
DEFAULT_MAX_DOC_LEN = 5000


def insert_paragraph_anchors(markdown: str) -> str:
    """Insert <!-- [P1] -->, <!-- [P2] -->, etc. after each paragraph."""
    paragraphs = re.split(r"(\n\s*\n)", markdown)
    result = []
    anchor_idx = 1

    for part in paragraphs:
        result.append(part)
        if part.strip():
            result.append(f"\n<!-- [P{anchor_idx}] -->")
            anchor_idx += 1

    return "".join(result)


def remove_unused_anchors(markdown: str) -> str:
    """Remove all remaining <!-- [Pn] --> anchors that weren't replaced."""
    return re.sub(r"\n?<!-- \[P\d+\] -->", "", markdown)


class ArticleIllustrator:
    def __init__(self, api_key: str | None = None):
        self.client = OpenRouterClient(api_key)
        self.text_model = os.getenv("TEXT_MODEL", DEFAULT_TEXT_MODEL)
        self.image_model = os.getenv("IMAGE_MODEL", DEFAULT_IMAGE_MODEL)
        self.max_doc_len = int(os.getenv("MAX_DOC_LEN", str(DEFAULT_MAX_DOC_LEN)))

    async def analyze_story(
        self, markdown_content: str, custom_requirements: str = ""
    ) -> StoryAnalysis:
        requirements_text = (
            custom_requirements.strip() or "(Use your best judgment based on article content)"
        )

        user_content = USER_PROMPT_STORY_ANALYSIS.format(
            markdown_content=markdown_content[: self.max_doc_len],
            custom_requirements=requirements_text,
        )

        response = await self.client.chat_completion(
            model=self.text_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_STORY_ANALYSIS},
                {"role": "user", "content": user_content},
            ],
        )

        data = self._parse_json(response)
        return StoryAnalysis(**data)

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from response, handling markdown code blocks."""
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try extracting JSON object by braces
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Failed to parse JSON response: {text[:100]}...")

    def inject_placeholders(
        self, md_with_anchors: str, analysis: StoryAnalysis
    ) -> tuple[str, list[SceneDescription]]:
        """Replace anchor <!-- [Pn] --> with <!-- SCENE_X --> based on insert_after field."""
        result = md_with_anchors

        for scene in analysis.scenes:
            anchor_id = self._normalize_anchor_id(scene.insert_after)
            if not anchor_id:
                print(f"[WARN] Scene {scene.index} has no insert_after. Skipping.")
                continue

            anchor = f"<!-- [{anchor_id}] -->"
            scene_marker = f"<!-- SCENE_{scene.index} -->"

            if anchor in result:
                result = result.replace(anchor, scene_marker)
                print(f"[INFO] Inserted placeholder for Scene {scene.index} at anchor {anchor_id}")
            else:
                print(f"[WARN] Anchor {anchor_id} not found for Scene {scene.index}")
                result += f"\n{scene_marker}\n"

        return result, analysis.scenes

    def _normalize_anchor_id(self, raw_id: str) -> str:
        """Normalize anchor ID to 'Pn' format (handles 'P1', '1', '[P1]')."""
        anchor_id = raw_id.strip()
        if not anchor_id:
            return ""
        if not anchor_id.startswith("P"):
            anchor_id = f"P{anchor_id}"
        return anchor_id

    def _lookup_character_description(self, char_id: str, char_map: dict[str, str]) -> str:
        """Look up character description by ID with partial match fallback."""
        if char_id in char_map:
            return char_map[char_id]

        for key, desc in char_map.items():
            if char_id in key or key in char_id:
                return desc

        return "(No specific description found)"

    def _build_scene_prompt(
        self, scene: SceneDescription, analysis: StoryAnalysis, char_map: dict[str, str]
    ) -> str:
        """Build the image generation prompt for a scene."""
        char_prompts = [
            f"{char_id}: {self._lookup_character_description(char_id, char_map)}"
            for char_id in scene.characters
        ]

        prompt_data = {
            "style": analysis.global_style,
            "characters_present": "\n".join(char_prompts),
            "scene_action": scene.scene_description,
            "aspect_ratio": analysis.aspect_ratio,
            "quality": "High quality, detailed, cinematic lighting",
            "negative_prompt": analysis.negative_prompt,
        }
        return json.dumps(prompt_data, ensure_ascii=False)

    async def generate_images(self, analysis: StoryAnalysis, output_dir: str = "output_images"):
        """Generate images for all scenes in parallel with concurrency limit."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        semaphore = asyncio.Semaphore(3)
        char_map = {c.id: c.description for c in analysis.characters}

        async def process_scene(scene: SceneDescription):
            async with semaphore:
                scene.final_prompt = self._build_scene_prompt(scene, analysis, char_map)
                print(f"[INFO] Generating image for Scene {scene.index}...")

                try:
                    img_bytes = await self.client.generate_image(
                        scene.final_prompt,
                        model=self.image_model,
                        aspect_ratio=analysis.aspect_ratio,
                    )
                    file_path = output_path / f"scene_{scene.index}.png"
                    file_path.write_bytes(img_bytes)
                    scene.image_path = str(file_path)
                    print(f"[SUCCESS] Scene {scene.index} saved.")
                except Exception as e:
                    print(f"[ERROR] Scene {scene.index} failed: {e}")

        await asyncio.gather(*[process_scene(scene) for scene in analysis.scenes])

    def assemble_final(
        self, markdown_with_placeholders: str, scenes: list[SceneDescription]
    ) -> str:
        """Replace placeholders with image tags in the final markdown."""
        result = markdown_with_placeholders

        for scene in scenes:
            if not scene.image_path:
                continue

            rel_path = f"./images/{Path(scene.image_path).name}"
            img_tag = f"![Illustration]({rel_path})"
            placeholder = f"<!-- SCENE_{scene.index} -->"

            if placeholder in result:
                result = result.replace(placeholder, img_tag)
            else:
                result += f"\n\n{img_tag}\n"

        return result

    async def run(
        self,
        markdown_path: str,
        output_dir: str = "output",
        custom_requirements: str = "",
    ) -> ArticleIllustratorOutput:
        """Execute the full illustration pipeline from a file path."""
        input_path = Path(markdown_path)
        content = input_path.read_text(encoding="utf-8")
        output_filename = f"{input_path.stem}_illustrated{input_path.suffix}"
        return await self.run_from_content(
            content, output_dir, output_filename, custom_requirements
        )

    async def run_from_content(
        self,
        content: str,
        output_dir: str = "output",
        output_filename: str = "illustrated.md",
        custom_requirements: str = "",
    ) -> ArticleIllustratorOutput:
        """Execute the full illustration pipeline from markdown content directly."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Pre-process: insert paragraph anchors for LLM to reference
        print("Step 0: Inserting paragraph anchors...")
        content_with_anchors = insert_paragraph_anchors(content)

        print("Step 1: Analyzing story (Style, Characters, Scenes)...")
        if custom_requirements:
            print(f"Custom requirements: {custom_requirements[:50]}...")
        analysis = await self.analyze_story(content_with_anchors, custom_requirements)
        print(
            f"Analysis Complete: {len(analysis.characters)} characters, {len(analysis.scenes)} scenes."
        )

        print("Step 2: Injecting placeholders...")
        md_with_placeholders, _ = self.inject_placeholders(content_with_anchors, analysis)

        print("Step 3: Generating images...")
        await self.generate_images(analysis, str(output_path / "images"))

        print("Step 4: Assembling final markdown...")
        final_md = self.assemble_final(md_with_placeholders, analysis.scenes)

        # Post-process: remove any unused anchors
        final_md = remove_unused_anchors(final_md)

        output_md_path = output_path / output_filename
        output_md_path.write_text(final_md, encoding="utf-8")

        print(f"Success! Saved to {output_md_path}")

        return ArticleIllustratorOutput(
            original_markdown=content,
            illustrated_markdown=final_md,
            output_path=str(output_md_path),
            analysis=analysis,
        )
