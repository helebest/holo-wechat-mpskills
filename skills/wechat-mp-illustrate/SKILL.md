---
name: wechat-mp-illustrate
description: Generate text-to-image or image-to-image assets for WeChat Official Account articles. Use when a WeChat MP / 微信公众号 article needs a cover image, body illustration, reference-image variation, or final image prompt turned into a local asset.
---

# WeChat MP Illustrate

Use this skill before typesetting when an article needs generated image assets. The
agent using the skill is responsible for writing the final image prompt from the
article context; this skill only turns that prompt, plus optional reference images,
into image files.

## OpenRouter Setup

Use `uv` for local dependency and script execution. From this repository, install
the locked development environment once:

```bash
uv sync
```

Configure OpenRouter in the process environment:

```text
OPENROUTER_API_KEY=your_api_key
OPENROUTER_IMAGE_MODEL=google/gemini-3-pro-image-preview
```

`OPENROUTER_IMAGE_MODEL` is optional. A `--model` argument overrides it for a
single command. The scripts do not load `.env` files; load one in your shell first
if you keep credentials locally.

## OpenRouter Workflow

Generate from a prompt:

```bash
uv run python <skill-dir>/scripts/illustrate.py \
  --prompt-file cover.prompt.txt \
  --output images/cover.png \
  --aspect-ratio 16:9
```

Generate from a prompt plus one or more reference images:

```bash
uv run python <skill-dir>/scripts/illustrate.py \
  --prompt "Create a clean WeChat article cover in the same visual direction." \
  --reference-image references/style.png \
  --output images/cover.png \
  --model google/gemini-3-pro-image-preview
```

Reference images can be local paths or remote URLs. Local paths are encoded as
base64 data URLs before the OpenRouter request.

## Codex Workflow

When this skill is used inside Codex and the built-in image generation capability
is available, the agent may use Codex's `gpt-image-2` image model instead of
OpenRouter. In that path:

1. Write the final prompt from the article context and any user constraints.
2. Use the built-in Codex image generation tool with `gpt-image-2`.
3. Save the generated asset under the article's image directory.
4. Insert or update the Markdown image reference before passing the article to
   `wechat-mp-typeset`.

This Codex path does not require `OPENROUTER_API_KEY` and is not implemented as a
Python runtime provider.

## Notes

- Keep prompts concrete: medium, subject, composition, palette, lighting, camera,
  text/no-text requirement, and aspect ratio.
- Do not print `OPENROUTER_API_KEY` or include it in generated files.
- Generated Markdown should be passed to `wechat-mp-typeset`.
