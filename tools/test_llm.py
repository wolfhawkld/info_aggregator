#!/usr/bin/env python3
"""
LLM连接测试工具
用于测试LLM API配置是否正确
"""

import os
import sys
import yaml
import argparse

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


def test_llm_connection(config_file=None):
    """测试LLM连接"""

    # 加载配置
    if config_file is None:
        config_file = os.path.join(os.path.dirname(__file__), '../config/config.yaml')

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    llm_config = config['llm']

    print("="*60)
    print("LLM连接测试")
    print("="*60)
    print(f"提供商: {llm_config['provider']}")
    print(f"模型: {llm_config['model']}")

    # 检查API密钥
    api_key = llm_config.get('api_key', '')
    if api_key.startswith('${'):
        env_var = api_key[2:-1]
        api_key = os.getenv(env_var, '')
        print(f"API密钥来源: 环境变量 {env_var}")
    else:
        print(f"API密钥来源: 配置文件")

    if not api_key:
        print("\n❌ 错误: 未找到API密钥")
        print("请设置环境变量或在配置文件中填写API密钥")
        return

    print(f"API密钥: {api_key[:10]}..." if len(api_key) > 10 else "已设置")

    if llm_config.get('base_url'):
        print(f"自定义URL: {llm_config['base_url']}")

    print("\n正在测试连接...")

    try:
        from summarizer import LLMSummarizer

        summarizer = LLMSummarizer(llm_config)

        # 简单测试
        test_articles = [{
            'title': '测试文章',
            'content': '这是一篇用于测试LLM连接的文章。',
            'source': '测试源',
            'category': '测试',
            'link': 'https://example.com'
        }]

        summary = summarizer.summarize_articles(
            test_articles,
            config['summary'],
            'zh'
        )

        print("\n✅ 连接成功!")
        print("\n测试响应:")
        print("-"*60)
        print(summary[:200] + "..." if len(summary) > 200 else summary)
        print("-"*60)

    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        print("\n请检查:")
        print("  1. API密钥是否正确")
        print("  2. 网络连接是否正常")
        print("  3. API服务是否可用")
        print("  4. 如使用代理，检查base_url配置")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='测试LLM API连接')
    parser.add_argument(
        '--config',
        default=None,
        help='配置文件路径 (默认: config/config.yaml)'
    )

    args = parser.parse_args()
    test_llm_connection(args.config)
