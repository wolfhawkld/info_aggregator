# RSS AI聚合助手 - 详细使用指南

## 📋 目录
1. [快速开始](#快速开始)
2. [配置Karpathy的RSS源](#配置karpathy的rss源)
3. [LLM配置详解](#llm配置详解)
4. [高级功能](#高级功能)
5. [常见问题](#常见问题)

## 快速开始

### 第一步：安装依赖

```bash
# 方式1: 直接安装
pip install -r requirements.txt

# 方式2: 使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 第二步：添加RSS源

你有90+个Karpathy推荐的RSS源，可以通过以下方式添加：

**方式1: 手动添加到 `config/rss_feeds.txt`**

```text
# AI论文
https://arxiv.org/rss/cs.AI [论文]
https://arxiv.org/rss/cs.LG [论文]
https://arxiv.org/rss/cs.CL [论文]

# 技术博客
https://distill.pub/rss.xml [技术博客]
https://lilianweng.github.io/feed.xml [技术博客]

# 研究机构
https://openai.com/blog/rss/ [行业动态]
https://www.anthropic.com/rss [行业动态]
https://ai.googleblog.com/feeds/posts/default [行业动态]

# 添加你的其他80+个源...
```

**方式2: 从OPML文件导入**

如果你的RSS源是从Feedly等阅读器导出的OPML格式：

```bash
python tools/opml_converter.py your_feeds.opml -o config/rss_feeds.txt
```

### 第三步：配置LLM

编辑 `config/config.yaml`，选择你的LLM方案：

**推荐方案A: OpenAI GPT-4o-mini（性价比高）**

```yaml
llm:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"  # 从环境变量读取
  model: "gpt-4o-mini"  # 或 gpt-4o
  temperature: 0.3
  max_tokens: 2000
```

然后设置环境变量：
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**推荐方案B: 使用国内API代理（解决网络问题）**

```yaml
llm:
  provider: "openai"
  api_key: "your-key"
  base_url: "https://api.example.com/v1"  # 你的代理地址
  model: "gpt-4o-mini"
```

**推荐方案C: 本地运行Ollama（完全免费）**

首先安装并启动Ollama:
```bash
# 安装Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull llama3

# 启动服务（默认会自动启动）
ollama serve
```

然后配置：
```yaml
llm:
  provider: "ollama"
  model: "llama3"  # 或 qwen, mistral等
  base_url: "http://localhost:11434/v1"
```

### 第四步：测试连接

```bash
python tools/test_llm.py
```

如果看到"✅ 连接成功!"，说明配置正确。

### 第五步：首次运行

**测试模式（仅5个源）：**
```bash
python main.py --test
```

**正式运行：**
```bash
python main.py
```

输出文件会保存在 `output/summaries/` 目录。

## 配置Karpathy的RSS源

Andrej Karpathy推荐的RSS源主要包括这些类别：

### 1. 学术论文源

```text
# arXiv主要分类
https://arxiv.org/rss/cs.AI [论文-AI]
https://arxiv.org/rss/cs.LG [论文-机器学习]
https://arxiv.org/rss/cs.CL [论文-NLP]
https://arxiv.org/rss/cs.CV [论文-计算机视觉]
https://arxiv.org/rss/cs.NE [论文-神经网络]
https://arxiv.org/rss/stat.ML [论文-统计ML]
```

### 2. 研究博客

```text
# 个人技术博客
https://lilianweng.github.io/feed.xml [技术博客]
https://colah.github.io/rss.xml [技术博客]
https://karpathy.github.io/feed.xml [技术博客]
https://distill.pub/rss.xml [技术博客]

# 研究组博客
https://ai.stanford.edu/blog/feed.xml [研究博客]
https://bair.berkeley.edu/blog/feed.xml [研究博客]
```

### 3. 产业动态

```text
https://openai.com/blog/rss/ [产业-OpenAI]
https://www.anthropic.com/rss [产业-Anthropic]
https://ai.googleblog.com/feeds/posts/default [产业-Google]
https://engineering.fb.com/feed/ [产业-Meta]
https://www.deepmind.com/blog/rss.xml [产业-DeepMind]
```

### 4. 技术社区

```text
https://huggingface.co/blog/feed.xml [开源社区]
https://blog.tensorflow.org/feeds/posts/default [框架]
https://pytorch.org/blog/feed.xml [框架]
```

### 完整示例

可以创建一个包含所有90+源的完整列表，按分类组织。

## LLM配置详解

### OpenAI配置

**基础配置:**
```yaml
llm:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o-mini"  # 推荐：性价比最高
```

**可选模型:**
- `gpt-4o-mini`: 最便宜，速度快，适合日常使用
- `gpt-4o`: 最强性能，适合重要总结
- `gpt-3.5-turbo`: 便宜但效果一般

**使用API代理:**
```yaml
llm:
  provider: "openai"
  api_key: "your-key"
  base_url: "https://api.your-proxy.com/v1"
  model: "gpt-4o-mini"
```

### Anthropic Claude配置

```yaml
llm:
  provider: "anthropic"
  api_key: "${ANTHROPIC_API_KEY}"
  model: "claude-3-5-sonnet-20241022"  # 最新模型
```

**可选模型:**
- `claude-3-5-sonnet-20241022`: 最强综合能力
- `claude-3-haiku-20240307`: 最快速度

### 本地Ollama配置

```yaml
llm:
  provider: "ollama"
  model: "llama3"
  base_url: "http://localhost:11434/v1"
```

**推荐模型:**
- `llama3`: Meta开源，综合性能好
- `qwen2:7b`: 阿里通义千问，中文优秀
- `mistral`: 欧洲开源，效率高

下载模型：
```bash
ollama pull llama3
ollama pull qwen2:7b
ollama pull mistral
```

### 国内LLM服务

**通义千问/文心一言等:**

大多数国内服务都兼容OpenAI API格式：

```yaml
llm:
  provider: "openai"
  api_key: "your-key"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问
  model: "qwen-max"
```

## 高级功能

### 1. 自定义总结风格

编辑 `config/config.yaml`:

```yaml
summary:
  summary_style: "detailed"  # concise: 简洁, detailed: 详细
  highlight_keywords:        # 重点关注的关键词
    - "大模型"
    - "Agent"
    - "你关心的主题"
```

### 2. 按分类分别总结

当文章数量很多（50+）时，可以按分类分别总结：

```yaml
summary:
  group_by_category: true
```

### 3. 定时任务

**方式1: 内置调度器**

```yaml
schedule:
  enabled: true
  time: "09:00"  # 每天9点
```

然后运行：
```bash
python main.py --schedule
```

**方式2: Crontab (Linux/Mac)**

```bash
crontab -e

# 添加以下行（每天9点）
0 9 * * * cd /path/to/rss_aggregator && /path/to/venv/bin/python main.py
```

**方式3: Windows任务计划程序**

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天9:00
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`main.py`
   - 起始于：项目目录

### 4. 多种输出格式

**Markdown（默认）:**
```yaml
output:
  format: "markdown"
  filename_template: "ai_digest_{date}.md"
```

**JSON（方便程序处理）:**
```yaml
output:
  format: "json"
  filename_template: "ai_digest_{date}.json"
```

**HTML（可在浏览器查看）:**
```yaml
output:
  format: "html"
  filename_template: "ai_digest_{date}.html"
```

### 5. 调整抓取策略

```yaml
rss:
  fetch_limit: 20      # 增加每源文章数
  days_back: 2         # 抓取最近2天
  timeout: 60          # 增加超时时间
```

### 6. 自定义提示词

编辑 `src/summarizer.py` 的 `_build_system_prompt` 方法，可以完全自定义LLM的行为。

例如，让LLM更关注实现细节：

```python
def _build_system_prompt(self, config: Dict, language: str) -> str:
    if language == 'zh':
        prompt = """你是AI工程师。总结时请：
1. 重点关注技术实现细节和代码
2. 标注论文的GitHub仓库链接
3. 评估技术的实用性和可复现性"""
    return prompt
```

## 常见问题

### Q1: API调用失败

**现象:** `LLM调用失败: Connection error`

**解决:**
1. 检查网络连接
2. 确认API密钥正确
3. 尝试使用代理或本地Ollama
4. 检查API额度是否充足

### Q2: RSS源抓取失败

**现象:** `抓取失败: timeout`

**解决:**
1. 检查RSS URL是否有效（浏览器访问测试）
2. 增加timeout设置
3. 某些源可能需要代理
4. 可能是临时网络问题，稍后重试

### Q3: 抓取到的文章为空

**现象:** `没有抓取到任何新文章`

**解决:**
1. 增加 `days_back` 参数（如改为7天）
2. 检查RSS源是否有最近更新
3. 有些论文源更新较慢

### Q4: 总结质量不好

**解决:**
1. 更换更强的模型（如gpt-4o）
2. 调整temperature（降低可提高稳定性）
3. 自定义提示词
4. 检查文章内容是否被正确抓取

### Q5: 成本控制

**使用OpenAI的成本估算:**
- 90个源，每源10篇 = 约900篇
- 每篇平均500 tokens内容
- 每次总结约：450K input tokens + 2K output tokens
- gpt-4o-mini成本：约$0.08每次
- 每月约$2.4（每天一次）

**省钱建议:**
1. 使用 `fetch_limit: 5` 减少文章数
2. 使用 `gpt-4o-mini` 而非 `gpt-4o`
3. 使用免费的Ollama本地模型
4. 按分类总结，每次只总结感兴趣的分类

### Q6: 文章内容太长

**现象:** Token超限

**解决:**
```yaml
summary:
  group_by_category: true  # 启用分类总结

rss:
  fetch_limit: 5           # 减少每源文章数
```

## 最佳实践

1. **首次使用**: 用 `--test` 模式测试，确认一切正常
2. **调整配置**: 根据实际情况调整 `fetch_limit` 和 `days_back`
3. **定期维护**: 定期检查RSS源是否失效，清理无效源
4. **关键词定制**: 根据研究方向设置 `highlight_keywords`
5. **成本控制**: 监控API使用量，必要时切换到本地模型

## 更多帮助

- 查看 `README.md` 了解基础功能
- 检查 `config/config.yaml` 中的注释
- 运行 `python main.py --help` 查看所有选项
