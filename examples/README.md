# Examples

This directory contains realistic WeChat Official Account article examples used by
the repository test suite.

Each example lives under `examples/articles/<slug>/` and contains:

- `article.md`: source Markdown with front matter.
- `cover.png`: local cover image for draft validation.
- `images/`: local body images referenced by the article.
- `README.md`: short notes for the example.

## Preview Without Credentials

Generate WeChat-compatible HTML, a local preview, and a dry-run payload:

```powershell
uv run holo-wechat-example-draft
```

The command copies the default example into `.tmp/examples/wechat-draft-workflow/`, writes
`article.html` and `article.preview.html`, then validates the draft payload without calling
WeChat APIs.

The equivalent manual flow is:

```powershell
New-Item -ItemType Directory -Force .tmp/examples | Out-Null
Copy-Item -Recurse -Force examples/articles/wechat-draft-workflow .tmp/examples/
uv run python skills/wechat-mp-typeset/scripts/typeset.py `
  .tmp/examples/wechat-draft-workflow/article.md `
  --theme pier `
  --output .tmp/examples/wechat-draft-workflow/article.html `
  --preview .tmp/examples/wechat-draft-workflow/article.preview.html
```

Validate the generated draft payload without calling WeChat:

```powershell
uv run python skills/wechat-mp-manage/scripts/submit_html_draft.py `
  .tmp/examples/wechat-draft-workflow/article.html `
  --cover .tmp/examples/wechat-draft-workflow/cover.png `
  --title "把 Markdown 稳定送进公众号草稿箱" `
  --author "holo" `
  --digest "从排版、图片上传到草稿创建，梳理一条可回归的公众号交付链路。" `
  --dry-run
```

## Local Credential Validation

Credential validation is local-only and must not run in CI. Copy credentials from
the sibling project when you need to create a real WeChat draft:

```powershell
Copy-Item -LiteralPath "C:\Users\HE LE\Project\holotalks\.env" -Destination .env -Force
git status --ignored --short
```

Confirm `.env` appears as ignored before continuing.

Then create a test draft with the guarded helper:

```powershell
uv run holo-wechat-example-draft --create-draft
```

On success, stdout contains only the created draft `media_id`. The command does not publish.

The lower-level equivalent is:

```powershell
uv run python skills/wechat-mp-manage/scripts/submit_html_draft.py `
  .tmp/examples/wechat-draft-workflow/article.html `
  --cover .tmp/examples/wechat-draft-workflow/cover.png `
  --title "把 Markdown 稳定送进公众号草稿箱" `
  --author "holo" `
  --digest "从排版、图片上传到草稿创建，梳理一条可回归的公众号交付链路。"
```

The command prints a `media_id` for the created draft. Do not publish from this
workflow.

If WeChat returns `40164 invalid ip`, add the current machine's public egress IP
to the Official Account API whitelist, then rerun the draft creation command.
