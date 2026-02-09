"""输出模块"""
import os
from datetime import datetime
from typing import List, Dict
import json


class OutputManager:
    """输出管理器"""

    def __init__(self, config: Dict):
        self.format = config.get('format', 'markdown')
        self.directory = config.get('directory', 'output/summaries')
        self.filename_template = config.get('filename_template', 'ai_digest_{date}.md')

        # 确保输出目录存在
        os.makedirs(self.directory, exist_ok=True)

    def save_summary(self, summary: str, articles: List[Dict],
                    date: str = None) -> str:
        """
        保存总结到文件
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        filename = self.filename_template.replace('{date}', date)
        filepath = os.path.join(self.directory, filename)

        if self.format == 'markdown':
            content = self._format_markdown(summary, articles, date)
        elif self.format == 'json':
            content = self._format_json(summary, articles, date)
        elif self.format == 'html':
            content = self._format_html(summary, articles, date)
        else:
            content = summary

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✓ 总结已保存到: {filepath}")
        return filepath

    def _format_markdown(self, summary: str, articles: List[Dict], date: str) -> str:
        """生成Markdown格式"""
        content = f"""# AI每日摘要 - {date}

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 文章总数: {len(articles)}

---

{summary}

---

## 📚 完整文章列表

"""

        # 按分类组织文章列表
        from collections import defaultdict
        categorized = defaultdict(list)

        for article in articles:
            categorized[article['category']].append(article)

        for category in sorted(categorized.keys()):
            content += f"\n### {category}\n\n"
            for article in categorized[category]:
                content += f"- [{article['title']}]({article['link']})\n"
                content += f"  - 来源: {article['source']}\n"
                if article.get('author'):
                    content += f"  - 作者: {article['author']}\n"
                if article.get('published'):
                    content += f"  - 发布: {article['published']}\n"
                content += "\n"

        content += f"""
---

*由RSS聚合助手自动生成 | Powered by LLM*
"""

        return content

    def _format_json(self, summary: str, articles: List[Dict], date: str) -> str:
        """生成JSON格式"""
        data = {
            'date': date,
            'generated_at': datetime.now().isoformat(),
            'total_articles': len(articles),
            'summary': summary,
            'articles': articles
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _format_html(self, summary: str, articles: List[Dict], date: str) -> str:
        """生成HTML格式"""
        # 简单的HTML模板
        import markdown

        md_content = self._format_markdown(summary, articles, date)
        html_body = markdown.markdown(md_content)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI每日摘要 - {date}</title>
    <style>
        body {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
        }}
        h1, h2, h3 {{ color: #333; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        blockquote {{
            border-left: 4px solid #ddd;
            padding-left: 20px;
            color: #666;
        }}
        hr {{ border: none; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

        return html

    def print_summary(self, summary: str, articles: List[Dict]):
        """在终端打印摘要"""
        print("\n" + "="*80)
        print(f"AI每日摘要 - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*80 + "\n")
        print(summary)
        print("\n" + "="*80)
        print(f"共 {len(articles)} 篇文章")
        print("="*80 + "\n")
