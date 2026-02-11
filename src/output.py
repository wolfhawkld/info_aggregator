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

    def save_exploration(self, summary: str, exploration_data: Dict,
                        explorer_config: Dict) -> str:
        """
        保存探索结果到文件

        Args:
            summary: LLM生成的总结
            exploration_data: 探索数据字典
            explorer_config: 探索器配置

        Returns:
            保存的文件路径
        """
        topic = exploration_data['topic']
        date = datetime.now().strftime('%Y-%m-%d')

        output_dir = explorer_config.get('output_directory', 'output/explorations')
        os.makedirs(output_dir, exist_ok=True)

        safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
        filename_template = explorer_config.get('filename_template', 'explore_{topic}_{date}.md')
        filename = filename_template.replace('{topic}', safe_topic).replace('{date}', date)
        filepath = os.path.join(output_dir, filename)

        content = self._format_exploration_markdown(summary, exploration_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def _format_exploration_markdown(self, summary: str, exploration_data: Dict) -> str:
        """生成探索结果的Markdown格式"""
        topic = exploration_data['topic']
        search_date = exploration_data['search_date']
        time_range = exploration_data['time_range']
        total_results = exploration_data['total_results']
        results = exploration_data['results']

        content = f"""# 探索主题: {topic}

> **生成时间**: {search_date}
> **搜索时间范围**: {time_range}
> **找到结果数**: {total_results} 个
> **来源**: arXiv ({exploration_data['arxiv_count']}), Google Scholar ({exploration_data['scholar_count']})

---

## 🎯 AI智能总结

{summary}

---

## 📄 详细论文列表

"""

        arxiv_results = [r for r in results if r['source'] == 'arXiv']
        scholar_results = [r for r in results if r['source'] == 'Google Scholar']

        if arxiv_results:
            content += f"\n### arXiv 论文 ({len(arxiv_results)}篇)\n\n"
            if 'arxiv_url' in exploration_data and exploration_data['arxiv_url']:
                content += f"🔗 [在 arXiv 网站查看完整搜索结果]({exploration_data['arxiv_url']})\n\n"
            for i, paper in enumerate(arxiv_results, 1):
                authors = ', '.join(paper['authors'][:3])
                if len(paper['authors']) > 3:
                    authors += ' et al.'

                content += f"#### {i}. {paper['title']}\n\n"
                content += f"- **作者**: {authors}\n"
                content += f"- **发布日期**: {paper['published']}\n"
                content += f"- **分类**: {', '.join(paper.get('categories', []))}\n"
                content += f"- **论文链接**: [{paper['link']}]({paper['link']})\n"
                content += f"- **PDF链接**: [{paper['pdf_url']}]({paper['pdf_url']})\n"
                content += f"\n**摘要**: {paper['summary']}\n\n"
                content += "---\n\n"

        if scholar_results:
            content += f"\n### Google Scholar 论文 ({len(scholar_results)}篇)\n\n"
            for i, paper in enumerate(scholar_results, 1):
                if isinstance(paper['authors'], list):
                    authors = ', '.join(paper['authors'][:3])
                    if len(paper['authors']) > 3:
                        authors += ' et al.'
                else:
                    authors = str(paper['authors'])

                content += f"#### {i}. {paper['title']}\n\n"
                content += f"- **作者**: {authors}\n"
                content += f"- **发布时间**: {paper['published']}\n"
                content += f"- **引用数**: {paper.get('citations', 'N/A')}\n"
                content += f"- **链接**: [{paper['link']}]({paper['link']})\n"
                content += f"\n**摘要**: {paper['summary']}\n\n"
                content += "---\n\n"

        content += f"""

---

*由RSS聚合助手探索功能自动生成 | Powered by LLM*
*主题: {topic} | 生成于 {search_date}*
"""

        return content
