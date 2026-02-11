"""RSS订阅源抓取模块"""
import feedparser
import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional
import time
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS内容抓取器"""

    def __init__(self, timeout: int = 30, days_back: int = 1, fetch_limit: int = 10):
        self.timeout = timeout
        self.days_back = days_back
        self.fetch_limit = fetch_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_feeds(self, feeds_file: str) -> List[Dict[str, str]]:
        """
        加载RSS源列表
        支持格式: URL [分类标签]
        只加载分类标签不是"未分类"的源
        """
        feeds = []
        skipped_count = 0
        total_count = 0

        try:
            with open(feeds_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    total_count += 1
                    parts = line.split('[')
                    url = parts[0].strip()
                    category = parts[1].strip(']').strip() if len(parts) > 1 else '未分类'

                    # 只添加分类不是"未分类"的源
                    if category != '未分类':
                        feeds.append({
                            'url': url,
                            'category': category
                        })
                        logger.debug(f"加载RSS源: {url} - 分类: {category}")
                    else:
                        skipped_count += 1
                        logger.debug(f"跳过未分类RSS源: {url}")

            message = f"RSS源加载完成: 总共 {total_count} 个源, 已加载 {len(feeds)} 个已分类源, 跳过 {skipped_count} 个未分类源"
            print(message)
            logger.info(message)

            if len(feeds) == 0:
                logger.warning("警告: 没有加载任何RSS源，请检查是否有已分类的源")

        except FileNotFoundError:
            error_msg = f"RSS源文件 {feeds_file} 不存在"
            print(f"警告: {error_msg}")
            logger.error(error_msg)

        return feeds

    def clean_html(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本"""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'lxml')

        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        # 获取文本
        text = soup.get_text()

        # 清理空白字符
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:1000]  # 限制长度

    def is_recent(self, entry_date: Optional[str], days_back: int) -> bool:
        """判断文章是否在指定天数内"""
        if not entry_date:
            return True  # 如果没有日期，默认包含

        try:
            if isinstance(entry_date, str):
                pub_date = date_parser.parse(entry_date)
            else:
                pub_date = datetime(*entry_date[:6])

            cutoff_date = datetime.now() - timedelta(days=days_back)
            return pub_date >= cutoff_date
        except:
            return True  # 解析失败，默认包含

    def fetch_feed(self, feed_url: str, category: str) -> List[Dict]:
        """
        抓取单个RSS源的内容
        """
        articles = []

        try:
            print(f"正在抓取: {feed_url} [{category}]")

            # 解析RSS
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"  警告: RSS解析可能不完整")

            # 获取源信息
            feed_title = feed.feed.get('title', '未知源')

            # 处理每篇文章
            count = 0
            for entry in feed.entries:
                if count >= self.fetch_limit:
                    break

                # 检查发布时间
                pub_date = entry.get('published', entry.get('updated', ''))
                if not self.is_recent(pub_date, self.days_back):
                    continue

                # 提取内容
                title = entry.get('title', '无标题')
                link = entry.get('link', '')

                # 获取描述/摘要
                description = entry.get('summary', entry.get('description', ''))
                content = self.clean_html(description)

                # 获取作者
                author = entry.get('author', '')

                articles.append({
                    'title': title,
                    'link': link,
                    'content': content,
                    'author': author,
                    'published': pub_date,
                    'source': feed_title,
                    'category': category
                })

                count += 1

            print(f"  ✓ 成功抓取 {count} 篇文章")

        except Exception as e:
            print(f"  ✗ 抓取失败: {str(e)}")

        return articles

    def fetch_all(self, feeds: List[Dict[str, str]]) -> List[Dict]:
        """
        抓取所有RSS源
        """
        all_articles = []

        print(f"\n开始抓取 {len(feeds)} 个RSS源...")
        print(f"时间范围: 最近 {self.days_back} 天")
        print(f"每源限制: {self.fetch_limit} 篇\n")

        for i, feed in enumerate(feeds, 1):
            print(f"[{i}/{len(feeds)}] ", end='')
            articles = self.fetch_feed(feed['url'], feed['category'])
            all_articles.extend(articles)

            # 避免请求过快
            if i < len(feeds):
                time.sleep(0.5)

        print(f"\n总计抓取 {len(all_articles)} 篇文章")

        return all_articles
