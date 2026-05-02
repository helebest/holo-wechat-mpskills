"""
微信公众号样式引擎

使用外部 JSON 主题文件，将样式应用到 HTML
"""

import re
from html import escape, unescape
from typing import Optional

try:
    from .theme_loader import ThemeLoader
except ImportError:
    from theme_loader import ThemeLoader


class ThemeEngine:
    """主题引擎：将主题样式应用到 HTML"""

    def __init__(self, theme_path: Optional[str] = None, theme_name: str = "minimal"):
        """
        初始化主题引擎

        Args:
            theme_path: 主题文件的直接路径
            theme_name: 主题名称（默认 minimal）
        """
        self.loader = ThemeLoader(theme_path, theme_name)

    def get_style(self, tag: str) -> str:
        """获取标签的内联样式"""
        return self.loader.get_element_style(tag)

    def _promote_image_paragraphs(self, html: str) -> str:
        """Convert image-only paragraphs into styled figures with optional captions."""

        def promote(match):
            img_tag = match.group(1)
            alt_match = re.search(r"""alt=(["'])(.*?)\1""", img_tag, flags=re.IGNORECASE)
            caption = ""
            if alt_match and alt_match.group(2).strip():
                caption_text = escape(unescape(alt_match.group(2).strip()))
                caption = f"<figcaption>{caption_text}</figcaption>"
            return f"<figure>{img_tag}{caption}</figure>"

        return re.sub(
            r"<p>\s*(<img\b[^>]*>)\s*</p>",
            promote,
            html,
            flags=re.IGNORECASE,
        )

    def _wrap_tables(self, html: str) -> str:
        """Wrap tables in a lightweight scroll container for narrow screens."""
        table_container_style = self.get_style("table_container")
        if not table_container_style:
            return html

        def wrap(match):
            return f'<section style="{table_container_style}">{match.group(0)}</section>'

        return re.sub(r"<table\b[^>]*>.*?</table>", wrap, html, flags=re.DOTALL | re.IGNORECASE)

    def apply_styles(self, html: str) -> str:
        """
        为 HTML 添加内联样式

        Args:
            html: 原始 HTML

        Returns:
            添加样式后的 HTML
        """
        styled_html = self._promote_image_paragraphs(html)

        # 标签与样式的映射关系
        tag_mappings = [
            ("h1", "h1"),
            ("h2", "h2"),
            ("h3", "h3"),
            ("h4", "h4"),
            ("h5", "h4"),
            ("h6", "h4"),
            ("p", "p"),
            ("blockquote", "blockquote"),
            ("strong", "strong"),
            ("b", "strong"),
            ("em", "em"),
            ("i", "em"),
            ("a", "a"),
            ("ul", "ul"),
            ("ol", "ol"),
            ("img", "img"),
            ("hr", "hr"),
            ("table", "table"),
            ("th", "th"),
            ("td", "td"),
            ("figure", "figure"),
            ("figcaption", "figcaption"),
        ]

        for html_tag, style_key in tag_mappings:
            style = self.get_style(style_key)
            if style:
                pattern = rf"<{html_tag}(\s+[^>]*)?>"

                def add_style(match, s=style, tag=html_tag):
                    attrs = match.group(1) or ""
                    if "style=" in attrs:
                        new_attrs = re.sub(r'style="([^"]*)"', f'style="{s} \\1"', attrs)
                        return f"<{tag}{new_attrs}>"
                    else:
                        return f'<{tag} style="{s}"{attrs}>'

                styled_html = re.sub(pattern, add_style, styled_html, flags=re.IGNORECASE)

        # 处理 H3 的装饰元素
        h3_decoration = self.loader.get_decoration("h3_prefix")
        if h3_decoration:
            symbol = h3_decoration.get("symbol", "")
            prefix_style = h3_decoration.get("style", {})
            prefix_style_str = " ".join(f"{k}: {v};" for k, v in prefix_style.items())
            h3_prefix = f'<span style="{prefix_style_str}">{symbol}</span>'
            styled_html = re.sub(
                r"(<h3[^>]*>)", rf"\1{h3_prefix}", styled_html, flags=re.IGNORECASE
            )

        # 处理无序列表项
        li_style = self.get_style("li")

        def style_ul_li(match):
            content = match.group(1)
            content = re.sub(r"<p[^>]*>", '<p style="display: inline; margin: 0;">', content)
            return f'<li style="{li_style}">{content}</li>'

        def process_ul(match):
            ul_content = match.group(1)
            ul_content = ul_content.strip()
            ul_content = re.sub(r">\s+<", "><", ul_content)
            ul_style = self.get_style("ul")
            styled_ul = re.sub(
                r"<li[^>]*>(.*?)</li>", style_ul_li, ul_content, flags=re.DOTALL | re.IGNORECASE
            )
            return f'<ul style="{ul_style}">{styled_ul}</ul>'

        styled_html = re.sub(
            r"<ul[^>]*>(.*?)</ul>", process_ul, styled_html, flags=re.DOTALL | re.IGNORECASE
        )

        # 处理有序列表项
        ol_li_style = self.get_style("ol_li") or li_style

        def process_ol(match):
            ol_content = match.group(1)
            ol_content = ol_content.strip()
            ol_content = re.sub(r">\s+<", "><", ol_content)
            ol_style = self.get_style("ol")

            def style_ol_li(m):
                content = m.group(1)
                content = re.sub(r"<p[^>]*>", '<p style="display: inline; margin: 0;">', content)
                return f'<li style="{ol_li_style}">{content}</li>'

            styled_ol = re.sub(
                r"<li[^>]*>(.*?)</li>", style_ol_li, ol_content, flags=re.DOTALL | re.IGNORECASE
            )
            return f'<ol style="{ol_style}">{styled_ol}</ol>'

        styled_html = re.sub(
            r"<ol[^>]*>(.*?)</ol>", process_ol, styled_html, flags=re.DOTALL | re.IGNORECASE
        )

        # 处理代码块
        pre_style = self.get_style("pre")
        pre_code_style = self.get_style("pre_code")
        line_number_style = self.get_style("code_line_number")

        def style_pre(match):
            content = match.group(1)
            code_match = re.search(r"<code[^>]*>(.*?)</code>", content, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
                lines = code_content.split("\n")
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                styled_lines = []
                for i, line in enumerate(lines, 1):
                    line = line.replace(" ", "&nbsp;")
                    line_num = f'<span style="{line_number_style}">{i}</span>'
                    styled_lines.append(f"{line_num}{line}")
                content = f'<code style="{pre_code_style}">' + "<br>".join(styled_lines) + "</code>"
            return f'<pre style="{pre_style}">{content}</pre>'

        styled_html = re.sub(
            r"<pre[^>]*>(.+?)</pre>", style_pre, styled_html, flags=re.DOTALL | re.IGNORECASE
        )

        # 处理行内 code
        code_style = self.get_style("code")

        def style_inline_code(html_content):
            pre_blocks = []

            def save_pre(match):
                pre_blocks.append(match.group(0))
                return f"___PRE_BLOCK_{len(pre_blocks) - 1}___"

            html_content = re.sub(r"<pre.*?>.*?</pre>", save_pre, html_content, flags=re.DOTALL)

            html_content = re.sub(
                r"<code(?![^>]*style=)([^>]*)>([^<]+)</code>",
                f'<code style="{code_style}"\\1>\\2</code>',
                html_content,
                flags=re.IGNORECASE,
            )

            for i, block in enumerate(pre_blocks):
                html_content = html_content.replace(f"___PRE_BLOCK_{i}___", block)

            return html_content

        styled_html = style_inline_code(styled_html)

        # 处理 blockquote 内的段落
        blockquote_p_style = self.get_style("blockquote_p")
        if blockquote_p_style:

            def style_blockquote_p(match):
                bq_content = match.group(0)
                bq_content = re.sub(
                    r'<p style="[^"]*">', f'<p style="{blockquote_p_style}">', bq_content
                )
                return bq_content

            styled_html = re.sub(
                r"<blockquote[^>]*>.*?</blockquote>",
                style_blockquote_p,
                styled_html,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # 移除 thead 和 tbody 标签（微信不支持）
        styled_html = re.sub(r"</?thead>", "", styled_html, flags=re.IGNORECASE)
        styled_html = re.sub(r"</?tbody>", "", styled_html, flags=re.IGNORECASE)
        styled_html = self._wrap_tables(styled_html)

        # 包装整体
        section_style = self.get_style("section")
        styled_html = f'<div style="{section_style}">{styled_html}</div>'

        return styled_html
