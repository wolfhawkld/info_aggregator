# -*- coding: utf-8 -*-
"""文章历史去重模块 - 避免重复总结已处理过的文章"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


class ArticleDeduplicator:
    """基于本地 JSON 记录的文章去重器

    记录已总结过文章的标识（优先 guid，其次 link，最后 title），
    下次抓取时跳过这些文章，避免同一内容在每日摘要中反复出现。
    """

    def __init__(self, store_path: str = 'data/seen_articles.json', retention_days: int = 30):
        self.store_path = store_path
        self.retention_days = retention_days
        # key -> 首次见到的日期字符串 'YYYY-MM-DD'
        self.seen: Dict[str, str] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.store_path):
            return
        try:
            with open(self.store_path, 'r', encoding='utf-8') as f:
                self.seen = json.load(f)
            logger.info(f"加载去重记录: {len(self.seen)} 条")
        except Exception as e:
            logger.warning(f"加载去重记录失败，将重新开始: {e}")
            self.seen = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.store_path) or '.', exist_ok=True)
        tmp_path = self.store_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self.seen, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.store_path)

    @staticmethod
    def _article_key(article: Dict) -> str:
        # 优先 GUID，其次链接，最后标题；去掉尾部斜杠差异
        key = article.get('guid') or article.get('link') or article.get('title') or ''
        return key.strip().rstrip('/')

    def filter_new(self, articles: List[Dict]) -> List[Dict]:
        """返回尚未总结过的文章列表"""
        new_articles = []
        dup_count = 0
        for article in articles:
            key = self._article_key(article)
            if not key:
                new_articles.append(article)
                continue
            if key in self.seen:
                dup_count += 1
                logger.debug(f"跳过重复文章: {article.get('title', '')[:60]}")
            else:
                new_articles.append(article)
        if dup_count:
            logger.info(f"历史去重: 跳过 {dup_count} 篇已总结文章，剩余 {len(new_articles)} 篇")
        return new_articles

    def mark_seen(self, articles: List[Dict]):
        """将文章标记为已总结并持久化"""
        today = datetime.now().strftime('%Y-%m-%d')
        for article in articles:
            key = self._article_key(article)
            if key:
                self.seen[key] = today
        self._prune()
        self._save()
        logger.info(f"已记录 {len(articles)} 篇文章到去重库（总计 {len(self.seen)} 条）")

    def _prune(self):
        """清理超过保留期的记录"""
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).strftime('%Y-%m-%d')
        before = len(self.seen)
        self.seen = {k: v for k, v in self.seen.items() if v >= cutoff}
        pruned = before - len(self.seen)
        if pruned:
            logger.info(f"清理过期去重记录: {pruned} 条（保留 {self.retention_days} 天）")
