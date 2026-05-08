# Holo WeChat MP Skills

[![CI](https://github.com/helebest/holo-wechat-mpskills/actions/workflows/ci.yml/badge.svg)](https://github.com/helebest/holo-wechat-mpskills/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/helebest/holo-wechat-mpskills)](https://github.com/helebest/holo-wechat-mpskills/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/helebest/holo-wechat-mpskills/blob/main/LICENSE)

Production-ready Agent Skills for WeChat Official Account article operations,
packaged as local plugins for Codex, Claude Code, OpenClaw, and
Hermes-compatible discovery flows. The toolkit covers Markdown-to-WeChat
typesetting, generated image handoff, draft/material management, and explicit
publishing guardrails.

## Features

- Convert Markdown articles with front matter into WeChat-compatible inline-style HTML.
- Generate local browser previews and raw styled HTML fragments for publishing pipelines.
- Prepare cover and body illustration assets through OpenRouter or Codex image generation.
- Upload materials, replace body images, create drafts, inspect drafts, and query stats.
- Require exact confirmations before publishing or deleting WeChat content.
- Package the canonical skills as Codex, Claude Code, and OpenClaw plugin artifacts.
- Generate well-known skills indexes for Hermes-compatible clients.

## Repository Layout

This repository treats `skills/` as the canonical Agent Skills source:

| Path | Purpose |
| --- | --- |
| `skills/` | Source-of-truth skill folders with `SKILL.md`, scripts, references, and assets. |
| `plugins/holo-wechat-mp/` | Shared plugin wrapper for Codex, Claude Code, and OpenClaw. |
| `.agents/plugins/marketplace.json` | Codex local marketplace entry pointing to `./plugins/holo-wechat-mp`. |
| `src/holo_wechat_wpskills/` | Validation, plugin sync, example generation, and release artifact build tooling. |
| `examples/articles/` | Example article workflows for local dry-runs and documentation. |
| `registry/` | OpenClaw and Hermes publication notes plus well-known discovery templates. |
| `dist/` | Generated release artifacts, ignored by Git. |

Generated plugin skill copies under `plugins/holo-wechat-mp/skills/` are synced
from the canonical `skills/` directory and are not maintained by hand.

## Skill Catalog

| Skill | Purpose |
| --- | --- |
| `wechat-mp-typeset` | Convert Markdown articles into WeChat-compatible inline-style HTML and local previews. |
| `wechat-mp-manage` | Upload materials, replace body images, create drafts, inspect drafts, and safely publish/delete with explicit confirmation. |
| `wechat-mp-illustrate` | Generate or prepare article illustration assets. |
| `wechat-mp-publish` | Coordinate the end-to-end Markdown, illustration, draft, and publish workflow. |

## Quickstart

Clone the repository and install the development environment:

```bash
uv sync
```

Local package management and script invocation use `uv`; run project commands
with `uv run ...`.

Generate a WeChat-compatible HTML article from the default example without any
WeChat credentials:

```bash
uv run holo-wechat-example-draft
```

The command writes generated files under ignored `.tmp/examples/`, runs the same
local draft validation used by CI, and prints a dry-run JSON payload. It does not
call WeChat APIs.

## Try The Examples

Example articles live under `examples/articles/`:

| Example | Focus |
| --- | --- |
| `ci-quality-baseline` | CI, Ruff, pytest, and repository validation. |
| `wechat-draft-workflow` | Markdown to HTML to WeChat draft creation. |
| `agent-skills-packaging` | Single-source skill and plugin packaging. |

Generate HTML and preview files manually:

```bash
uv run python skills/wechat-mp-typeset/scripts/typeset.py \
  examples/articles/wechat-draft-workflow/article.md \
  --theme pier \
  --output .tmp/examples/wechat-draft-workflow/article.html \
  --preview .tmp/examples/wechat-draft-workflow/article.preview.html
```

Validate a generated HTML file without credentials:

```bash
uv run python skills/wechat-mp-manage/scripts/submit_html_draft.py \
  .tmp/examples/wechat-draft-workflow/article.html \
  --cover .tmp/examples/wechat-draft-workflow/cover.png \
  --dry-run
```

## Generate Article Images

`wechat-mp-illustrate` is a prompt-to-image helper. It does not analyze the whole
article or write prompts for you; the calling agent writes the final prompt and
then generates a local asset.

OpenRouter usage:

```bash
uv run python skills/wechat-mp-illustrate/scripts/illustrate.py \
  --prompt-file cover.prompt.txt \
  --output images/cover.png \
  --model "$OPENROUTER_IMAGE_MODEL"
```

The script reads `OPENROUTER_API_KEY` and optional `OPENROUTER_IMAGE_MODEL` from
the process environment, or accepts `--openrouter-api-key` / `--model` explicitly.
It does not load `.env` files. In Codex, the skill documentation also allows the
agent to use the built-in `gpt-image-2` image model and save the generated asset
directly, without an OpenRouter key.

## Credential Safety

CI never reads `.env`, never requires WeChat secrets, and never calls the WeChat
API. Local real-draft validation is opt-in:

```bash
uv run holo-wechat-example-draft --create-draft
```

Before creating a real draft, copy credentials into a local ignored `.env` file.
The command verifies that the credential file is ignored by Git, creates only a
draft, and prints only the draft `media_id`. It does not publish.

WeChat draft credentials use these environment variable names:

```text
WECHAT_MP_APPID=your_appid
WECHAT_MP_APPSECRET=your_appsecret
```

High-risk manage actions require exact confirmation:

```bash
uv run python skills/wechat-mp-manage/scripts/manage.py draft publish \
  --media-id MEDIA_ID \
  --confirm-media-id MEDIA_ID

uv run python skills/wechat-mp-manage/scripts/manage.py draft delete \
  --media-id MEDIA_ID \
  --confirm-media-id MEDIA_ID

uv run python skills/wechat-mp-manage/scripts/manage.py published delete \
  --article-id ARTICLE_ID \
  --confirm-article-id ARTICLE_ID
```

If the confirmation value is missing or different, the command exits before
sending the WeChat API request.

## Distribution

The latest packaged release is available at:

https://github.com/helebest/holo-wechat-mpskills/releases/tag/v0.2.0

Release artifacts include:

| Path | Contents |
| --- | --- |
| `dist/skills/*.zip` | Individual skill archives. |
| `dist/plugins/*-holo-wechat-mp-plugin.zip` | Claude, Codex, and OpenClaw plugin archives. |
| `dist/site/.well-known/skills/index.json` | Skills discovery index. |
| `dist/site/.well-known/agent-skills/index.json` | Agent Skills discovery index. |
| `dist/checksums.txt` | SHA-256 checksums for generated artifacts. |

Build artifacts locally:

```bash
uv run holo-wechat-build
```

`dist/` is ignored by Git. Release assets are generated, verified, and uploaded
separately.

For local plugin testing, generate the ignored plugin skill copy:

```bash
uv run holo-wechat-sync-plugin
```

Codex can discover the plugin through `.agents/plugins/marketplace.json`, which
points to `./plugins/holo-wechat-mp`. Claude Code can load the same wrapper with
`claude --plugin-dir ./plugins/holo-wechat-mp`. OpenClaw can either load the root
`skills/` directory directly or use the generated OpenClaw plugin archive. Hermes
Agent should continue to consume the root `skills/` directory, the generated
skill zips, or the well-known discovery index.

## Development

Run the same quality baseline used by GitHub Actions:

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run holo-wechat-validate
uv run holo-wechat-sync-plugin --check
uv run python -m pytest --basetemp .tmp/pytest -p no:cacheprovider
```

Validate repository structure only:

```bash
uv run holo-wechat-validate
```

The repository uses `uv` for development and testing. Deployable skills do not
include `pyproject.toml`; Python runtime dependencies are declared in each
skill's `scripts/requirements.txt`.

## Release Checklist

1. Update `pyproject.toml` and plugin manifest versions together.
2. Update `CHANGELOG.md`.
3. Run the local quality baseline.
4. Verify plugin sync with `uv run holo-wechat-sync-plugin --check`.
5. Build release artifacts with `uv run holo-wechat-build`.
6. Create and push a version tag, for example `v0.2.0`.
7. Create a GitHub Release and upload the generated zip files plus `checksums.txt`.

The build regression tests check that generated skill/plugin archives and
well-known indexes are produced from the canonical `skills/` directory.
