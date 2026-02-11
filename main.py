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


def run_aggregator(config: dict, dry_run: bool = False, test_mode: bool = False):
    """
    运行RSS聚合流程

    Args:
        config: 配置字典
        dry_run: 仅抓取不总结
        test_mode: 测试模式（限制源数量）
    """
    print("="*80)
    print("RSS AI聚合助手")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 初始化抓取器
    fetcher = RSSFetcher(
        timeout=config['rss']['timeout'],
        days_back=config['rss']['days_back'],
        fetch_limit=config['rss']['fetch_limit']
    )

    # 2. 加载RSS源
    feeds = fetcher.load_feeds(config['rss']['feeds_file'])
    logging.info(f"加载了 {len(feeds)} 个RSS源")

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
    if args.explore:
        logging.info(f"运行模式: 内容探索 - 主题: {args.explore}")
        run_explorer(config, args.explore)
    elif args.schedule or config['schedule'].get('enabled', False):
        logging.info("运行模式: 定时任务")
        schedule_job(config)
    else:
        logging.info(f"运行模式: RSS聚合 (dry_run={args.dry_run}, test={args.test})")
        run_aggregator(config, dry_run=args.dry_run, test_mode=args.test)


if __name__ == '__main__':
    main()
