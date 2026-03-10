"""RSS订阅源抓取模块"""
import feedparser
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from typing import List, Dict, Optional
import time
from bs4 import BeautifulSoup
import re
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS内容抓取器"""

    def __init__(self, timeout: int = 30, days_back: int = 1, fetch_limit: int = 10):
        self.timeout = timeout
        self.days_back = days_back
        self.fetch_limit = fetch_limit
        # 分离连接超时和读取超时：连接超时短，读取超时长
        # (connect_timeout, read_timeout)
        self.timeout_tuple = (10, timeout)  # 连接超时10秒，读取超时由配置决定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_feeds(self, feeds_file: str, region: str = None) -> List[Dict[str, str]]:
        """
        加载RSS源列表
        支持 YAML 格式（优先）和 TXT 格式（向后兼容）

        Args:
            feeds_file: 配置文件路径
            region: 区域过滤，'cn' 表示国内站点，None 表示全部
        """
        feeds = []
        skipped_count = 0
        total_count = 0

        try:
            path = Path(feeds_file)

            # 检测文件格式
            if path.suffix in ['.yaml', '.yml']:
                feeds = self._load_yaml_feeds(feeds_file, region)
            else:
                feeds = self._load_txt_feeds(feeds_file)

            # 按 priority 降序排序（高优先级先抓取）
            feeds.sort(key=lambda x: x.get('priority', 3), reverse=True)

            region_info = f" (区域: {region})" if region else ""
            message = f"RSS源加载完成: 共 {len(feeds)} 个源{region_info}"
            print(message)
            logger.info(message)

            if len(feeds) == 0:
                logger.warning("警告: 没有加载任何RSS源")

        except FileNotFoundError:
            error_msg = f"RSS源文件 {feeds_file} 不存在"
            print(f"警告: {error_msg}")
            logger.error(error_msg)

        return feeds

    def _load_yaml_feeds(self, feeds_file: str, region: str = None) -> List[Dict]:
        """加载 YAML 格式的 RSS 源配置

        Args:
            feeds_file: 配置文件路径
            region: 区域过滤，'cn' 表示国内站点，None 表示全部
        """
        feeds = []

        with open(feeds_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        feed_list = config.get('feeds', [])
        enabled_count = 0
        region_filtered = 0

        for feed in feed_list:
            status = feed.get('status', 'enabled')
            feed_region = feed.get('region', 'global')

            # 区域过滤
            if region and feed_region != region:
                region_filtered += 1
                logger.debug(f"跳过非目标区域源: {feed.get('name', feed['url'][:40])} (区域: {feed_region})")
                continue

            if status == 'enabled':
                feeds.append({
                    'url': feed['url'],
                    'category': feed.get('category', '未分类'),
                    'priority': feed.get('priority', 3),
                    'frequency': feed.get('frequency', '未知'),
                    'name': feed.get('name', ''),
                    'region': feed_region
                })
                enabled_count += 1
                logger.debug(f"加载RSS源: {feed.get('name', feed['url'][:40])} - 分类: {feed.get('category')} - 优先级: {feed.get('priority', 3)}")
            else:
                logger.debug(f"跳过非启用源: {feed.get('name', feed['url'][:40])} (状态: {status})")

        region_info = f", 区域过滤跳过 {region_filtered} 个" if region else ""
        logger.info(f"YAML配置: 共 {len(feed_list)} 个源, 已启用 {enabled_count} 个{region_info}")
        return feeds

    def _load_txt_feeds(self, feeds_file: str) -> List[Dict]:
        """加载 TXT 格式的 RSS 源配置（向后兼容）"""
        feeds = []
        skipped_count = 0
        total_count = 0

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
                        'category': category,
                        'priority': 3,  # TXT 格式默认优先级
                        'frequency': '未知',
                        'name': url.split('/')[2] if '/' in url else url
                    })
                    logger.debug(f"加载RSS源: {url} - 分类: {category}")
                else:
                    skipped_count += 1
                    logger.debug(f"跳过未分类RSS源: {url}")

        message = f"TXT配置: 总共 {total_count} 个源, 已加载 {len(feeds)} 个已分类源, 跳过 {skipped_count} 个未分类源"
        logger.info(message)

        return feeds

    def clean_html(self, html_content: str) -> str:
        """清理HTML内容，提取纯文本"""
        if not html_content:
            return ""

        # 使用 html.parser 替代 lxml，避免创建临时文件
        # html.parser 是 Python 内置解析器，不会产生磁盘 I/O
        soup = BeautifulSoup(html_content, 'html.parser')

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
            logger.info(f"开始抓取RSS源: {feed_url}")

            # 使用 requests 下载内容（支持超时），再传给 feedparser 解析
            # timeout=(connect_timeout, read_timeout) 分别设置连接和读取超时
            response = self.session.get(feed_url, timeout=self.timeout_tuple)
            response.raise_for_status()

            # 解析RSS
            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"  警告: RSS解析可能不完整 - {feed.bozo_exception}")
                logger.warning(f"RSS解析警告: {feed.bozo_exception}")

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
            logger.info(f"RSS源抓取成功: {feed_url} - {count} 篇文章")

        except Timeout:
            error_msg = f"超时 ({self.timeout_tuple[0]}秒连接/{self.timeout_tuple[1]}秒读取)"
            print(f"  ✗ {error_msg}")
            logger.error(f"RSS源抓取超时: {feed_url} - {error_msg}")
        except ConnectionError as e:
            error_msg = f"连接失败: {str(e)[:100]}"
            print(f"  ✗ {error_msg}")
            logger.error(f"RSS源连接失败: {feed_url} - {error_msg}")
        except RequestException as e:
            error_msg = f"请求错误: {str(e)[:100]}"
            print(f"  ✗ {error_msg}")
            logger.error(f"RSS源请求错误: {feed_url} - {error_msg}")
        except Exception as e:
            error_msg = f"未知错误: {str(e)[:100]}"
            print(f"  ✗ {error_msg}")
            logger.error(f"RSS源抓取异常: {feed_url} - {error_msg}", exc_info=True)

        return articles

    def fetch_all(self, feeds: List[Dict[str, str]]) -> List[Dict]:
        """
        抓取所有RSS源
        """
        all_articles = []

        print(f"\n开始抓取 {len(feeds)} 个RSS源...")
        print(f"时间范围: 最近 {self.days_back} 天")
        print(f"每源限制: {self.fetch_limit} 篇\n")

        try:
            for i, feed in enumerate(feeds, 1):
                print(f"[{i}/{len(feeds)}] ", end='')
                articles = self.fetch_feed(feed['url'], feed['category'])
                all_articles.extend(articles)

                # 避免请求过快
                if i < len(feeds):
                    time.sleep(0.5)
        finally:
            # 确保 Session 被关闭，释放资源
            self.session.close()

        print(f"\n总计抓取 {len(all_articles)} 篇文章")

        return all_articles
