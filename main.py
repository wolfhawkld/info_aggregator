# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
RSS聚合助手 - 主程序
自动抓取RSS订阅源，使用LLM生成每日AI摘要
"""

import os
import sys
import yaml
import argparse
import logging
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fetcher import RSSFetcher
from summarizer import LLMSummarizer
from output import OutputManager
from explorer import ContentExplorer
from notifier import EmailNotifier


def setup_logging(log_level: str = 'INFO'):
    """配置日志系统"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'rss_aggregator_{datetime.now().strftime("%Y%m%d")}.log')

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return log_file


def load_config(config_file: str = 'config/config.yaml') -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def run_aggregator(config: dict, dry_run: bool = False, test_mode: bool = False, region: str = None):
    """
    运行RSS聚合流程

    Args:
        config: 配置字典
        dry_run: 仅抓取不总结
        test_mode: 测试模式（限制源数量）
        region: 区域过滤，'cn' 表示国内站点
    """
    print("="*80)
    print("RSS AI聚合助手")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if region:
        print(f"区域过滤: {'国内站点' if region == 'cn' else '国际站点'}")
    print()

    # 1. 初始化抓取器
    fetcher = RSSFetcher(
        timeout=config['rss']['timeout'],
        days_back=config['rss']['days_back'],
        fetch_limit=config['rss']['fetch_limit']
    )

    # 2. 加载RSS源
    feeds = fetcher.load_feeds(config['rss']['feeds_file'], region=region)
    logging.info(f"加载了 {len(feeds)} 个RSS源" + (f" (区域: {region})" if region else ""))

    if not feeds:
        print("错误: 没有找到任何RSS源，请检查配置文件")
        logging.error("没有找到任何RSS源")
        return

    if test_mode:
        print(f"⚠️  测试模式：仅使用前5个源\n")
        feeds = feeds[:5]
        logging.info("测试模式：限制为前5个源")

    # 3. 抓取文章
    logging.info("开始抓取RSS文章...")
    articles = fetcher.fetch_all(feeds)
    logging.info(f"抓取完成：共 {len(articles)} 篇文章")

    if not articles:
        print("\n没有抓取到任何新文章")
        logging.warning("没有抓取到任何新文章")
        return

    # 4. 显示统计信息
    print("\n" + "-"*80)
    print("抓取统计:")
    from collections import Counter
    category_counts = Counter(article['category'] for article in articles)
    for category, count in category_counts.most_common():
        print(f"  {category}: {count}篇")
    print("-"*80 + "\n")

    # 如果是dry-run模式，到此结束
    if dry_run:
        print("Dry-run模式：跳过LLM总结")
        return

    # 5. 使用LLM生成总结
    try:
        logging.info(f"初始化LLM总结器 - Provider: {config['llm']['provider']}, Model: {config['llm']['model']}")
        summarizer = LLMSummarizer(config['llm'])

        # 根据文章数量选择总结策略
        if len(articles) > 50 and config['summary'].get('group_by_category', False):
            print("文章数量较多，按分类分别总结...")
            logging.info(f"采用分类总结策略 - 文章数: {len(articles)}")
            summaries = summarizer.summarize_by_category(
                articles,
                config['summary'],
                config['output']['language']
            )
            # 合并所有分类的总结
            summary = "\n\n".join([
                f"## {category}\n\n{text}"
                for category, text in summaries.items()
            ])
            logging.info(f"分类总结完成 - 分类数: {len(summaries)}")
        else:
            logging.info(f"开始生成LLM总结 - 文章数: {len(articles)}")
            summary = summarizer.summarize_articles(
                articles,
                config['summary'],
                config['output']['language']
            )

    except Exception as e:
        print(f"\n错误: LLM总结失败 - {str(e)}")
        print("请检查:")
        print("  1. API密钥是否正确配置")
        print("  2. 网络连接是否正常")
        print("  3. LLM服务是否可用")
        logging.error(f"LLM总结失败: {str(e)}", exc_info=True)
        return

    logging.info(f"LLM总结完成 - 总长度: {len(summary)} 字符")

    # 6. 保存和输出
    output_manager = OutputManager(config['output'])

    # 保存到文件
    output_file = output_manager.save_summary(summary, articles)
    logging.info(f"摘要已保存到: {output_file}")

    # 同时在终端显示
    output_manager.print_summary(summary, articles)

    print(f"\n✅ 完成！摘要已保存到: {output_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("RSS聚合流程完成")


def run_explorer(config: dict, topics: list):
    """
    运行内容探索流程

    Args:
        config: 配置字典
        topics: 探索主题列表
    """
    print("="*80)
    print("内容探索模式 - 搜索学术论文与技术内容")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"探索主题: {', '.join(topics)}\n")

    explorer_config = config.get('explorer', {})
    enable_scholar = explorer_config.get('enable_scholar', True)
    logging.info(f"初始化内容探索器 - 时间范围: {explorer_config.get('months_back', 1)}个月, Scholar: {'启用' if enable_scholar else '禁用'}")
    explorer = ContentExplorer(
        months_back=explorer_config.get('months_back', 1),
        results_limit=explorer_config.get('results_limit', 10),
        cert_path=explorer_config.get('cert_path'),
        scholar_retry=explorer_config.get('scholar_retry', 3),
        scholar_delay_range=explorer_config.get('scholar_delay_range', [5, 10]),
        enable_scholar=enable_scholar
    )

    for topic in topics:
        print(f"\n{'='*80}")
        print(f"正在探索主题: {topic}")
        print('='*80)
        logging.info(f"开始探索主题: {topic}")

        exploration_data = explorer.explore_topic(topic)

        if exploration_data['total_results'] == 0:
            print(f"未找到关于 '{topic}' 的相关内容")
            logging.warning(f"未找到关于 '{topic}' 的相关内容")
            continue

        print(f"✓ 找到 {exploration_data['total_results']} 个结果")
        print(f"  - arXiv: {exploration_data['arxiv_count']} 篇")
        print(f"  - Scholar: {exploration_data['scholar_count']} 篇")
        logging.info(f"探索 '{topic}' 完成 - 总计: {exploration_data['total_results']} (arXiv: {exploration_data['arxiv_count']}, Scholar: {exploration_data['scholar_count']})")

        try:
            summarizer = LLMSummarizer(config['llm'])
            summary_config = config['summary']
            language = config['output']['language']

            print("\n正在生成智能摘要...")
            logging.info(f"开始为主题 '{topic}' 生成LLM摘要...")
            summary = summarizer.summarize_exploration(
                exploration_data,
                summary_config,
                language
            )
            logging.info(f"LLM摘要生成完成 - 长度: {len(summary)} 字符")

            output_manager = OutputManager(config['output'])
            output_file = output_manager.save_exploration(
                summary,
                exploration_data,
                explorer_config
            )
            logging.info(f"探索结果已保存到: {output_file}")

            print(f"✅ 探索完成！结果已保存到: {output_file}")

        except Exception as e:
            print(f"\n错误: 处理主题 '{topic}' 时失败 - {str(e)}")
            logging.error(f"处理主题 '{topic}' 时出错: {str(e)}", exc_info=True)
            continue

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_daily_task(config: dict):
    """
    运行每日全量任务

    工作流程：
    1. 检查当天内容是否已存在
    2. 如不存在，执行RSS抓取和探索
    3. 生成HTML版本文件
    4. 生成一句话摘要并发送邮件（包含web链接）
    """
    daily_config = config.get('daily', {})
    topics = daily_config.get('topics', [])
    web_config = daily_config.get('web', {})

    # 使用web目录作为输出路径
    output_base = web_config.get('output_base_path', 'resource/daily')
    base_url = web_config.get('base_url', '')

    date_str = datetime.now().strftime('%Y-%m-%d')
    output_dir = os.path.join(output_base, date_str)
    web_url = f"{base_url}/{date_str}" if base_url else ""

    print("=" * 80)
    print("每日任务模式 - 一键执行全量任务")
    print("=" * 80)
    print(f"当前日期: {date_str}")
    print(f"输出目录: {output_dir}")
    if web_url:
        print(f"访问URL: {web_url}")

    # 检查当天内容是否已存在
    existing_results = _check_existing_daily_content(output_dir, topics)

    if existing_results:
        print("\n✓ 检测到今日内容已存在，跳过抓取步骤")
        logging.info("今日内容已存在，跳过抓取")
        results = existing_results
    else:
        # 执行抓取和探索
        os.makedirs(output_dir, exist_ok=True)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"探索主题: {', '.join(topics)}\n")
        logging.info(f"每日任务启动 - 输出目录: {output_dir}, 主题数: {len(topics)}")

        results = _execute_daily_tasks(config, output_dir, date_str, topics)

    # 生成HTML版本文件
    _generate_html_files(output_dir, results, date_str)

    # 生成一句话摘要并发送邮件（包含web链接）
    _send_daily_email(config, output_dir, date_str, results, web_url)


def _check_existing_daily_content(output_dir: str, topics: list) -> dict:
    """
    检查当天内容是否已存在

    Returns:
        如果存在返回results字典，否则返回None
    """
    if not os.path.exists(output_dir):
        return None

    results = {
        'rss': None,
        'explorations': []
    }

    # 检查RSS摘要
    rss_file = os.path.join(output_dir, 'rss_summary.md')
    if os.path.exists(rss_file):
        # 读取文件估算文章数
        with open(rss_file, 'r', encoding='utf-8') as f:
            content = f.read()
            article_count = content.count('- 来源:')
        results['rss'] = {
            'file': rss_file,
            'article_count': article_count
        }

    # 检查探索结果
    for topic in topics:
        safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
        explore_file = os.path.join(output_dir, f'explore_{safe_topic}.md')
        if os.path.exists(explore_file):
            results['explorations'].append({
                'topic': topic,
                'file': explore_file,
                'result_count': 0  # 精确数不重要，文件存在即可
            })

    # 如果没有任何内容，返回None
    if not results['rss'] and not results['explorations']:
        return None

    return results


def _execute_daily_tasks(config: dict, output_dir: str, date_str: str, topics: list) -> dict:
    """执行每日抓取和探索任务"""
    results = {
        'rss': None,
        'explorations': []
    }

    # 1. RSS抓取和总结
    print("\n" + "=" * 80)
    print("步骤 1/2: RSS信息抓取和总结")
    print("=" * 80)
    logging.info("开始RSS抓取...")

    try:
        fetcher = RSSFetcher(
            timeout=config['rss']['timeout'],
            days_back=config['rss']['days_back'],
            fetch_limit=config['rss']['fetch_limit']
        )
        feeds = fetcher.load_feeds(config['rss']['feeds_file'])
        logging.info(f"加载了 {len(feeds)} 个RSS源")

        if feeds:
            articles = fetcher.fetch_all(feeds)
            logging.info(f"抓取完成：共 {len(articles)} 篇文章")

            if articles:
                summarizer = LLMSummarizer(config['llm'])

                if len(articles) > 50 and config['summary'].get('group_by_category', False):
                    summaries = summarizer.summarize_by_category(
                        articles,
                        config['summary'],
                        config['output']['language']
                    )
                    summary = "\n\n".join([
                        f"## {category}\n\n{text}"
                        for category, text in summaries.items()
                    ])
                else:
                    summary = summarizer.summarize_articles(
                        articles,
                        config['summary'],
                        config['output']['language']
                    )

                # 保存到每日目录
                rss_file = os.path.join(output_dir, 'rss_summary.md')
                output_manager = OutputManager(config['output'])
                content = output_manager._format_markdown(summary, articles, date_str)
                with open(rss_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                results['rss'] = {
                    'file': rss_file,
                    'article_count': len(articles)
                }
                print(f"✓ RSS总结已保存: {rss_file}")
                logging.info(f"RSS总结已保存: {rss_file}")
            else:
                print("⚠️  没有抓取到新文章")
                logging.warning("RSS抓取: 没有新文章")
        else:
            print("⚠️  没有找到已分类的RSS源")
            logging.warning("RSS: 没有已分类的源")
    except Exception as e:
        print(f"✗ RSS抓取失败: {str(e)}")
        logging.error(f"RSS抓取失败: {str(e)}", exc_info=True)

    # 2. 主题探索
    print("\n" + "=" * 80)
    print(f"步骤 2/2: 学术论文探索 ({len(topics)} 个主题)")
    print("=" * 80)
    logging.info(f"开始探索 {len(topics)} 个主题...")

    explorer_config = config.get('explorer', {})
    enable_scholar = explorer_config.get('enable_scholar', True)

    explorer = ContentExplorer(
        months_back=explorer_config.get('months_back', 1),
        results_limit=explorer_config.get('results_limit', 10),
        cert_path=explorer_config.get('cert_path'),
        scholar_retry=explorer_config.get('scholar_retry', 3),
        scholar_delay_range=explorer_config.get('scholar_delay_range', [5, 10]),
        enable_scholar=enable_scholar
    )

    summarizer = LLMSummarizer(config['llm'])
    output_manager = OutputManager(config['output'])

    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] 探索主题: {topic}")
        logging.info(f"[{i}/{len(topics)}] 开始探索: {topic}")

        try:
            exploration_data = explorer.explore_topic(topic)

            if exploration_data['total_results'] == 0:
                print(f"  ⚠️  未找到相关内容")
                logging.warning(f"探索 '{topic}': 未找到结果")
                continue

            print(f"  ✓ 找到 {exploration_data['total_results']} 个结果")
            logging.info(f"探索 '{topic}': {exploration_data['total_results']} 个结果")

            summary = summarizer.summarize_exploration(
                exploration_data,
                config['summary'],
                config['output']['language']
            )

            # 保存到每日目录
            safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
            explore_file = os.path.join(output_dir, f'explore_{safe_topic}.md')
            content = output_manager._format_exploration_markdown(summary, exploration_data)
            with open(explore_file, 'w', encoding='utf-8') as f:
                f.write(content)

            results['explorations'].append({
                'topic': topic,
                'file': explore_file,
                'result_count': exploration_data['total_results']
            })
            print(f"  ✓ 已保存: {explore_file}")
            logging.info(f"探索 '{topic}' 已保存: {explore_file}")

        except Exception as e:
            print(f"  ✗ 探索失败: {str(e)}")
            logging.error(f"探索 '{topic}' 失败: {str(e)}", exc_info=True)

    # 3. 生成汇总索引文件
    index_file = os.path.join(output_dir, '00_index.md')
    _generate_daily_index(index_file, date_str, results)
    print(f"\n✓ 汇总索引已生成: {index_file}")
    logging.info(f"汇总索引已生成: {index_file}")

    # 4. 输出总结
    print("\n" + "=" * 80)
    print("每日任务完成")
    print("=" * 80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {output_dir}")

    if results['rss']:
        print(f"  RSS总结: {results['rss']['article_count']} 篇文章")
    print(f"  主题探索: {len(results['explorations'])} 个主题完成")

    logging.info(f"每日任务完成 - RSS: {results['rss'] is not None}, 探索: {len(results['explorations'])}/{len(topics)}")

    return results


def _send_daily_email(config: dict, output_dir: str, date_str: str, results: dict, web_url: str = ""):
    """生成一句话摘要并发送邮件"""
    email_config = config.get('email', {})
    if not email_config.get('enabled', False):
        print("\n邮件功能未启用，跳过发送")
        return

    print("\n" + "=" * 80)
    print("生成精简摘要并发送邮件")
    print("=" * 80)
    logging.info("开始生成精简摘要...")

    try:
        # 收集所有内容用于生成摘要
        all_content = _collect_daily_content(output_dir, results)

        if not all_content:
            print("  ⚠️  没有内容可生成摘要")
            logging.warning("没有内容可生成摘要")
            return

        # 调用LLM生成一句话摘要
        brief_summary = _generate_brief_summary(config, all_content, date_str)
        print(f"  ✓ 精简摘要已生成")
        logging.info(f"精简摘要已生成: {brief_summary[:100]}...")

        # 发送邮件
        notifier = EmailNotifier(email_config)
        recipient = email_config.get('recipient', 'damon.long@merckgroup.com')

        stats = {
            'rss_articles': results['rss']['article_count'] if results['rss'] else 0,
            'exploration_count': len(results['explorations']),
            'web_url': web_url
        }

        success = notifier.send_daily_summary(brief_summary, recipient, date_str, stats)

        if success:
            print(f"  ✓ 邮件已发送至: {recipient}")
            logging.info(f"邮件发送成功: {recipient}")
        else:
            print(f"  ✗ 邮件发送失败，请检查日志")

    except Exception as e:
        print(f"  ✗ 邮件发送流程失败: {str(e)}")
        logging.error(f"邮件发送流程失败: {str(e)}", exc_info=True)


def _collect_daily_content(output_dir: str, results: dict) -> str:
    """收集每日任务的所有内容"""
    content_parts = []

    # 收集RSS摘要
    if results['rss']:
        rss_file = os.path.join(output_dir, 'rss_summary.md')
        if os.path.exists(rss_file):
            with open(rss_file, 'r', encoding='utf-8') as f:
                rss_content = f.read()
                # 只取摘要部分，不要完整文章列表
                if '## 📚 完整文章列表' in rss_content:
                    rss_content = rss_content.split('## 📚 完整文章列表')[0]
                content_parts.append(f"=== RSS摘要 ===\n{rss_content}")

    # 收集探索结果
    for exp in results['explorations']:
        if os.path.exists(exp['file']):
            with open(exp['file'], 'r', encoding='utf-8') as f:
                exp_content = f.read()
                # 只取AI总结部分
                if '## 📄 详细论文列表' in exp_content:
                    exp_content = exp_content.split('## 📄 详细论文列表')[0]
                content_parts.append(f"=== 探索: {exp['topic']} ===\n{exp_content}")

    return "\n\n".join(content_parts)


def _generate_brief_summary(config: dict, all_content: str, date_str: str) -> str:
    """调用LLM生成bullet points格式的精简摘要"""
    summarizer = LLMSummarizer(config['llm'])

    prompt = f"""基于以下今日收集的所有AI研究内容，生成一个简洁的每日摘要。

要求：
1. 使用bullet points格式（每项以"• "开头）
2. 每个bullet point概括一个重要研究方向或发现
3. 每个bullet point控制在20-30字以内
4. 列出3-5个最重要的要点
5. 不要列举具体论文标题，而是概括研究趋势

内容：
{all_content[:8000]}

请直接输出bullet points，不要有其他说明文字。示例格式：
• Agent领域研究热点转向多智能体协作与任务规划
• RAG技术聚焦于检索效率优化与上下文长度扩展
• 多模态模型在视觉理解任务上取得显著进展"""

    summary = summarizer.client.chat.completions.create(
        model=config['llm']['model'],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500
    )

    return summary.choices[0].message.content.strip()


def _generate_daily_index(index_file: str, date_str: str, results: dict):
    """生成每日任务汇总索引文件"""
    content = f"""# 每日信息汇总 - {date_str}

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 快速导航

"""

    if results['rss']:
        content += f"- [RSS信息摘要](rss_summary.html) ({results['rss']['article_count']} 篇文章)\n"

    if results['explorations']:
        for exp in results['explorations']:
            safe_topic = exp['topic'].replace(' ', '_').replace('/', '_')[:50]
            content += f"- [探索: {exp['topic']}](explore_{safe_topic}.html) ({exp['result_count']} 篇论文)\n"

    content += "\n---\n\n"

    if results['rss']:
        content += f"""## RSS信息摘要

- 文章数量: {results['rss']['article_count']}
- 详细内容: [rss_summary.html](rss_summary.html)

---

"""

    if results['explorations']:
        content += "## 学术论文探索\n\n"
        for exp in results['explorations']:
            safe_topic = exp['topic'].replace(' ', '_').replace('/', '_')[:50]
            content += f"""### 探索: {exp['topic']}

- 找到结果: {exp['result_count']} 篇
- 详细内容: [explore_{safe_topic}.html](explore_{safe_topic}.html)

"""

    content += """---

*由RSS聚合助手每日任务自动生成*
"""

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(content)


def _generate_html_files(output_dir: str, results: dict, date_str: str):
    """为所有markdown文件生成对应的HTML版本，方便浏览器直接查看"""
    print("\n" + "=" * 80)
    print("生成HTML版本文件")
    print("=" * 80)
    logging.info("开始生成HTML文件...")

    html_files = []

    # 生成索引页HTML
    index_md = os.path.join(output_dir, '00_index.md')
    if os.path.exists(index_md):
        index_html = os.path.join(output_dir, 'index.html')
        _convert_md_to_html(index_md, index_html, f"每日信息汇总 - {date_str}")
        html_files.append(('index.html', '汇总索引'))
        print(f"  ✓ index.html")
        logging.info(f"生成HTML: index.html")

    # 生成RSS摘要HTML
    rss_md = os.path.join(output_dir, 'rss_summary.md')
    if os.path.exists(rss_md):
        rss_html = os.path.join(output_dir, 'rss_summary.html')
        _convert_md_to_html(rss_md, rss_html, f"RSS信息摘要 - {date_str}")
        html_files.append(('rss_summary.html', 'RSS摘要'))
        print(f"  ✓ rss_summary.html")
        logging.info(f"生成HTML: rss_summary.html")

    # 生成各探索主题HTML
    for exp in results.get('explorations', []):
        safe_topic = exp['topic'].replace(' ', '_').replace('/', '_')[:50]
        explore_md = os.path.join(output_dir, f'explore_{safe_topic}.md')
        if os.path.exists(explore_md):
            explore_html = os.path.join(output_dir, f'explore_{safe_topic}.html')
            _convert_md_to_html(explore_md, explore_html, f"探索: {exp['topic']} - {date_str}")
            html_files.append((f'explore_{safe_topic}.html', exp['topic']))
            print(f"  ✓ explore_{safe_topic}.html")
            logging.info(f"生成HTML: explore_{safe_topic}.html")

    print(f"\n✓ 共生成 {len(html_files)} 个HTML文件")
    logging.info(f"HTML文件生成完成，共 {len(html_files)} 个")


def _convert_md_to_html(md_file: str, html_file: str, title: str):
    """将Markdown文件转换为HTML"""
    import re

    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 简单的Markdown到HTML转换
    html_content = _markdown_to_html(md_content)

    # 获取当前日期
    current_date = datetime.now().strftime('%Y-%m-%d')

    # 完整HTML页面
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #fff;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: .3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: .3em; }}
        h3 {{ font-size: 1.25em; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        code {{
            padding: .2em .4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,.05);
            border-radius: 3px;
        }}
        pre {{
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
        }}
        blockquote {{
            padding: 0 1em;
            color: #6a737d;
            border-left: .25em solid #dfe2e5;
            margin: 0 0 16px 0;
        }}
        table {{
            border-spacing: 0;
            border-collapse: collapse;
            margin-bottom: 16px;
        }}
        table th, table td {{
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }}
        table th {{
            font-weight: 600;
            background: #f6f8fa;
        }}
        table tr:nth-child(2n) {{
            background: #f6f8fa;
        }}
        hr {{
            height: .25em;
            padding: 0;
            margin: 24px 0;
            background-color: #e1e4e8;
            border: 0;
        }}
        ul, ol {{
            padding-left: 2em;
            margin-bottom: 16px;
        }}
        li {{
            margin-bottom: .25em;
        }}
        .nav {{
            background: #f6f8fa;
            padding: 10px 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .nav a {{
            margin-right: 15px;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.html">返回索引</a>
        <a href="rss_summary.html">RSS摘要</a>
    </div>
    <article>
{html_content}
    </article>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">
        由 RSS聚合助手 自动生成 - {current_date}
    </footer>
</body>
</html>"""

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)


def _markdown_to_html(md: str) -> str:
    """简单的Markdown到HTML转换（不依赖外部库）"""
    import re

    html = md

    # 转义HTML特殊字符（但保留我们需要的格式）
    # html = html.replace('&', '&amp;')

    # 代码块
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # 标题
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # 粗体和斜体
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # 引用
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # 水平线
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

    # 无序列表
    def convert_ul(match):
        items = match.group(0)
        items = re.sub(r'^[-•] (.+)$', r'<li>\1</li>', items, flags=re.MULTILINE)
        return f'<ul>\n{items}\n</ul>'

    html = re.sub(r'(^[-•] .+\n?)+', convert_ul, html, flags=re.MULTILINE)

    # 有序列表
    def convert_ol(match):
        items = match.group(0)
        items = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', items, flags=re.MULTILINE)
        return f'<ol>\n{items}\n</ol>'

    html = re.sub(r'(^\d+\. .+\n?)+', convert_ol, html, flags=re.MULTILINE)

    # 段落（连续的非标签行）
    lines = html.split('\n')
    result = []
    in_paragraph = False
    paragraph_content = []

    for line in lines:
        stripped = line.strip()
        # 检查是否是块级元素
        is_block = (stripped.startswith('<') or
                    stripped.startswith('---') or
                    stripped == '')

        if is_block:
            if in_paragraph:
                result.append('<p>' + ' '.join(paragraph_content) + '</p>')
                paragraph_content = []
                in_paragraph = False
            result.append(line)
        else:
            in_paragraph = True
            paragraph_content.append(stripped)

    if in_paragraph:
        result.append('<p>' + ' '.join(paragraph_content) + '</p>')

    return '\n'.join(result)


def schedule_job(config: dict):
    """定时任务模式"""
    import schedule
    import time

    schedule_config = config['schedule']
    run_time = schedule_config['time']

    print(f"定时任务已启动，将在每天 {run_time} 运行")
    print("按 Ctrl+C 停止\n")

    schedule.every().day.at(run_time).do(
        lambda: run_aggregator(config)
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n定时任务已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='RSS AI聚合助手 - 自动抓取并总结AI领域资讯'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='配置文件路径 (默认: config/config.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅抓取RSS内容，不进行LLM总结'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式：仅使用前5个RSS源'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='启动定时任务模式'
    )
    parser.add_argument(
        '--explore',
        action='append',
        metavar='TOPIC',
        help='探索指定主题的学术论文和技术内容（可多次使用）'
    )
    parser.add_argument(
        '--explore-months',
        type=int,
        help='探索模式的时间范围（月）'
    )
    parser.add_argument(
        '--explore-limit',
        type=int,
        help='探索模式每个主题的结果数量限制'
    )
    parser.add_argument(
        '--daily',
        action='store_true',
        help='执行每日全量任务（RSS抓取 + 主题探索）'
    )
    parser.add_argument(
        '--region',
        choices=['cn', 'global'],
        help='区域过滤：cn=国内站点, global=国际站点'
    )

    args = parser.parse_args()

    # 初始化日志系统
    log_file = setup_logging()
    logging.info("="*80)
    logging.info("RSS聚合助手启动")
    logging.info(f"日志文件: {log_file}")
    logging.info("="*80)

    # 加载配置
    try:
        config = load_config(args.config)
        logging.info(f"配置文件加载成功: {args.config}")
    except FileNotFoundError:
        print(f"错误: 配置文件 {args.config} 不存在")
        logging.error(f"配置文件不存在: {args.config}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误: 配置文件格式错误 - {e}")
        logging.error(f"配置文件格式错误: {e}")
        sys.exit(1)

    # 应用命令行参数覆盖配置
    if args.explore_months:
        config['explorer']['months_back'] = args.explore_months
        logging.info(f"命令行参数覆盖: explore_months={args.explore_months}")
    if args.explore_limit:
        config['explorer']['results_limit'] = args.explore_limit
        logging.info(f"命令行参数覆盖: explore_limit={args.explore_limit}")

    # 运行模式选择
    if args.daily:
        logging.info("运行模式: 每日任务")
        run_daily_task(config)
    elif args.explore:
        logging.info(f"运行模式: 内容探索 - 主题: {args.explore}")
        run_explorer(config, args.explore)
    elif args.schedule or config['schedule'].get('enabled', False):
        logging.info("运行模式: 定时任务")
        schedule_job(config)
    else:
        logging.info(f"运行模式: RSS聚合 (dry_run={args.dry_run}, test={args.test}, region={args.region})")
        run_aggregator(config, dry_run=args.dry_run, test_mode=args.test, region=args.region)


if __name__ == '__main__':
    main()
