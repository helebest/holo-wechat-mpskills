---
name: wechat-mp-illustrate
description: Generate coherent illustrations for Markdown articles and insert them into the document. Use when a WeChat MP / 微信公众号 article needs AI-generated cover or body illustrations, visual scene planning, consistent characters, or image prompts.
---

# WeChat MP Illustrate

Use this skill before typesetting when a Markdown article needs generated illustrations.

## Setup

Install dependencies when needed:

```bash
python -m pip install -r <skill-dir>/scripts/requirements.txt
```

Configure OpenRouter access:

```text
OPENROUTER_API_KEY=your_api_key
TEXT_MODEL=google/gemini-3-pro-preview
IMAGE_MODEL=google/gemini-3-pro-image-preview
MAX_DOC_LEN=5000
```

## Workflow

Run the illustrator:

```bash
python <skill-dir>/scripts/illustrate.py article.md --output output --style "clean editorial illustration"
```

The script:

1. Adds paragraph anchors such as `<!-- [P1] -->`.
2. Asks the text model for a JSON visual plan with characters, style, aspect ratio, and scene insertion anchors.
3. Generates images for planned scenes.
4. Writes an illustrated Markdown file and an `images/` directory.

## Notes

- The prompt contract is stored in `scripts/prompts.py`.
- Generated Markdown should be passed to `wechat-mp-typeset`.
- Keep custom style instructions concrete: medium, palette, lighting, camera, and aspect ratio preference.
