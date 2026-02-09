# 🎉 开始使用 - RSS AI聚合助手

## ✅ 已完成的工作

### 1. RSS源转换
- ✅ 已从 `resource/hn-popular-blogs-2025.opml` 转换
- ✅ 成功导入 **92个RSS订阅源**
- ✅ 保存到 `config/rss_feeds.txt`

### 2. Azure OpenAI支持
- ✅ 添加Azure OpenAI provider支持
- ✅ 创建Azure配置模板 `config/config.azure.example.yaml`
- ✅ 更新LLM总结模块以支持Azure endpoint
- ✅ 创建详细的Azure配置指南 `AZURE_SETUP.md`

### 3. 项目结构
```
rss_aggregator/
├── config/
│   ├── config.yaml                    # 主配置（需要你编辑）
│   ├── config.azure.example.yaml     # Azure配置模板
│   └── rss_feeds.txt                 # 92个RSS源（已转换）
├── resource/
│   └── hn-popular-blogs-2025.opml    # 原始OPML文件
├── src/
│   ├── fetcher.py                    # RSS抓取模块
│   ├── summarizer.py                 # LLM总结（支持Azure）
│   └── output.py                     # 输出管理
├── tools/
│   ├── test_llm.py                   # LLM测试工具
│   └── opml_converter.py             # OPML转换工具
├── output/summaries/                  # 生成的摘要存放目录
├── main.py                           # 主程序
├── AZURE_SETUP.md                    # Azure配置详细指南
└── USAGE_GUIDE.md                    # 完整使用指南
```

## 🚀 接下来你需要做什么

### 步骤1: 安装Python依赖

```bash
pip install -r requirements.txt
```

或使用虚拟环境（推荐）：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 步骤2: 配置Azure OpenAI

**方式A: 使用配置模板**

```bash
# 1. 复制Azure配置模板
cp config/config.azure.example.yaml config/config.yaml

# 2. 编辑config/config.yaml，填入你的Azure信息
nano config/config.yaml  # 或使用其他编辑器
```

需要修改的关键配置：
```yaml
llm:
  provider: "azure"
  api_key: "你的Azure-API-Key"
  model: "gpt-51"  # 或你的deployment名称
  base_url: "https://你的资源名.openai.azure.com/"
  api_version: "2024-02-15-preview"
```

**方式B: 使用环境变量（更安全）**

```bash
# 设置环境变量
export AZURE_OPENAI_KEY="your-api-key"

# 配置文件中使用
api_key: "${AZURE_OPENAI_KEY}"
```

**详细配置指南：** 参考 `AZURE_SETUP.md`

### 步骤3: 测试Azure连接

```bash
python tools/test_llm.py
```

期望输出：
```
✅ 连接成功!
测试响应:
------------------------------------------------------------
[LLM生成的测试响应]
------------------------------------------------------------
```

如果失败，查看错误信息并参考 `AZURE_SETUP.md` 的故障排查部分。

### 步骤4: 测试运行（建议）

先用少量源测试，确保一切正常：

```bash
python main.py --test
```

这会仅使用前5个RSS源进行测试。

### 步骤5: 正式运行

```bash
python main.py
```

这会：
1. 从92个RSS源抓取最新文章
2. 使用Azure GPT-5.1生成总结
3. 保存到 `output/summaries/ai_digest_YYYY-MM-DD.md`

## 📖 代码逻辑说明

### 核心流程

```
1. 加载配置 (config/config.yaml)
   ↓
2. 读取RSS源列表 (config/rss_feeds.txt)
   ↓
3. 抓取RSS内容 (src/fetcher.py)
   - 解析RSS feed
   - 过滤最近N天的文章
   - 清理HTML内容
   ↓
4. LLM总结 (src/summarizer.py)
   - 初始化Azure OpenAI客户端
   - 构建提示词
   - 调用GPT-5.1生成总结
   ↓
5. 保存输出 (src/output.py)
   - 生成Markdown文档
   - 按分类组织文章
   - 保存到output目录
```

### 关键模块

#### 1. fetcher.py - RSS抓取器
```python
class RSSFetcher:
    def load_feeds()      # 加载RSS源列表
    def fetch_feed()      # 抓取单个RSS源
    def fetch_all()       # 批量抓取所有源
    def clean_html()      # 清理HTML内容
    def is_recent()       # 过滤时间范围
```

#### 2. summarizer.py - LLM总结器
```python
class LLMSummarizer:
    def _init_client()           # 初始化LLM客户端（支持Azure）
    def summarize_articles()     # 总结文章列表
    def _call_openai()          # 调用OpenAI/Azure API
    def _build_system_prompt()  # 构建系统提示词
    def _build_user_prompt()    # 构建用户提示词
```

**Azure支持要点：**
- 使用 `AzureOpenAI` 类而非 `OpenAI`
- 需要 `azure_endpoint` 和 `api_version` 参数
- API调用接口与OpenAI兼容

#### 3. output.py - 输出管理器
```python
class OutputManager:
    def save_summary()       # 保存总结到文件
    def _format_markdown()   # 生成Markdown格式
    def print_summary()      # 终端打印
```

### 配置参数说明

**RSS抓取配置：**
```yaml
rss:
  fetch_limit: 10   # 每个源最多10篇（92源×10=920篇）
  days_back: 1      # 抓取最近1天的文章
  timeout: 30       # 30秒超时
```

**LLM配置：**
```yaml
llm:
  temperature: 0.3  # 较低=更确定性，较高=更创意
  max_tokens: 2000  # 总结最大长度
```

**总结策略：**
```yaml
summary:
  group_by_category: true  # 按分类分别总结（推荐开启，因为源多）
  summary_style: "concise" # concise=简洁, detailed=详细
```

## 🔍 校验建议

在正式使用前，建议你检查：

### 1. 配置文件检查
```bash
# 查看配置是否正确
cat config/config.yaml

# 查看RSS源数量
wc -l config/rss_feeds.txt  # 应该显示约92行
```

### 2. 代码逻辑检查
```bash
# 查看核心模块
cat src/summarizer.py | grep -A 10 "class LLMSummarizer"
cat src/fetcher.py | grep -A 10 "class RSSFetcher"

# 查看Azure支持
cat src/summarizer.py | grep -B 5 -A 10 "provider == 'azure'"
```

### 3. 测试文件检查
```bash
# 确认RSS源文件存在且有内容
head -20 config/rss_feeds.txt

# 确认输出目录存在
ls -la output/summaries/
```

## ⚙️ 调优建议

根据实际使用情况，你可能需要调整：

### 如果抓取太慢
```yaml
rss:
  fetch_limit: 5    # 减少每源文章数
  timeout: 15       # 减少超时时间
```

### 如果token使用过多
```yaml
rss:
  fetch_limit: 5    # 减少文章数
summary:
  group_by_category: true  # 启用分类总结
llm:
  max_tokens: 1500  # 减少输出长度
```

### 如果需要更详细的总结
```yaml
summary:
  summary_style: "detailed"
llm:
  max_tokens: 3000
  temperature: 0.5
```

## 📚 相关文档

- **Azure配置详解：** `AZURE_SETUP.md`
- **完整使用指南：** `USAGE_GUIDE.md`
- **快速参考：** `README.md`

## 💡 使用技巧

1. **首次运行用 `--test` 模式**，验证配置正确
2. **使用环境变量**存储API密钥，不要硬编码
3. **定期检查RSS源**，移除失效的源
4. **根据需要调整**`fetch_limit`和`days_back`
5. **启用定时任务**，每天自动运行

## 🐛 遇到问题？

1. **查看错误信息**，通常会指明问题所在
2. **参考 `AZURE_SETUP.md`** 的故障排查部分
3. **运行测试工具**：`python tools/test_llm.py`
4. **检查配置文件**格式是否正确（YAML格式对缩进敏感）

## ✅ 检查清单

在正式运行前，确认：

- [ ] Python依赖已安装
- [ ] Azure配置已填写（api_key, model, base_url）
- [ ] RSS源文件存在（92个源）
- [ ] LLM连接测试通过
- [ ] 已用 `--test` 模式测试过
- [ ] 输出目录可写入

全部勾选后，就可以开始使用了！

## 🎯 下一步

```bash
# 正式运行
python main.py

# 或设置定时任务（每天9点自动运行）
python main.py --schedule
```

祝使用愉快！📖✨
