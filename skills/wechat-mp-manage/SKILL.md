---
name: wechat-mp-manage
description: Manage WeChat Official Account materials, article images, drafts, publish status, and stats through WeChat MP APIs. Use when uploading images, creating or updating drafts, publishing or checking publish status, querying materials, or analyzing 微信公众号 data.
---

# WeChat MP Manage

Use this skill for WeChat Official Account API operations after content has been prepared.

## Setup

Use `uv` for local dependency and script execution. From this repository, install
the locked development environment once:

```bash
uv sync
```

Provide credentials through process environment variables:

```text
WECHAT_MP_APPID=your_appid
WECHAT_MP_APPSECRET=your_appsecret
```

The manage skill does not load `.env` files by itself. Load local credential files
before invoking scripts if your workflow uses them.

## Common Workflows

- Validate an HTML draft without calling WeChat:

  ```bash
  uv run python <skill-dir>/scripts/submit_html_draft.py article.html --cover cover.png --dry-run
  ```

- Submit a prepared HTML file to the draft box:

  ```bash
  uv run python <skill-dir>/scripts/submit_html_draft.py article.html --cover cover.png --title "标题" --author "作者"
  ```

- List or inspect drafts without publishing:

  ```bash
  uv run python <skill-dir>/scripts/manage.py draft list --no-content
  uv run python <skill-dir>/scripts/manage.py draft get --media-id MEDIA_ID
  ```

- Delete or publish only with an exact confirmation value:

  ```bash
  uv run python <skill-dir>/scripts/manage.py draft delete --media-id MEDIA_ID --confirm-media-id MEDIA_ID
  uv run python <skill-dir>/scripts/manage.py draft publish --media-id MEDIA_ID --confirm-media-id MEDIA_ID
  ```

- List or delete published articles:

  ```bash
  uv run python <skill-dir>/scripts/manage.py published list --no-content
  uv run python <skill-dir>/scripts/manage.py published delete --article-id ARTICLE_ID --confirm-article-id ARTICLE_ID
  ```

- Use `scripts/material_manager.py` to upload permanent materials or article body images.
- Use `scripts/draft_manager.py` directly when custom Python integration is needed.
- Use `scripts/stats_manager.py` for user, article, message, and interface statistics.

## API Behavior

- `WeChatClient` preserves WeChat `errcode` and `errmsg` in `WeChatAPIError`.
- Expired access-token errors (`40001`, `40014`, `42001`) are retried once after refreshing the token.
- Tests can inject a fake HTTP session through `WeChatClient(session=...)`; normal use does not need this parameter.
- `submit_html_draft` performs local file, title, author, digest, and image checks before uploading anything.

## References

- `references/article_format.md` for article payload and HTML constraints.
- `references/api_reference.md` for WeChat API endpoint notes.
- `references/stats_reference.md` for data query ranges.
- `references/error_codes.md` for common API errors.

## Safety

Creating drafts is allowed when credentials are configured. Publishing or deleting content requires exact confirmation through both Python and CLI interfaces:

```python
dm.publish_draft(media_id, confirm_media_id=media_id)
dm.delete_draft(media_id, confirm_media_id=media_id)
dm.delete_published(article_id, confirm_article_id=article_id)
```

```bash
uv run python <skill-dir>/scripts/manage.py draft publish --media-id MEDIA_ID --confirm-media-id MEDIA_ID
uv run python <skill-dir>/scripts/manage.py draft delete --media-id MEDIA_ID --confirm-media-id MEDIA_ID
uv run python <skill-dir>/scripts/manage.py published delete --article-id ARTICLE_ID --confirm-article-id ARTICLE_ID
```

If the confirmation value is omitted or differs from the target ID, the command exits before sending the WeChat API request.
