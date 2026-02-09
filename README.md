# RSS AI聚合助手

自动抓取90+个AI领域RSS订阅源，使用LLM生成每日高质量摘要，帮助快速了解AI领域最新动态。

## ✨ 特性

- 📡 支持批量RSS源抓取（90+源）
- 🤖 多种LLM支持（OpenAI/Claude/Ollama）
- 📝 智能分类和内容总结
- 🎯 关键词高亮和重点推荐
- ⏰ 定时任务自动运行
- 📊 多种输出格式（Markdown/JSON/HTML）
- 🌐 支持中英文输出

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置RSS源

编辑 `config/rss_feeds.txt`，添加你的RSS订阅源：

```
https://arxiv.org/rss/cs.AI [论文]
https://arxiv.org/rss/cs.LG [论文]
https://distill.pub/rss.xml [技术博客]
...
```

格式：`URL [可选分类标签]`

### 3. 配置LLM

编辑 `config/config.yaml`，设置你的LLM配置：

**使用OpenAI:**
```yaml
llm:
  provider: "openai"
  api_key: "your-api-key"  # 或设置环境变量 OPENAI_API_KEY
  model: "gpt-4o-mini"
```

**使用Claude:**
```yaml
llm:
  provider: "anthropic"
  api_key: "your-api-key"  # 或设置环境变量 ANTHROPIC_API_KEY
  model: "claude-3-5-sonnet-20241022"
```

**使用本地Ollama:**
```yaml
llm:
  provider: "ollama"
  model: "llama3"
  base_url: "http://localhost:11434/v1"
```

**使用API代理或国内服务:**
```yaml
llm:
  provider: "openai"
  api_key: "your-key"
  base_url: "https://your-proxy-url/v1"  # 如中转API
  model: "gpt-4o-mini"
```

### 4. 运行

**基本运行:**
```bash
python main.py
```

**测试模式（仅5个源）:**
```bash
python main.py --test
```

**仅抓取不总结:**
```bash
python main.py --dry-run
```

**定时任务模式:**
```bash
python main.py --schedule
```

或在配置文件中启用：
```yaml
schedule:
  enabled: true
  time: "09:00"  # 每天9点运行
```

## 📁 项目结构

```
rss_aggregator/
├── config/
│   ├── config.yaml          # 主配置文件
│   └── rss_feeds.txt        # RSS源列表
├── src/
│   ├── fetcher.py          # RSS抓取模块
│   ├── summarizer.py       # LLM总结模块
│   └── output.py           # 输出管理模块
├── output/
│   └── summaries/          # 生成的摘要文件
├── data/                   # 数据缓存（可选）
├── main.py                 # 主程序
├── requirements.txt        # Python依赖
└── README.md              # 本文件
```

## ⚙️ 配置说明

### RSS配置
```yaml
rss:
  feeds_file: "config/rss_feeds.txt"  # RSS源文件
  fetch_limit: 10                      # 每源最多抓取文章数
  days_back: 1                         # 抓取最近N天的文章
  timeout: 30                          # 请求超时（秒）
```

### 总结配置
```yaml
summary:
  group_by_category: true              # 是否按分类分组
  include_original_link: true          # 是否包含原文链接
  summary_style: "concise"             # concise/detailed
  highlight_keywords:                  # 关键词高亮
    - "大模型"
    - "Transformer"
    - "强化学习"
```

### 输出配置
```yaml
output:
  format: "markdown"                   # markdown/json/html
  directory: "output/summaries"        # 输出目录
  filename_template: "ai_digest_{date}.md"  # 文件名模板
  language: "zh"                       # zh/en
```

## 📊 输出示例

生成的Markdown文件格式：

```markdown
# AI每日摘要 - 2024-01-15

> 生成时间: 2024-01-15 09:00:00
> 文章总数: 127

## 🔥 今日要点

1. **大模型推理优化**: 新研究提出了...
2. **多模态进展**: GPT-4V在...
3. **开源工具**: 发布了新的...

## 📑 分类内容

### 论文
- [Attention Is All You Need 2.0](https://arxiv.org)
  核心创新：提出了改进的注意力机制...

### 技术博客
- [如何训练10B参数模型](https://example.com)
  实用指南：详细介绍了...

---

## 📚 完整文章列表
...
```

## 🔧 高级用法

### 环境变量配置

推荐使用环境变量存储API密钥：

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

或创建 `.env` 文件：
```bash
OPENAI_API_KEY=your-key
```

### 定时任务（Cron）

Linux/Mac添加到crontab：
```bash
# 每天早上9点运行
0 9 * * * cd /path/to/rss_aggregator && python main.py
```

Windows使用任务计划程序。

### 自定义提示词

编辑 `src/summarizer.py` 中的 `_build_system_prompt` 和 `_build_user_prompt` 方法来自定义LLM提示词。

## 🐛 故障排查

### API调用失败
1. 检查API密钥是否正确
2. 确认网络连接
3. 验证API额度是否充足
4. 尝试使用代理

### RSS抓取失败
1. 检查RSS URL是否有效
2. 确认网络连接
3. 某些源可能需要代理访问

### 内容为空
1. 调整 `days_back` 参数
2. 增加 `fetch_limit` 限制
3. 检查RSS源是否有更新

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可

MIT License

## 🙏 致谢

- 感谢Andrej Karpathy分享的RSS源列表
- 基于feedparser、OpenAI等优秀开源项目构建
