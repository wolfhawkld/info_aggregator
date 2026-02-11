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
import random

logger = logging.getLogger(__name__)


class ContentExplorer:
    """内容探索器 - 搜索arXiv论文和Google Scholar"""

    def __init__(self, months_back: int = 1, results_limit: int = 10, cert_path: str = None,
                 scholar_retry: int = 3, scholar_delay_range: list = None, enable_scholar: bool = True):
        self.months_back = months_back
        self.results_limit = results_limit
        self.cutoff_date = datetime.now() - timedelta(days=30 * months_back)

        # Scholar 防限流配置
        self.enable_scholar = enable_scholar
        self.scholar_retry = scholar_retry
        self.scholar_delay_range = scholar_delay_range or [5, 10]

        # 标题搜索使用更宽松的时间范围（2年），因为有些领域论文更新不频繁
        self.relaxed_cutoff = datetime.now() - timedelta(days=730)  # 2年 = 730天
        logger.info(f"时间过滤: 标题搜索={self.relaxed_cutoff.strftime('%Y-%m-%d')} (2年), 原始={self.cutoff_date.strftime('%Y-%m-%d')} ({months_back}个月)")

        self._setup_ssl_cert(cert_path)
        self.arxiv_client = arxiv.Client()

        # 配置 scholarly 防限流策略
        self._setup_scholarly()

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

    def _setup_scholarly(self):
        """配置 scholarly 的防限流策略"""
        try:
            # 设置随机 User-Agent 池
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]

            # 随机选择一个 User-Agent
            selected_ua = random.choice(user_agents)
            logger.info(f"Scholar 配置: User-Agent = {selected_ua[:50]}...")

            # 注意：scholarly 2.x 版本没有直接的 set_user_agent 方法
            # 需要通过修改内部 session 来实现
            # 这里我们主要依靠延迟策略

            logger.info("Scholar 防限流策略已配置: 随机延迟 5-10秒")

        except Exception as e:
            logger.warning(f"Scholar配置失败: {e}")

    def search_arxiv(self, query: str, limit: int = 4) -> tuple[List[Dict], str]:
        """
        搜索arXiv论文（按标题搜索，按提交日期倒序）

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            (论文列表, 搜索URL)
        """
        results = []

        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://arxiv.org/search/?query={encoded_query}&searchtype=title&abstracts=show&order=-submitted_date&size=50"

        # arXiv API: 使用 ti: 前缀进行标题搜索
        title_query = f"ti:{query}"
        logger.debug(f"arXiv API查询: {title_query}")

        try:
            search = arxiv.Search(
                query=title_query,
                max_results=limit * 2,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            total_found = 0
            filtered_out = 0

            for paper in self.arxiv_client.results(search):
                total_found += 1
                paper_date = paper.published.replace(tzinfo=None)

                # 标题搜索使用更宽松的时间限制（至少 6 个月）
                if paper_date < self.relaxed_cutoff:
                    filtered_out += 1
                    logger.debug(f"过滤旧论文: {paper.title[:60]}... (发布于 {paper_date.strftime('%Y-%m-%d')})")
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

                logger.debug(f"✓ 添加论文: {paper.title[:60]}... (发布于 {paper_date.strftime('%Y-%m-%d')})")

                if len(results) >= limit:
                    break

            logger.info(f"arXiv搜索 '{query}': API返回 {total_found} 篇, 过滤 {filtered_out} 篇, 最终 {len(results)} 篇")
            logger.info(f"arXiv网页搜索: {search_url}")

        except Exception as e:
            logger.error(f"arXiv搜索失败: {e}")

        return results, search_url

    def search_scholar(self, query: str, limit: int = 3, max_retries: int = None) -> List[Dict]:
        """
        搜索Google Scholar (带防限流策略)

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            max_retries: CAPTCHA触发后的重试次数（None则使用配置值）

        Returns:
            论文列表
        """
        results = []
        retry_count = 0
        max_retries = max_retries or self.scholar_retry
        base_delay = self.scholar_delay_range[0]  # 使用配置的最小延迟

        while retry_count <= max_retries:
            try:
                # 如果是重试，先等待指数退避时间
                if retry_count > 0:
                    wait_time = base_delay * (2 ** retry_count) + random.uniform(5, 15)
                    logger.warning(f"⏸ Scholar触发限流，等待 {wait_time:.1f} 秒后重试 ({retry_count}/{max_retries})...")
                    print(f"\n⚠️  Google Scholar 触发限流保护")
                    print(f"⏳ 等待 {wait_time:.1f} 秒后自动重试... ({retry_count}/{max_retries})")
                    time.sleep(wait_time)

                search_query = scholarly.search_pubs(query)
                logger.info(f"Scholar搜索开始 - 查询: '{query}', 限制: {limit}, 尝试: {retry_count+1}")

                count = 0
                processed = 0
                captcha_detected = False

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
                        error_msg = str(e).lower()
                        # 检测 CAPTCHA 相关错误
                        if 'captcha' in error_msg or '429' in error_msg or 'too many requests' in error_msg:
                            logger.warning(f"⚠️  检测到限流信号: {e}")
                            captcha_detected = True
                            break
                        logger.warning(f"处理Scholar结果时出错: {e}", exc_info=True)
                        continue
                    finally:
                        count += 1
                        # 使用配置的随机延迟范围（默认 5-10 秒）
                        delay = random.uniform(self.scholar_delay_range[0], self.scholar_delay_range[1])
                        logger.debug(f"等待 {delay:.1f} 秒...")
                        time.sleep(delay)

                # 如果检测到 CAPTCHA，触发重试
                if captcha_detected:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"❌ Scholar 达到最大重试次数 {max_retries}，放弃搜索")
                        print(f"\n❌ Google Scholar 持续限流，已放弃搜索")
                        print(f"💡 建议: 稍后手动重试，或等待更长时间")
                        break
                    continue  # 继续重试循环

                # 成功完成搜索
                logger.info(f"Scholar搜索 '{query}' 完成: 迭代 {count} 次, 收集 {len(results)} 篇")
                break  # 跳出重试循环

            except Exception as e:
                error_msg = str(e).lower()
                # 检测限流相关错误
                if 'captcha' in error_msg or '429' in error_msg or 'too many requests' in error_msg:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"❌ Scholar搜索失败，达到最大重试次数: {e}")
                        print(f"\n❌ Google Scholar 持续限流，搜索失败")
                        break
                    continue  # 继续重试
                else:
                    # 其他类型错误，直接失败
                    logger.error(f"Google Scholar搜索失败: {e}", exc_info=True)
                    break

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

        # 根据是否启用Scholar动态调整查询数量
        if self.enable_scholar:
            arxiv_limit = min(self.results_limit // 2 + 1, 4)
            scholar_limit = min(self.results_limit - arxiv_limit, 3)
            logger.info(f"Scholar已启用 - arXiv: {arxiv_limit}篇, Scholar: {scholar_limit}篇")
        else:
            arxiv_limit = self.results_limit
            scholar_limit = 0
            logger.warning(f"⚠️  Scholar已禁用 - 仅使用arXiv，查询 {arxiv_limit}篇")
            print(f"⚠️  Google Scholar 已禁用（避免限流），仅使用 arXiv 查询 {arxiv_limit} 篇论文")

        arxiv_results, arxiv_url = self.search_arxiv(topic, limit=arxiv_limit)
        time.sleep(1)

        # 只有启用Scholar时才搜索
        if self.enable_scholar:
            scholar_results = self.search_scholar(topic, limit=scholar_limit)
        else:
            scholar_results = []
            logger.info("跳过Scholar搜索")

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
