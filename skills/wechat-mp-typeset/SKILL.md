---
name: wechat-mp-typeset
description: Convert Markdown articles into WeChat Official Account compatible HTML with inline styles, front matter metadata, themes, and local preview output. Use when preparing Markdown, md, HTML, preview, typesetting, styling, or layout for WeChat MP / 微信公众号 articles.
---

# WeChat MP Typeset

Use this skill to turn Markdown articles into WeChat Official Account compatible HTML.

## Workflow

1. Inspect the Markdown front matter for `title`, `cover`, `author`, `summary`, `category`, and `keywords`.
2. Install Python dependencies when needed:

   ```bash
   python -m pip install -r <skill-dir>/scripts/requirements.txt
   ```

3. Generate HTML and an optional browser preview:

   ```bash
   python <skill-dir>/scripts/typeset.py article.md --output article.html --preview article.preview.html --theme minimal
   ```

4. Use `--raw` when another workflow needs only the styled HTML fragment.
5. Use `--list-themes` to see bundled themes. Theme details are in `references/theme-format.md`.

## Notes

- Theme JSON files live in `assets/themes/`.
- Preview output rewrites local image references to `file://` URLs for browser inspection.
- For publishing to WeChat, pass the generated HTML to `wechat-mp-manage`; local image URLs must be uploaded and replaced before draft creation.
