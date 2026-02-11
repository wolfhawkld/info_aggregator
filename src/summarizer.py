"""LLM总结模块"""
import os
from typing import List, Dict, Optional
import json


class LLMSummarizer:
    """使用LLM进行内容总结"""

    def __init__(self, config: Dict):
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 2000)

        # 从环境变量或配置获取API密钥
        api_key = config.get('api_key', '')
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var, '')

        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('AZURE_OPENAI_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.base_url = config.get('base_url', '')
        self.api_version = config.get('api_version', '2024-02-15-preview')  # Azure需要

        self._init_client()

    def _init_client(self):
        """初始化LLM客户端"""
        if self.provider == 'openai':
            from openai import OpenAI
            kwargs = {'api_key': self.api_key}
            if self.base_url:
                kwargs['base_url'] = self.base_url
            self.client = OpenAI(**kwargs)

        elif self.provider == 'azure':
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.base_url
            )

        elif self.provider == 'anthropic':
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)

        elif self.provider == 'ollama':
            from openai import OpenAI
            self.client = OpenAI(
                base_url=self.base_url or 'http://localhost:11434/v1',
                api_key='ollama'  # Ollama不需要真实API key
            )
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        """调用OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        """调用Anthropic Claude API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    def summarize_articles(self, articles: List[Dict],
                          summary_config: Dict,
                          language: str = 'zh') -> str:
        """
        总结文章列表
        """
        if not articles:
            return "今日暂无新内容更新。"

        # 准备文章内容
        articles_text = self._format_articles_for_llm(articles)

        # 构建提示词
        system_prompt = self._build_system_prompt(summary_config, language)
        user_prompt = self._build_user_prompt(articles_text, summary_config, language)

        print(f"\n正在使用 {self.provider} ({self.model}) 生成总结...")

        try:
            if self.provider in ['openai', 'azure', 'ollama']:
                summary = self._call_openai(user_prompt, system_prompt)
            elif self.provider == 'anthropic':
                summary = self._call_anthropic(user_prompt, system_prompt)
            else:
                summary = "错误: 不支持的LLM提供商"

            print("✓ 总结生成完成")
            return summary

        except Exception as e:
            error_msg = f"LLM调用失败: {str(e)}"
            print(f"✗ {error_msg}")
            return error_msg

    def _format_articles_for_llm(self, articles: List[Dict]) -> str:
        """格式化文章供LLM处理"""
        formatted = []

        for i, article in enumerate(articles, 1):
            text = f"""
文章 {i}:
标题: {article['title']}
来源: {article['source']}
分类: {article['category']}
链接: {article['link']}
内容摘要: {article['content'][:500]}
"""
            formatted.append(text.strip())

        return "\n\n---\n\n".join(formatted)

    def _build_system_prompt(self, config: Dict, language: str) -> str:
        """构建系统提示词"""
        if language == 'zh':
            prompt = """你是一位专业的AI领域技术分析师。你的任务是阅读今日收集的AI领域文章，并生成一份高质量的每日摘要。

要求：
1. 识别出最重要和最有价值的内容
2. 按技术主题分类（如：大模型、多模态、强化学习、Agent等）
3. 每篇重点文章用1-2句话概括核心内容
4. 突出技术创新点、实际应用价值和研究意义
5. 保持客观、准确、简洁的写作风格
6. 必须包含原文链接，方便深入阅读"""
        else:
            prompt = """You are a professional AI technology analyst. Your task is to read today's collected AI articles and generate a high-quality daily digest.

Requirements:
1. Identify the most important and valuable content
2. Categorize by technical topics (e.g., LLMs, Multimodal, RL, Agents, etc.)
3. Summarize each key article in 1-2 sentences covering core content
4. Highlight technical innovations, practical value, and research significance
5. Maintain objective, accurate, and concise writing style
6. Include original links for deep reading"""

        return prompt

    def _build_user_prompt(self, articles_text: str, config: Dict, language: str) -> str:
        """构建用户提示词"""
        style = config.get('summary_style', 'concise')
        keywords = config.get('highlight_keywords', [])

        if language == 'zh':
            prompt = f"""请阅读以下今日收集的AI领域文章，并生成一份每日摘要报告。

{'特别关注包含以下关键词的内容: ' + ', '.join(keywords) if keywords else ''}

文章内容：
{articles_text}

请生成一份{"详细" if style == "detailed" else "简洁"}的Markdown格式摘要，包括：
1. 今日要点（3-5个最重要的发现）
2. 分类内容（按主题分组）
3. 值得深入阅读的重点文章推荐

格式要求：使用Markdown标题、列表和链接。"""
        else:
            prompt = f"""Please read the following AI articles collected today and generate a daily digest report.

{'Pay special attention to content containing these keywords: ' + ', '.join(keywords) if keywords else ''}

Articles:
{articles_text}

Please generate a {"detailed" if style == "detailed" else "concise"} Markdown-formatted summary including:
1. Key Highlights (3-5 most important findings)
2. Categorized Content (grouped by topics)
3. Recommended Articles for Deep Reading

Format: Use Markdown headings, lists, and links."""

        return prompt

    def summarize_by_category(self, articles: List[Dict],
                             summary_config: Dict,
                             language: str = 'zh') -> Dict[str, str]:
        """
        按分类分别总结（适用于文章数量特别多的情况）
        """
        from collections import defaultdict

        # 按分类分组
        categorized = defaultdict(list)
        for article in articles:
            categorized[article['category']].append(article)

        summaries = {}

        for category, cat_articles in categorized.items():
            print(f"正在总结分类: {category} ({len(cat_articles)}篇)")
            summary = self.summarize_articles(cat_articles, summary_config, language)
            summaries[category] = summary

        return summaries

    def summarize_exploration(self, exploration_data: Dict,
                            summary_config: Dict,
                            language: str = 'zh') -> str:
        """
        总结探索结果（学术论文和技术内容）
        """
        if exploration_data['total_results'] == 0:
            return "未找到相关内容。"

        topic = exploration_data['topic']
        results = exploration_data['results']

        formatted = []
        for i, item in enumerate(results, 1):
            authors_str = ', '.join(item['authors'][:3]) if isinstance(item['authors'], list) else str(item['authors'])
            if len(item['authors']) > 3:
                authors_str += ' et al.'

            text = f"""
论文 {i}:
标题: {item['title']}
作者: {authors_str}
来源: {item['source']}
发布日期: {item['published']}
链接: {item['link']}
摘要: {item['summary'][:800]}
"""
            formatted.append(text.strip())

        articles_text = "\n\n---\n\n".join(formatted)

        if language == 'zh':
            system_prompt = f"""你是一位专业的学术研究分析师。你的任务是阅读关于"{topic}"主题的最新学术论文和技术文章，并生成一份高质量的分析报告。

要求：
1. 概括该领域的最新研究趋势和技术进展
2. 识别出最有价值和最具创新性的研究
3. 分析不同研究之间的关联和差异
4. 突出实际应用价值和未来研究方向
5. 保持客观、准确、专业的写作风格
6. 必须包含原文链接，方便深入阅读"""

            user_prompt = f"""请阅读以下关于"{topic}"的最新研究论文，并生成一份分析报告。

论文内容：
{articles_text}

请生成一份Markdown格式的分析报告，包括：
1. 研究趋势概述（总体方向和热点）
2. 重点论文分析（3-5篇最重要的论文，每篇2-3句话）
3. 技术创新点总结
4. 实际应用价值
5. 推荐阅读（按重要性排序）

格式要求：使用Markdown标题、列表和链接。"""
        else:
            system_prompt = f"""You are a professional academic research analyst. Your task is to read the latest academic papers and technical articles about "{topic}" and generate a high-quality analysis report.

Requirements:
1. Summarize the latest research trends and technical advances
2. Identify the most valuable and innovative research
3. Analyze connections and differences between studies
4. Highlight practical applications and future research directions
5. Maintain objective, accurate, and professional writing style
6. Include original links for deep reading"""

            user_prompt = f"""Please read the following research papers about "{topic}" and generate an analysis report.

Papers:
{articles_text}

Please generate a Markdown-formatted analysis report including:
1. Research Trends Overview (overall direction and hot topics)
2. Key Papers Analysis (3-5 most important papers, 2-3 sentences each)
3. Technical Innovation Summary
4. Practical Application Value
5. Recommended Reading (sorted by importance)

Format: Use Markdown headings, lists, and links."""

        print(f"\n正在使用 {self.provider} ({self.model}) 生成探索总结...")

        try:
            if self.provider in ['openai', 'azure', 'ollama']:
                summary = self._call_openai(user_prompt, system_prompt)
            elif self.provider == 'anthropic':
                summary = self._call_anthropic(user_prompt, system_prompt)
            else:
                summary = "错误: 不支持的LLM提供商"

            print("✓ 探索总结生成完成")
            return summary

        except Exception as e:
            error_msg = f"LLM调用失败: {str(e)}"
            print(f"✗ {error_msg}")
            return error_msg
