from __future__ import annotations

import re
import sys

from holo_wechat_wpskills.validate import ROOT


TYPESET_SCRIPTS = ROOT / "skills/wechat-mp-typeset/scripts"


def load_typeset_modules():
    if str(TYPESET_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(TYPESET_SCRIPTS))
    from markdown_converter import MarkdownConverter
    from style_engine import ThemeEngine

    return MarkdownConverter, ThemeEngine


def render_sample(theme: str = "pier") -> str:
    MarkdownConverter, ThemeEngine = load_typeset_modules()
    markdown = """![Architecture overview](images/architecture.png)

| 阶段 | 主要风险 | 处理方式 |
|------|----------|----------|
| 生成 | very-long-unbroken-token-for-mobile-layout-regression | 保留换行 |

```python
payload = {"title": "长代码行应该在移动端保持可读，而不是撑开整个正文容器"}
```

Inline `code` should stay compact.
"""
    raw_html = MarkdownConverter().to_html(markdown)
    return ThemeEngine(theme_name=theme).apply_styles(raw_html)


def test_image_only_paragraphs_become_captioned_figures() -> None:
    html = render_sample()

    assert "<figure" in html
    assert "<figcaption" in html
    assert "Architecture overview" in html
    assert not re.search(r"<p[^>]*>\s*<img", html)


def test_tables_and_code_blocks_are_mobile_resilient() -> None:
    html = render_sample()

    assert "<thead" not in html
    assert "<tbody" not in html
    assert "overflow-x: auto" in html
    assert "table-layout: fixed" in html
    assert "word-break: break-word" in html
    assert "white-space: pre-wrap" in html
