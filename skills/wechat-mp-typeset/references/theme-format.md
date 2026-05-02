# 主题格式说明

## 文件结构

每个主题是一个 JSON 文件，包含以下部分：

```json
{
  "name": "主题名称",
  "version": "1.0.0",
  "description": "主题描述",

  "colors": { ... },      // 颜色定义
  "fonts": { ... },       // 字体定义
  "tokens": { ... },      // 设计令牌（圆角、阴影等）
  "elements": { ... },    // 各 HTML 元素的样式
  "decorations": { ... }  // 装饰性元素（如 h3 前缀）
}
```

## 变量引用

在 `elements` 中可以引用 `colors`、`fonts`、`tokens` 中定义的变量：

```json
{
  "colors": {
    "primary": "#26a69a"
  },
  "elements": {
    "h1": {
      "border-bottom": "3px solid {colors.primary}"
    }
  }
}
```

## 支持的元素

| 元素 | 说明 |
|------|------|
| `section` | 整体容器 |
| `h1` - `h4` | 标题 |
| `p` | 段落 |
| `strong`, `em` | 加粗、斜体 |
| `a` | 链接 |
| `blockquote`, `blockquote_p` | 引用及其内部段落 |
| `ul`, `ol`, `li` | 列表 |
| `li_bullet`, `ol_number` | 列表标记样式 |
| `code`, `pre`, `pre_code` | 代码 |
| `code_line_number` | 代码行号 |
| `img`, `figure`, `figcaption` | 图片 |
| `hr` | 分割线 |
| `table_container`, `table`, `th`, `td` | 表格外层滚动容器和单元格 |

## 创建新主题

1. 复制 `assets/themes/minimal.json` 作为基础
2. 修改 `name` 和 `description`
3. 调整 `colors` 中的颜色值
4. 根据需要调整 `elements` 中的样式

## 使用主题

```bash
# CLI 方式
python <skill-dir>/scripts/typeset.py article.md --theme minimal --preview article.preview.html

# 程序方式
from scripts.style_engine import ThemeEngine
engine = ThemeEngine(theme_name="minimal")
```
