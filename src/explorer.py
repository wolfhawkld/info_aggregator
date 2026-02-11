"""内容探索模块 - 搜索学术论文和技术内容"""
import arxiv
from scholarly import scholarly
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import logging
import os
import certifi
import requests

logger = logging.getLogger(__name__)


class ContentExplorer:
    """内容探索器 - 搜索arXiv论文和Google Scholar"""

    def __init__(self, months_back: int = 1, results_limit: int = 10, cert_path: str = None):
        self.months_back = months_back
        self.results_limit = results_limit
        self.cutoff_date = datetime.now() - timedelta(days=30 * months_back)

        self._setup_ssl_cert(cert_path)
        self.arxiv_client = arxiv.Client()

    def _setup_ssl_cert(self, cert_path: str = None):
        """设置SSL证书，如果连接失败则自动添加本地证书"""
        try:
            print('检查arXiv连接...')
            test = requests.get('https://export.arxiv.org', timeout=10)
            print('✓ arXiv连接正常')
        except requests.exceptions.SSLError as err:
            print('✗ SSL证书错误，正在添加自定义证书到Certifi...')

            if not cert_path:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                cert_path = os.path.join(os.path.dirname(current_dir), 'certs', 'arxiv_fullchain.pem')

            if not os.path.exists(cert_path):
                logger.error(f"证书文件不存在: {cert_path}")
                print(f"错误: 证书文件不存在 {cert_path}")
                print("请先运行以下命令下载证书:")
                print("  mkdir -p certs")
                print("  echo | openssl s_client -showcerts -servername export.arxiv.org -connect export.arxiv.org:443 2>/dev/null | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > certs/arxiv_fullchain.pem")
                raise

            try:
                cafile = certifi.where()
                with open(cert_path, 'r') as infile:
                    customca = infile.read()

                with open(cafile, 'ab') as outfile:
                    outfile.write(customca.encode())

                print(f'✓ 证书已添加到 {cafile}')
                logger.info(f"已将 {cert_path} 添加到certifi证书库")

                test_again = requests.get('https://export.arxiv.org', timeout=10)
                print('✓ arXiv连接成功')

            except Exception as e:
                logger.error(f"添加证书失败: {e}")
                raise
        except Exception as e:
            logger.warning(f"连接测试失败: {e}")

    def search_arxiv(self, query: str, limit: int = 4) -> tuple[List[Dict], str]:
        """
        搜索arXiv论文

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            (论文列表, 搜索URL)
        """
        results = []

        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://arxiv.org/search/?query={encoded_query}&searchtype=all&abstracts=show&order=-announced_date_first&size=50"

        try:
            search = arxiv.Search(
                query=query,
                max_results=limit * 2,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            for paper in self.arxiv_client.results(search):
                if paper.published.replace(tzinfo=None) < self.cutoff_date:
                    continue

                results.append({
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'summary': paper.summary.replace('\n', ' ').strip(),
                    'published': paper.published.strftime('%Y-%m-%d'),
                    'link': paper.entry_id,
                    'pdf_url': paper.pdf_url,
                    'source': 'arXiv',
                    'categories': paper.categories
                })

                if len(results) >= limit:
                    break

            logger.info(f"arXiv搜索 '{query}': 找到 {len(results)} 篇论文")
            logger.info(f"arXiv网页搜索: {search_url}")

        except Exception as e:
            logger.error(f"arXiv搜索失败: {e}")

        return results, search_url

    def search_scholar(self, query: str, limit: int = 3) -> List[Dict]:
        """
        搜索Google Scholar

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            论文列表
        """
        results = []
        try:
            search_query = scholarly.search_pubs(query)
            logger.info(f"Scholar搜索开始 - 查询: '{query}', 限制: {limit}")

            count = 0
            processed = 0

            for pub in search_query:
                if count >= limit * 2:
                    logger.info(f"达到最大迭代次数 {limit * 2}，停止搜索")
                    break

                try:
                    # 记录原始数据结构
                    logger.debug(f"处理第 {count+1} 个结果")
                    logger.debug(f"pub keys: {pub.keys()}")

                    title = pub.get('bib', {}).get('title', 'N/A')
                    pub_year = pub.get('bib', {}).get('pub_year')

                    logger.debug(f"论文标题: {title}")
                    logger.debug(f"发表年份: {pub_year}")

                    # Scholar不做时间过滤，因为只有年份信息不够精确
                    # Google Scholar通常只返回最近和相关的论文，无需额外过滤

                    # 构建结果
                    paper_data = {
                        'title': title,
                        'authors': pub.get('bib', {}).get('author', []),
                        'summary': pub.get('bib', {}).get('abstract', 'No abstract available'),
                        'published': pub_year or 'Unknown',
                        'link': pub.get('pub_url', pub.get('eprint_url', '#')),
                        'citations': pub.get('num_citations', 0),
                        'source': 'Google Scholar'
                    }

                    results.append(paper_data)
                    processed += 1
                    logger.info(f"✓ 添加论文: {title[:80]}... (年份: {pub_year})")

                    if len(results) >= limit:
                        logger.info(f"已收集足够结果 ({limit} 篇)，停止搜索")
                        break

                except Exception as e:
                    logger.warning(f"处理Scholar结果时出错: {e}", exc_info=True)
                    continue
                finally:
                    count += 1
                    time.sleep(2)

            logger.info(f"Scholar搜索 '{query}' 完成: 迭代 {count} 次, 收集 {len(results)} 篇")

        except Exception as e:
            logger.error(f"Google Scholar搜索失败: {e}", exc_info=True)

        return results

    def explore_topic(self, topic: str) -> Dict:
        """
        探索指定主题的内容

        Args:
            topic: 主题关键词

        Returns:
            包含所有搜索结果的字典
        """
        logger.info(f"开始探索主题: {topic}")

        arxiv_limit = min(self.results_limit // 2 + 1, 4)
        scholar_limit = min(self.results_limit - arxiv_limit, 3)

        arxiv_results, arxiv_url = self.search_arxiv(topic, limit=arxiv_limit)
        time.sleep(1)

        scholar_results = self.search_scholar(topic, limit=scholar_limit)

        all_results = arxiv_results + scholar_results
        all_results = all_results[:self.results_limit]

        return {
            'topic': topic,
            'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_range': f'最近{self.months_back}个月',
            'total_results': len(all_results),
            'arxiv_count': len(arxiv_results),
            'scholar_count': len(scholar_results),
            'arxiv_url': arxiv_url,
            'results': all_results
        }
