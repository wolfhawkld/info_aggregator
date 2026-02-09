#!/usr/bin/env python3
"""
RSS聚合助手 - 主程序
自动抓取RSS订阅源，使用LLM生成每日AI摘要
"""

import os
import sys
import yaml
import argparse
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fetcher import RSSFetcher
from summarizer import LLMSummarizer
from output import OutputManager


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

    if not feeds:
        print("错误: 没有找到任何RSS源，请检查配置文件")
        return

    if test_mode:
        print(f"⚠️  测试模式：仅使用前5个源\n")
        feeds = feeds[:5]

    # 3. 抓取文章
    articles = fetcher.fetch_all(feeds)

    if not articles:
        print("\n没有抓取到任何新文章")
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
        summarizer = LLMSummarizer(config['llm'])

        # 根据文章数量选择总结策略
        if len(articles) > 50 and config['summary'].get('group_by_category', False):
            print("文章数量较多，按分类分别总结...")
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
        else:
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
        return

    # 6. 保存和输出
    output_manager = OutputManager(config['output'])

    # 保存到文件
    output_file = output_manager.save_summary(summary, articles)

    # 同时在终端显示
    output_manager.print_summary(summary, articles)

    print(f"\n✅ 完成！摘要已保存到: {output_file}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


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

    args = parser.parse_args()

    # 加载配置
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"错误: 配置文件 {args.config} 不存在")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"错误: 配置文件格式错误 - {e}")
        sys.exit(1)

    # 运行模式选择
    if args.schedule or config['schedule'].get('enabled', False):
        schedule_job(config)
    else:
        run_aggregator(config, dry_run=args.dry_run, test_mode=args.test)


if __name__ == '__main__':
    main()
