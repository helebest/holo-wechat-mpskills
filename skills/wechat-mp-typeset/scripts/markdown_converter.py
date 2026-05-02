"""
Markdown 到 HTML 转换器

解析 Markdown 文件，提取 Front Matter 元数据，转换为 HTML
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

import yaml
import markdown


@dataclass
class ArticleMeta:
    """文章元数据"""
    title: str
    date: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    cover: Optional[str] = None
    author: Optional[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class ParsedArticle:
    """解析后的文章"""
    meta: ArticleMeta
    raw_html: str
    images: List[str]  # 正文中引用的图片路径列表


class MarkdownConverter:
    """Markdown 转换器"""

    # Front Matter 分隔符正则
    FRONT_MATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL
    )

    # Markdown 图片语法正则
    IMAGE_PATTERN = re.compile(
        r'!\[([^\]]*)\]\(([^)]+)\)'
    )

    def __init__(self, md_extensions: List[str] = None):
        """
        初始化转换器

        Args:
            md_extensions: Markdown 扩展列表
        """
        self.extensions = md_extensions or [
            'tables',
            'fenced_code',
            'nl2br',
            'sane_lists',
        ]
        self.md = markdown.Markdown(extensions=self.extensions)

    def parse_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        解析 Front Matter

        Args:
            content: 完整的 Markdown 内容

        Returns:
            (front_matter_dict, body_content)
        """
        match = self.FRONT_MATTER_PATTERN.match(content)
        if match:
            yaml_str = match.group(1)
            body = content[match.end():]
            try:
                front_matter = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError:
                front_matter = {}
            return front_matter, body
        return {}, content

    def extract_images(self, md_content: str) -> List[str]:
        """
        提取 Markdown 中的图片路径

        Args:
            md_content: Markdown 正文内容

        Returns:
            图片路径列表
        """
        return [match[1] for match in self.IMAGE_PATTERN.findall(md_content)]

    def replace_images(
        self,
        md_content: str,
        url_mapping: Dict[str, str]
    ) -> str:
        """
        替换图片路径为新 URL

        Args:
            md_content: Markdown 内容
            url_mapping: {原始路径: 新URL} 映射

        Returns:
            替换后的 Markdown 内容
        """
        def replacer(match):
            alt_text = match.group(1)
            original_path = match.group(2)
            new_url = url_mapping.get(original_path, original_path)
            return f'![{alt_text}]({new_url})'

        return self.IMAGE_PATTERN.sub(replacer, md_content)

    def _preprocess_lists(self, md_content: str) -> str:
        """
        预处理 Markdown 中的列表：确保列表前有空行

        标准 Markdown 要求列表前有空行才能正确解析。
        此方法自动在有序/无序列表标记前添加空行（如果缺失）。

        Args:
            md_content: Markdown 内容

        Returns:
            预处理后的 Markdown 内容
        """
        lines = md_content.split('\n')
        result = []

        for i, line in enumerate(lines):
            # 检查是否是列表项开头（有序或无序）
            is_list_item = (
                re.match(r'^\d+\.\s', line) or  # 有序列表: "1. xxx"
                re.match(r'^[-*+]\s', line)      # 无序列表: "- xxx" 或 "* xxx"
            )

            if is_list_item and i > 0:
                prev_line = lines[i - 1].strip()
                # 如果前一行不是空行、不是列表项、不是引用，则添加空行
                if prev_line and not re.match(r'^(\d+\.|-|\*|\+|>)\s', prev_line):
                    result.append('')

            result.append(line)

        return '\n'.join(result)

    def to_html(self, md_content: str) -> str:
        """
        将 Markdown 转换为 HTML

        Args:
            md_content: Markdown 内容

        Returns:
            HTML 字符串
        """
        self.md.reset()
        # 预处理：确保列表前有空行
        preprocessed = self._preprocess_lists(md_content)
        return self.md.convert(preprocessed)

    def parse(self, md_path: str) -> ParsedArticle:
        """
        解析 Markdown 文件

        Args:
            md_path: Markdown 文件路径

        Returns:
            ParsedArticle 对象
        """
        path = Path(md_path)
        content = path.read_text(encoding='utf-8')

        # 解析 Front Matter
        front_matter, body = self.parse_front_matter(content)

        # 提取图片
        images = self.extract_images(body)

        # 解析图片的绝对路径（相对于 md 文件目录）
        base_dir = path.parent
        absolute_images = []
        for img in images:
            if not img.startswith(('http://', 'https://')):
                img_path = (base_dir / img).resolve()
                absolute_images.append(str(img_path))
            else:
                absolute_images.append(img)

        # 转换为 HTML
        raw_html = self.to_html(body)

        # 构建元数据
        meta = ArticleMeta(
            title=front_matter.get('title', path.stem),
            date=str(front_matter.get('date')) if front_matter.get('date') else None,
            category=front_matter.get('category'),
            keywords=front_matter.get('keywords', []),
            summary=front_matter.get('summary'),
            cover=front_matter.get('cover'),
            author=front_matter.get('author'),
        )

        # 处理封面图的绝对路径
        if meta.cover and not meta.cover.startswith(('http://', 'https://')):
            meta.cover = str((base_dir / meta.cover).resolve())

        return ParsedArticle(
            meta=meta,
            raw_html=raw_html,
            images=absolute_images
        )
