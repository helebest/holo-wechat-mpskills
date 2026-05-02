---
name: wechat-mp-manage
description: Manage WeChat Official Account materials, article images, drafts, publish status, and stats through WeChat MP APIs. Use when uploading images, creating or updating drafts, publishing or checking publish status, querying materials, or analyzing 微信公众号 data.
---

# WeChat MP Manage

Use this skill for WeChat Official Account API operations after content has been prepared.

## Setup

Install dependencies when needed:

```bash
python -m pip install -r <skill-dir>/scripts/requirements.txt
```

Provide credentials through environment variables or a project `.env` file:

```text
WECHAT_APPID=your_appid
WECHAT_APPSECRET=your_appsecret
```

The client searches for `.env` from the current working directory upward.

## Common Workflows

- Validate an HTML draft without calling WeChat:

  ```bash
  python <skill-dir>/scripts/submit_html_draft.py article.html --cover cover.png --dry-run
  ```

- Submit a prepared HTML file to the draft box:

  ```bash
  python <skill-dir>/scripts/submit_html_draft.py article.html --cover cover.png --title "标题" --author "作者"
  ```

- Use `scripts/material_manager.py` to upload permanent materials or article body images.
- Use `scripts/draft_manager.py` to create, list, update, delete, publish, and query drafts.
- Use `scripts/stats_manager.py` for user, article, message, and interface statistics.

## References

- `references/article_format.md` for article payload and HTML constraints.
- `references/api_reference.md` for WeChat API endpoint notes.
- `references/stats_reference.md` for data query ranges.
- `references/error_codes.md` for common API errors.

## Safety

Creating drafts is allowed when credentials are configured. Publishing a draft or deleting materials/articles should require explicit user confirmation.
