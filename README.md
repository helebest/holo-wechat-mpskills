# holo-wechat-mpskills

Agent Skills for producing WeChat Official Account articles: typesetting Markdown,
creating publication-ready images, managing WeChat drafts/materials, and keeping
publishing actions explicit and auditable.

This repository treats `skills/` as the canonical source. Build outputs, plugin
archives, and discovery indexes are generated from that source instead of being
maintained by hand.

## What Are These Skills?

Skills are self-contained folders of instructions, scripts, references, and assets
that an agent can load when a task needs specialized behavior. In this repo, each
skill focuses on one part of the WeChat Official Account workflow and can be used
independently or as a pipeline.

| Skill | Purpose |
| --- | --- |
| `wechat-mp-typeset` | Convert Markdown articles into WeChat-compatible inline-style HTML and local previews. |
| `wechat-mp-manage` | Upload materials, replace body images, create drafts, inspect drafts, and safely publish/delete with explicit confirmation. |
| `wechat-mp-illustrate` | Generate or prepare article illustration assets. |
| `wechat-mp-publish` | Provide publishing workflow guidance and operator-facing guardrails. |

## Quickstart

Clone the repository and install the development environment:

```bash
uv sync
```

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
| `dist/plugins/*-wechat-mp-plugin.zip` | Claude, Codex, and OpenClaw plugin archives. |
| `dist/site/.well-known/skills/index.json` | Skills discovery index. |
| `dist/site/.well-known/agent-skills/index.json` | Agent Skills discovery index. |
| `dist/checksums.txt` | SHA-256 checksums for generated artifacts. |

Build artifacts locally:

```bash
uv run holo-wechat-build
```

`dist/` is ignored by Git. Release assets are generated, verified, and uploaded
separately.

## Development

Run the same quality baseline used by GitHub Actions:

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run holo-wechat-validate
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
4. Build release artifacts with `uv run holo-wechat-build`.
5. Create and push a version tag, for example `v0.2.0`.
6. Create a GitHub Release and upload the generated zip files plus `checksums.txt`.

The build regression tests check that generated skill/plugin archives and
well-known indexes are produced from the canonical `skills/` directory.
