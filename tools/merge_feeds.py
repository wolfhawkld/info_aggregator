#!/usr/bin/env python3
"""
RSS源整合脚本
将 txt 格式的现有源和 CSV 推荐表整合为统一的 YAML 格式
"""
import csv
import yaml
from pathlib import Path
from typing import Dict, List


def parse_txt_feeds(txt_path: str) -> List[Dict]:
    """解析现有的 txt 格式 RSS 源"""
    feeds = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # 解析格式: URL [分类标签]  # 注释
            parts = line.split('[')
            url = parts[0].strip()
            category = parts[1].split(']')[0].strip() if len(parts) > 1 else '未分类'

            # 提取注释作为名称
            comment = ''
            if '#' in line:
                comment = line.split('#')[1].strip()

            if category != '未分类':
                feeds.append({
                    'url': url,
                    'category': category,
                    'name': comment or url.split('/')[2] if '/' in url else url,
                    'priority': 3,  # 默认优先级
                    'frequency': '未知',
                    'status': 'enabled'
                })

    return feeds


def parse_csv_feeds(csv_path: str) -> List[Dict]:
    """解析 CSV 推荐表"""
    feeds = []
    # 使用 utf-8-sig 自动处理 BOM
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 解析优先级（星级转数字）
            stars = row.get('推荐优先级', '★★★')
            priority = min(stars.count('★'), 5)

            # 解析 URL（去除注释）
            url = row.get('RSS地址', '').strip()
            if '(' in url:
                # 有注释标记，如 "https://xxx (需查证)"
                url = url.split('(')[0].strip()
                status = 'pending'
            else:
                status = 'enabled'

            if not url:
                continue

            # CSV 列名映射（中文列名）
            feeds.append({
                'url': url,
                'category': row.get('类别', '未分类'),
                'name': row.get('RSS源名称', ''),
                'priority': priority,
                'frequency': row.get('更新频率', '未知'),
                'note': row.get('备注', ''),
                'status': status
            })

    return feeds


def merge_feeds(txt_feeds: List[Dict], csv_feeds: List[Dict]) -> List[Dict]:
    """
    合并两个数据源
    规则：以 CSV 为准，txt 中不在 CSV 的源追加
    """
    # 以 URL 为 key 去重
    url_set = set()
    merged = []

    # 先添加 CSV 源（优先）
    for feed in csv_feeds:
        if feed['url'] not in url_set:
            url_set.add(feed['url'])
            merged.append(feed)

    # 再添加 txt 中独有的源
    for feed in txt_feeds:
        if feed['url'] not in url_set:
            url_set.add(feed['url'])
            merged.append(feed)

    return merged


def group_by_category(feeds: List[Dict]) -> Dict[str, List[Dict]]:
    """按分类分组"""
    groups = {}
    for feed in feeds:
        cat = feed.get('category', '未分类')
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(feed)

    # 每个分组内按 priority 降序排序
    for cat in groups:
        groups[cat].sort(key=lambda x: x.get('priority', 3), reverse=True)

    return groups


def generate_yaml(feeds: List[Dict], output_path: str):
    """生成 YAML 配置文件"""
    # 按 category 分组
    grouped = group_by_category(feeds)

    # 构建 YAML 结构
    yaml_data = {
        'meta': {
            'description': 'RSS订阅源配置',
            'last_updated': '2026-03-10',
            'field_descriptions': {
                'priority': '1-5 (5最高)，影响抓取和呈现优先级',
                'frequency': '更新频率，可用于调整抓取策略',
                'status': 'enabled/disabled/pending，控制是否抓取'
            }
        },
        'feeds': feeds  # 保持排序后的列表
    }

    # 写入 YAML 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✓ 已生成 YAML 配置: {output_path}")
    print(f"  总源数: {len(feeds)}")
    print(f"  分类数: {len(grouped)}")


def print_summary(feeds: List[Dict]):
    """打印整合摘要"""
    grouped = group_by_category(feeds)

    print("\n" + "="*50)
    print("RSS源整合摘要")
    print("="*50)

    for cat, items in sorted(grouped.items()):
        print(f"\n[{cat}] - {len(items)} 个源")
        for feed in items:
            status_icon = '✓' if feed.get('status') == 'enabled' else '⚠' if feed.get('status') == 'pending' else '✗'
            print(f"  {status_icon} [{feed.get('priority', 3)}★] {feed.get('name', feed['url'][:40])}")


def main():
    # 路径配置
    base_path = Path(__file__).parent.parent
    txt_path = base_path / 'config' / 'rss_feeds.txt'
    csv_path = base_path / 'resource' / 'RSS_Feeds_Recommendation_Table.csv'
    output_path = base_path / 'config' / 'feeds.yaml'

    print("开始整合 RSS 源...")
    print(f"  TXT 源: {txt_path}")
    print(f"  CSV 源: {csv_path}")

    # 解析两个数据源
    txt_feeds = parse_txt_feeds(txt_path)
    csv_feeds = parse_csv_feeds(csv_path)

    print(f"\n  TXT 已分类源: {len(txt_feeds)}")
    print(f"  CSV 推荐源: {len(csv_feeds)}")

    # 合并
    merged = merge_feeds(txt_feeds, csv_feeds)
    print(f"  合并后: {len(merged)}")

    # 打印摘要
    print_summary(merged)

    # 生成 YAML
    generate_yaml(merged, output_path)


if __name__ == '__main__':
    main()