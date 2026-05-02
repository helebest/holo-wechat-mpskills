# WeChat MP Publishing Workflow

## Inputs

- Markdown article.
- Cover image.
- Optional style requirements for illustrations.
- WeChat credentials in environment variables or a local `.env` file.

## Sequence

1. Illustrate the article when requested:

   ```bash
   python <illustrate-skill>/scripts/illustrate.py article.md --output output --style "..."
   ```

2. Typeset the resulting Markdown:

   ```bash
   python <typeset-skill>/scripts/typeset.py output/article_illustrated.md --output article.html --preview article.preview.html
   ```

3. Validate draft inputs:

   ```bash
   python <manage-skill>/scripts/submit_html_draft.py article.html --cover cover.png --dry-run
   ```

4. Create the draft:

   ```bash
   python <manage-skill>/scripts/submit_html_draft.py article.html --cover cover.png --title "标题"
   ```

5. Report the returned `media_id` and ask for explicit confirmation before publishing.

## Handoff Artifacts

- Illustrated Markdown path.
- HTML path.
- Preview HTML path.
- Cover image path.
- WeChat draft `media_id`.

## Safety Gates

- Confirm before publish.
- Confirm before delete.
- Confirm before replacing an existing draft.
- Never print secrets or token cache contents.
