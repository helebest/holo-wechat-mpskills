"""
主题加载器

从 JSON 文件加载主题配置，解析变量引用
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional


class ThemeLoader:
    """主题加载器：从 JSON 文件加载并解析主题"""

    # 变量引用模式：{category.key}
    VAR_PATTERN = re.compile(r"\{(\w+)\.(\w+)\}")

    def __init__(self, theme_path: Optional[str] = None, theme_name: str = "minimal"):
        """
        初始化主题加载器

        Args:
            theme_path: 主题文件的直接路径（优先级最高）
            theme_name: 主题名称，将从 themes/ 目录查找
        """
        self.theme_data = self._load_theme(theme_path, theme_name)
        self._build_lookup()
        self._resolve_all_references()

    def _load_theme(self, theme_path: Optional[str], theme_name: str) -> Dict[str, Any]:
        """加载主题 JSON 文件"""
        if theme_path:
            path = Path(theme_path)
        else:
            # Load bundled themes from the skill assets directory.
            skill_dir = Path(__file__).parent.parent
            path = skill_dir / "assets" / "themes" / f"{theme_name}.json"

        if not path.exists():
            raise FileNotFoundError(f"主题文件不存在: {path}")

        return json.loads(path.read_text(encoding="utf-8"))

    def _build_lookup(self):
        """构建变量查找表"""
        self._lookup = {
            "colors": self.theme_data.get("colors", {}),
            "fonts": self.theme_data.get("fonts", {}),
            "tokens": self.theme_data.get("tokens", {}),
        }

    def _substitute(self, value: str) -> str:
        """替换字符串中的变量引用"""
        if not isinstance(value, str):
            return value

        def replacer(match):
            category, key = match.groups()
            table = self._lookup.get(category, {})
            return table.get(key, match.group(0))

        # 多次替换，处理嵌套引用
        result = value
        for _ in range(3):  # 最多 3 层嵌套
            new_result = self.VAR_PATTERN.sub(replacer, result)
            if new_result == result:
                break
            result = new_result

        return result

    def _resolve_all_references(self):
        """解析所有变量引用"""
        # 解析 elements
        elements = self.theme_data.get("elements", {})
        for tag, styles in elements.items():
            if isinstance(styles, dict):
                for prop, value in styles.items():
                    if isinstance(value, str):
                        styles[prop] = self._substitute(value)

        # 解析 decorations
        decorations = self.theme_data.get("decorations", {})
        for name, config in decorations.items():
            if config and isinstance(config, dict):
                style = config.get("style", {})
                if isinstance(style, dict):
                    for prop, value in style.items():
                        if isinstance(value, str):
                            style[prop] = self._substitute(value)

    @property
    def name(self) -> str:
        """主题名称"""
        return self.theme_data.get("name", "unknown")

    @property
    def colors(self) -> Dict[str, str]:
        """颜色定义"""
        return self.theme_data.get("colors", {})

    @property
    def fonts(self) -> Dict[str, str]:
        """字体定义"""
        return self.theme_data.get("fonts", {})

    @property
    def tokens(self) -> Dict[str, str]:
        """设计令牌"""
        return self.theme_data.get("tokens", {})

    @property
    def elements(self) -> Dict[str, Dict[str, str]]:
        """元素样式"""
        return self.theme_data.get("elements", {})

    @property
    def decorations(self) -> Dict[str, Any]:
        """装饰配置"""
        return self.theme_data.get("decorations", {})

    def get_element_style(self, tag: str) -> str:
        """
        获取元素的内联样式字符串

        Args:
            tag: HTML 标签名

        Returns:
            内联样式字符串，如 "color: #333; font-size: 16px;"
        """
        styles = self.elements.get(tag, {})
        if not styles:
            return ""

        return " ".join(f"{k}: {v};" for k, v in styles.items())

    def get_decoration(self, name: str) -> Optional[Dict[str, Any]]:
        """获取装饰配置"""
        return self.decorations.get(name)
