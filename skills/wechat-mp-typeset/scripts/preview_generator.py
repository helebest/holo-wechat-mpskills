"""
本地预览生成器

生成可在浏览器中直接打开的 HTML 预览文件
"""
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote

try:
    from .markdown_converter import MarkdownConverter, ParsedArticle
    from .style_engine import ThemeEngine
except ImportError:
    from markdown_converter import MarkdownConverter, ParsedArticle
    from style_engine import ThemeEngine


class PreviewGenerator:
    """预览生成器：生成本地可预览的 HTML 文件"""

    def __init__(
        self,
        theme_path: str = None,
        theme_name: str = "minimal"
    ):
        """
        初始化预览生成器

        Args:
            theme_path: 主题文件路径
            theme_name: 主题名称
        """
        self.converter = MarkdownConverter()
        self.engine = ThemeEngine(theme_path, theme_name)

    def _to_file_url(self, path: str) -> str:
        """
        将本地路径转换为 file:// URL

        Args:
            path: 本地文件路径

        Returns:
            file:// URL
        """
        abs_path = Path(path).resolve()

        # Windows 路径处理
        path_str = str(abs_path).replace('\\', '/')
        if abs_path.drive:
            # Windows: file:///C:/path/to/file
            return f"file:///{quote(path_str, safe='/:')}"
        else:
            # Unix: file:///path/to/file
            return f"file://{quote(path_str, safe='/')}"

    def _replace_image_paths(self, html: str, images: List[str]) -> str:
        """
        替换 HTML 中的图片路径为 file:// URL

        Args:
            html: HTML 内容
            images: 图片绝对路径列表

        Returns:
            替换后的 HTML
        """
        result = html

        # 构建文件名到 file:// URL 的映射
        url_mapping: Dict[str, str] = {}
        for img_path in images:
            if img_path.startswith(('http://', 'https://')):
                continue
            filename = Path(img_path).name
            url_mapping[filename] = self._to_file_url(img_path)

        # 替换 src 属性中的图片路径
        def replace_src(match):
            src = match.group(1)
            # 提取文件名
            filename = Path(src).name
            if filename in url_mapping:
                return f'src="{url_mapping[filename]}"'
            return match.group(0)

        result = re.sub(r'src="([^"]+)"', replace_src, result)

        return result

    def _wrap_html(self, content: str, title: str = "Preview") -> str:
        """
        包装为完整的 HTML 文档

        Args:
            content: HTML 内容
            title: 页面标题

        Returns:
            完整的 HTML 文档
        """
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        /* 模拟微信公众号文章容器 */
        .article-container {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
    </style>
</head>
<body>
    <div class="article-container">
{content}
    </div>
</body>
</html>'''

    def generate(self, md_path: str) -> str:
        """
        从 Markdown 生成预览 HTML

        Args:
            md_path: Markdown 文件路径

        Returns:
            完整的 HTML 文档
        """
        # 解析 Markdown
        parsed = self.converter.parse(md_path)

        # 应用样式
        styled_html = self.engine.apply_styles(parsed.raw_html)

        # 替换图片路径为 file:// URL
        styled_html = self._replace_image_paths(styled_html, parsed.images)

        # 包装为完整 HTML
        return self._wrap_html(styled_html, parsed.meta.title)

    def save(
        self,
        md_path: str,
        output_path: str = None
    ) -> str:
        """
        生成预览 HTML 并保存到文件

        Args:
            md_path: Markdown 文件路径
            output_path: 输出文件路径（可选，默认为 .preview.html）

        Returns:
            输出文件的绝对路径
        """
        html = self.generate(md_path)

        if output_path is None:
            output_path = Path(md_path).with_suffix('.preview.html')

        output_path = Path(output_path)
        output_path.write_text(html, encoding='utf-8')

        return str(output_path.resolve())
