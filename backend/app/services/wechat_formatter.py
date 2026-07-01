"""微信格式化 —— Markdown → 微信兼容的 HTML（内联样式）"""
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


# 微信支持的全局样式
PAGE_STYLE = """
body {
    max-width: 680px; margin: 0 auto; padding: 16px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 16px; line-height: 1.8; color: #333;
}
h1 { font-size: 22px; font-weight: bold; margin: 24px 0 12px; color: #1a1a1a; border-bottom: 2px solid #3f51b5; padding-bottom: 8px; }
h2 { font-size: 20px; font-weight: bold; margin: 20px 0 10px; color: #1a1a1a; }
h3 { font-size: 18px; font-weight: bold; margin: 16px 0 8px; color: #1a1a1a; }
p  { margin: 10px 0; }
blockquote { border-left: 4px solid #3f51b5; padding: 8px 16px; margin: 12px 0; background: #f5f5f5; color: #666; }
ul, ol { padding-left: 24px; margin: 8px 0; }
li { margin: 4px 0; }
a  { color: #3f51b5; text-decoration: none; }
strong { font-weight: bold; color: #1a1a1a; }
code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 14px; font-family: "SF Mono", Consolas, monospace; }
pre { background: #282c34; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.6; }
pre code { background: none; padding: 0; color: #abb2bf; }
img { max-width: 100%; height: auto; display: block; margin: 12px auto; border-radius: 4px; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
th, td { border: 1px solid #e0e0e0; padding: 8px 12px; text-align: left; }
th { background: #f5f5f5; font-weight: bold; }
"""


def markdown_to_wechat_html(md_text: str, title: str = "") -> str:
    """把 Markdown 文本转成可直接粘贴到微信公众号编辑器的 HTML"""

    # 1. Markdown → HTML
    html_body = markdown.markdown(
        md_text,
        extensions=[
            "fenced_code",      # ``` 代码块
            "codehilite",        # 代码高亮
            "tables",            # 表格
            "toc",               # 目录
        ],
    )

    # 2. 组装完整 HTML 页面（内联样式、无 JS）
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title or '微信文章'}</title>
<style>{PAGE_STYLE}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    return full_html
