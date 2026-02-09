#!/usr/bin/env python3
"""
OPML转换工具
从RSS阅读器导出的OPML文件转换为rss_feeds.txt格式
"""

import xml.etree.ElementTree as ET
import argparse


def parse_opml(opml_file: str, output_file: str):
    """解析OPML文件并生成rss_feeds.txt"""

    tree = ET.parse(opml_file)
    root = tree.getroot()

    feeds = []

    # 查找所有outline元素
    for outline in root.findall('.//outline'):
        xml_url = outline.get('xmlUrl')
        title = outline.get('title') or outline.get('text', '')
        category = outline.get('category', '未分类')

        # 如果有父级分类，使用父级分类
        parent = outline.find('..')
        if parent is not None and parent.tag == 'outline':
            parent_title = parent.get('title') or parent.get('text')
            if parent_title:
                category = parent_title

        if xml_url:
            feeds.append({
                'url': xml_url,
                'title': title,
                'category': category
            })

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# RSS订阅源列表\n")
        f.write("# 从OPML文件自动生成\n\n")

        # 按分类分组
        from collections import defaultdict
        categorized = defaultdict(list)

        for feed in feeds:
            categorized[feed['category']].append(feed)

        for category in sorted(categorized.keys()):
            f.write(f"\n# {category}\n")
            for feed in categorized[category]:
                f.write(f"{feed['url']} [{feed['category']}]  # {feed['title']}\n")

    print(f"✓ 成功转换 {len(feeds)} 个RSS源")
    print(f"✓ 输出文件: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='将OPML文件转换为rss_feeds.txt格式'
    )
    parser.add_argument('opml_file', help='输入的OPML文件')
    parser.add_argument(
        '-o', '--output',
        default='../config/rss_feeds.txt',
        help='输出文件路径 (默认: ../config/rss_feeds.txt)'
    )

    args = parser.parse_args()

    try:
        parse_opml(args.opml_file, args.output)
    except FileNotFoundError:
        print(f"错误: 文件 {args.opml_file} 不存在")
    except ET.ParseError as e:
        print(f"错误: OPML文件格式错误 - {e}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    main()
