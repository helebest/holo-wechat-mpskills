---
name: wechat-mp-publish
description: Orchestrate the complete WeChat Official Account publishing workflow from Markdown to illustrations, typeset HTML, draft creation, and optional publish confirmation. Use when the user wants an end-to-end 微信公众号 publish, draft, or release workflow.
---

# WeChat MP Publish

Use this skill to coordinate the other WeChat MP skills without duplicating their scripts.

## Workflow

1. If illustrations are needed, use `wechat-mp-illustrate` to generate an illustrated Markdown file.
2. Use `wechat-mp-typeset` to create WeChat-compatible HTML and preview it.
3. Use `wechat-mp-manage --dry-run` behavior to validate the HTML, cover image, title, digest, and local images.
4. Create a WeChat draft with `wechat-mp-manage`.
5. Stop and report the draft `media_id`.
6. Publish only after the user explicitly confirms the exact draft to publish.

## Constraints

- Do not publish, delete, or overwrite WeChat content without explicit confirmation.
- Do not expose `WECHAT_MP_APPSECRET`, `OPENROUTER_API_KEY`, access tokens, or token cache contents.
- Prefer draft creation and preview checks over direct publishing.
- Read `references/workflow.md` for the detailed sequence and handoff artifacts.
