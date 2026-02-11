# RSS聚合器项目 - 长期开发记忆

> **最后更新**: 2026-02-10
> **当前版本**: v1.1.2
> **代码规模**: 1214行核心代码
> **状态**: 功能完整，生产可用，企业网络兼容，日志完善，支持源分类过滤

---

## 📋 项目快照

**项目类型**: 命令行工具 - RSS AI聚合助手
**核心功能**: 自动抓取92个技术博客RSS订阅源，使用LLM生成智能摘要
**技术栈**: Python 3 + feedparser + LLM API (OpenAI/Azure/Claude/Ollama)

---

## 🏗️ 核心架构

```
工作流程1 (RSS聚合):
RSS源列表 → RSSFetcher(抓取) → LLMSummarizer(总结) → OutputManager(输出) → Markdown/JSON/HTML

工作流程2 (内容探索):
用户主题 → ContentExplorer(搜索) → LLMSummarizer(总结) → OutputManager(输出) → Markdown
```

### 四大核心模块

| 模块 | 文件 | 行数 | 主要功能 |
|------|------|------|---------|
| **RSS抓取器** | `src/fetcher.py` | 191 | 抓取、清理HTML、时间过滤、分类过滤 |
| **内容探索器** | `src/explorer.py` | 178 | arXiv/Scholar搜索、结果聚合、SSL证书自动修复 |
| **LLM总结器** | `src/summarizer.py` | 292 | 支持4种LLM、智能分组总结、学术分析 |
| **输出管理器** | `src/output.py` | 246 | Markdown/JSON/HTML输出、探索结果格式化 |

---

## ✅ 已实现功能清单

### 1. RSS抓取功能
- [x] 90个RSS源配置（当前5个已分类）
- [x] **分类过滤功能** - 只抓取已分类的高质量源（v1.1.2新增）
- [x] HTML内容自动清理（BeautifulSoup）
- [x] 时间范围过滤（默认最近1天）
- [x] 每源文章数量限制（默认10篇）
- [x] 自动分类标记
- [x] 错误容错处理（单源失败不影响其他）
- [x] 请求速率控制（0.5秒延迟）
- [x] 详细加载统计和日志（v1.1.2增强）

### 2. LLM智能总结
- [x] **Azure OpenAI** 支持（当前使用）
- [x] **OpenAI** 支持（GPT-4、GPT-4o系列）
- [x] **Anthropic Claude** 支持（Claude-3系列）
- [x] **Ollama** 本地模型支持（llama3、qwen等）
- [x] 按分类分组总结（避免Token超限）
- [x] 中英文双语支持
- [x] 关键词高亮功能
- [x] 简洁/详细模式切换
- [x] 自定义提示词

### 3. 输出管理
- [x] Markdown格式输出（默认）
- [x] JSON格式输出
- [x] HTML格式输出
- [x] 自动创建输出目录
- [x] 文件名日期模板
- [x] 终端彩色输出

### 4. 运行模式
- [x] 正常模式（完整流程）
- [x] 测试模式（仅5个源）
- [x] Dry-run模式（只抓取不总结）
- [x] 定时任务模式（后台定时运行）

### 5. 内容探索功能（v1.1新增）
- [x] **arXiv论文搜索** - 按关键词搜索最新学术论文，支持精确时间过滤
- [x] **Google Scholar搜索** - 覆盖更广泛的学术文献（v1.1.2修复：移除不合理的时间过滤）
- [x] **时间范围过滤** - arXiv支持精确日期过滤（1个月/3个月/1年等）
- [x] **多主题并行探索** - 一次命令探索多个主题
- [x] **智能学术总结** - LLM分析研究趋势和创新点
- [x] **独立输出管理** - 独立目录和文件名模板
- [x] **防限流机制** - 自动延迟避免被封禁
- [x] **完整元数据** - 作者、日期、链接、PDF、引用数
- [x] **详细日志记录** - 搜索过程、结果统计全程可追溯（v1.1.2增强）

### 6. 辅助工具
- [x] LLM连接测试工具（`tools/test_llm.py`）
- [x] OPML转换工具（`tools/opml_converter.py`）
- [x] 快速启动脚本（`run.sh`）

---

## ⚙️ 当前配置（2026-02-10）

### LLM配置
```yaml
provider: azure
model: gpt-51
base_url: https://api.nlp.dev.uptimize.merckgroup.com
api_version: 2025-11-13
temperature: 0.3
max_tokens: 8000
```

### RSS配置
```yaml
feeds_file: config/rss_feeds.txt  # 90个源配置，当前5个已分类被加载
fetch_limit: 10                    # 每源10篇
days_back: 1                       # 最近1天
timeout: 30                        # 30秒超时
# 注：v1.1.2起只加载分类不是"未分类"的源
```

### 输出配置
```yaml
format: markdown
directory: output/summaries
filename_template: ai_digest_{date}.md
language: zh
```

---

## 📁 关键文件位置索引

### 核心代码
- **主程序入口**: `main.py:1-263`
- **RSS抓取类**: `src/fetcher.py:26` → `RSSFetcher`
- **内容探索类**: `src/explorer.py:12` → `ContentExplorer` (v1.1新增)
- **LLM总结类**: `src/summarizer.py:15` → `LLMSummarizer`
  - `summarize_articles()`: RSS文章总结
  - `summarize_exploration()`: 学术论文总结 (v1.1新增)
- **输出管理类**: `src/output.py:12` → `OutputManager`
  - `save_summary()`: RSS摘要输出
  - `save_exploration()`: 探索结果输出 (v1.1新增)

### 配置文件
- **主配置**: `config/config.yaml`
- **RSS源列表**: `config/rss_feeds.txt` (92行)
- **Azure配置示例**: `config/config.azure.example.yaml`
- **环境变量示例**: `.env.example`

### 工具脚本
- **LLM测试**: `tools/test_llm.py:1-101`
- **OPML转换**: `tools/opml_converter.py:1-85`

### 文档
- **项目说明**: `README.md`
- **详细指南**: `USAGE_GUIDE.md`
- **快速开始**: `GETTING_STARTED.md`
- **Azure配置**: `AZURE_SETUP.md`
- **开发记忆**: `CLAUDE.md`（本文件）

---

## 🎯 优化和扩展建议

### 🟢 短期优化（易实现，1-2天）

#### 1. 添加单元测试 ⭐⭐⭐
**优先级**: 高
**原因**: 提升代码可靠性，方便重构
**实现建议**:
```python
# tests/test_fetcher.py
def test_clean_html()
def test_is_recent()
def test_fetch_feed()

# tests/test_summarizer.py
def test_init_client()
def test_summarize_articles()

# tests/test_output.py
def test_save_summary()
```

#### 2. 增量更新机制 ⭐⭐⭐
**优先级**: 高
**原因**: 避免重复抓取，节省API成本
**实现建议**:
- 使用SQLite存储已处理文章的URL/GUID
- 抓取前检查是否已存在
- 添加`--force-refresh`选项强制重新抓取

#### 3. RSS源健康检查 ⭐⭐
**优先级**: 中
**原因**: 监控失败的源，及时发现问题
**实现建议**:
```python
# tools/check_feeds.py
- 遍历所有RSS源
- 记录响应时间和状态
- 生成健康报告
- 发送告警邮件
```

#### 4. 错误恢复机制 ⭐⭐
**优先级**: 中
**原因**: 处理网络中断、API超时
**实现建议**:
- 添加重试机制（exponential backoff）
- 保存中间结果（断点续传）
- 添加日志记录

#### 5. 多语言RSS支持 ⭐
**优先级**: 低
**原因**: 扩展信息源
**实现建议**:
- 自动检测文章语言
- 调用翻译API
- 双语输出

---

### 🟡 中期扩展（需一定开发，1-2周）

#### 6. SQLite数据库持久化 ⭐⭐⭐
**优先级**: 高
**原因**: 历史追踪、去重、统计分析
**数据表设计**:
```sql
-- articles表
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    guid TEXT UNIQUE,
    title TEXT,
    link TEXT,
    content TEXT,
    author TEXT,
    published TIMESTAMP,
    source TEXT,
    category TEXT,
    fetched_at TIMESTAMP,
    processed BOOLEAN
);

-- feeds表
CREATE TABLE feeds (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    category TEXT,
    last_fetch TIMESTAMP,
    status TEXT,
    error_count INTEGER
);

-- summaries表
CREATE TABLE summaries (
    id INTEGER PRIMARY KEY,
    date DATE,
    content TEXT,
    article_count INTEGER,
    llm_provider TEXT,
    created_at TIMESTAMP
);
```

#### 7. Web界面 ⭐⭐⭐
**优先级**: 高
**原因**: 提升用户体验
**技术选型**:
- 后端: Flask/FastAPI
- 前端: Vue.js/React
- 功能:
  - 查看历史摘要
  - 管理RSS源
  - 配置LLM参数
  - 手动触发任务
  - 统计分析图表

#### 8. 邮件推送功能 ⭐⭐
**优先级**: 中
**原因**: 主动推送，提高阅读率
**实现建议**:
```python
# src/notifier.py
class EmailNotifier:
    def send_digest(summary, recipients)
    def format_email_template()
```

#### 9. 关键词订阅 ⭐⭐
**优先级**: 中
**原因**: 个性化推荐
**实现建议**:
- 用户配置关注关键词
- 文章匹配关键词后高亮
- 生成个性化摘要

#### 10. 多用户支持 ⭐
**优先级**: 低
**原因**: 多人使用
**实现建议**:
- 用户认证系统
- 独立的RSS源配置
- 个人订阅偏好

---

### 🔴 长期升级（架构级改进，1个月+）

#### 11. 分布式抓取 ⭐⭐
**技术方案**:
- Celery + Redis队列
- 多Worker并发抓取
- 任务调度和监控

#### 12. 实时推送 ⭐
**技术方案**:
- WebSocket连接
- 实时文章更新
- 桌面通知

#### 13. 移动端应用 ⭐
**技术方案**:
- React Native/Flutter
- 离线缓存
- 推送通知

#### 14. AI问答系统（RAG） ⭐⭐⭐
**技术方案**:
- 向量数据库（Pinecone/Weaviate）
- 文章内容embedding
- 基于历史文章的智能问答
```python
用户: "最近有哪些关于Transformer的创新？"
系统: 检索相关文章 → 生成回答
```

#### 15. 社区共享功能 ⭐
**技术方案**:
- 用户可分享RSS源列表
- 点赞和评论
- 热门源推荐

---

## 🚨 开发注意事项

### 代码风格
- 避免过度工程化
- 只添加必要的功能
- 保持代码简洁
- 不要添加不必要的注释和docstring

### 安全性
- 注意防范命令注入、XSS、SQL注入
- API密钥不要硬编码
- 使用环境变量管理敏感信息

### 错误处理
- RSS抓取失败时继续处理其他源
- API调用异常时返回错误信息
- 日期解析失败时使用默认值

### 性能优化
- 源间请求延迟0.5秒（避免被封）
- HTML内容限制1000字（减少Token）
- 按分类分组总结（避免超限）

### 测试策略
- 使用`--test`模式快速验证
- 使用`--dry-run`测试RSS抓取
- 使用`tools/test_llm.py`测试LLM连接

---

## 📊 项目优势

✅ **多LLM支持** - Azure、OpenAI、Claude、Ollama灵活切换
✅ **智能成本优化** - 分类分组、本地模型、内容限制
✅ **灵活配置** - YAML、环境变量、命令行选项
✅ **完善文档** - 4个详细文档，易于上手
✅ **轻量级设计** - 无数据库、纯文件输出
✅ **企业级集成** - 支持Azure OpenAI
✅ **主动探索能力** - 不局限于RSS源，可搜索任意主题学术内容（v1.1新增）
✅ **双模式运行** - RSS被动聚合 + 主动内容探索（v1.1新增）
✅ **完善日志系统** - 文件+控制台双输出，覆盖关键流程和异常（v1.1.1新增）
✅ **RSS源质量管理** - 分类过滤机制，只抓取精选高质量源（v1.1.2新增）

---

## 🔍 项目弱点

⚠️ **缺乏测试覆盖** - 无单元测试和集成测试
⚠️ **无Web界面** - 仅命令行操作
⚠️ **无数据库** - 难以追踪历史、去重
⚠️ **错误恢复有限** - 网络中断处理不足
⚠️ **无用户系统** - 单用户设计

---

## 📝 历史快照

### 2026-02-09 生成的输出
- 文件: `output/summaries/ai_digest_2026-02-09.md`
- 大小: 912KB
- 文章数: 818篇
- 内容: 详细分类总结 + 完整文章列表

### 2026-02-10 项目分析
- 完成项目完整功能分析
- 创建长期开发记忆文档
- 提出优化和扩展建议

### 2026-02-10 新增探索功能
- **功能**: 学术论文和技术内容探索模块
- **数据源**: arXiv + Google Scholar
- **新增文件**: `src/explorer.py` (178行)
- **修改文件**: `main.py`, `src/summarizer.py`, `src/output.py`, `config/config.yaml`
- **命令示例**: `python main.py --explore "Transformer优化"`
- **输出位置**: `output/explorations/`
- **SSL修复**: 企业网络环境自签名证书问题已解决（自动安装到certifi）

### 2026-02-10 Bug修复和日志系统 (v1.1.1)
- **修复1**: scholarly搜索结果无法正常显示 - 修复tuple/list类型不匹配问题
- **修复2**: 添加arXiv搜索链接到输出文件，方便查看完整结果
- **新增**: 完整的日志系统 - 文件+控制台双输出
- **日志位置**: `logs/rss_aggregator_YYYYMMDD.log`
- **修改文件**: `src/explorer.py`, `src/output.py`, `main.py`
- **影响**: 所有关键流程现在都有详细日志记录

### 2026-02-10 Scholar时间过滤修复和RSS源分类过滤 (v1.1.2)
- **修复**: Google Scholar时间过滤导致返回0结果 - 移除年份过滤逻辑
- **原因**: Scholar只有年份信息，精确日期比较不合理
- **新增**: RSS源分类过滤功能 - 只加载已分类的高质量源
- **当前状态**: 90个源中5个已分类被加载，85个未分类被跳过
- **修改文件**: `src/explorer.py`, `src/fetcher.py`
- **日志增强**: RSS加载过程添加详细统计和调试日志

---

## 🎓 技术债务清单

1. **添加pytest单元测试框架** - 覆盖核心功能
2. **实现SQLite数据库** - 替换纯文件存储
3. ~~**添加日志系统**~~ - ✅ 已完成 (v1.1.1)
4. **实现重试机制** - tenacity库处理临时失败
5. **添加性能监控** - 记录抓取时间、API耗时
6. **代码重构** - 提取重复代码、优化结构
7. **添加CI/CD** - GitHub Actions自动测试

---

## 💡 增量开发策略

### 阶段1: 基础完善（第1-2周）
1. 添加单元测试
2. 实现SQLite数据库
3. 添加增量更新机制
4. 完善错误处理

### 阶段2: 功能扩展（第3-4周）
5. 开发Web界面（Flask + Vue.js）
6. 添加邮件推送
7. 实现RSS源健康检查
8. 添加关键词订阅

### 阶段3: 高级功能（第5-8周）
9. 实现分布式抓取
10. 开发AI问答系统（RAG）
11. 添加实时推送
12. 开发移动端应用

---

## 🔗 相关资源

### 依赖库文档
- **feedparser**: https://feedparser.readthedocs.io/
- **OpenAI API**: https://platform.openai.com/docs/
- **Anthropic API**: https://docs.anthropic.com/
- **BeautifulSoup**: https://www.crummy.com/software/BeautifulSoup/
- **arxiv**: https://github.com/lukasschwab/arxiv.py (v1.1新增)
- **scholarly**: https://github.com/scholarly-python-package/scholarly (v1.1新增)

### 参考项目
- **RSSHub**: https://github.com/DIYgod/RSSHub
- **Miniflux**: https://github.com/miniflux/v2
- **Feedbin**: https://github.com/feedbin/feedbin

---

## 📞 维护联系

**最后更新**: 2026-02-10
**更新人**: Claude Code
**下次审查**: 根据开发进度更新

---

## 🆕 更新日志

### 版本 v1.1 - 2026-02-10

#### 新增功能：内容探索模块

**背景**：用户需要主动探索指定兴趣方向的SOTA论文和技术内容，而不局限于现有RSS源。

**实现内容**：

1. **新增核心模块** `src/explorer.py` (178行代码)
   - `ContentExplorer` 类：内容探索器
   - `search_arxiv()`: 搜索arXiv学术论文
   - `search_scholar()`: 搜索Google Scholar论文
   - `explore_topic()`: 聚合多源搜索结果
   - `_setup_ssl_cert()`: 自动检测并修复企业网络SSL证书问题

2. **扩展 LLM 总结器** `src/summarizer.py`
   - 新增 `summarize_exploration()` 方法
   - 专门针对学术论文的总结提示词
   - 支持研究趋势分析、重点论文解读

3. **扩展输出管理器** `src/output.py`
   - 新增 `save_exploration()` 方法
   - 新增 `_format_exploration_markdown()` 格式化函数
   - 独立的探索结果输出目录和格式

4. **主程序集成** `main.py`
   - 新增 `run_explorer()` 函数
   - 新增命令行参数：
     - `--explore TOPIC`: 探索主题（可多次使用）
     - `--explore-months N`: 时间范围（月）
     - `--explore-limit N`: 结果数量限制

5. **配置文件扩展** `config/config.yaml`
   ```yaml
   explorer:
     enabled: true
     months_back: 1
     results_limit: 10
     results_per_source:
       arxiv: 4
       scholar: 3
     output_directory: "output/explorations"
     filename_template: "explore_{topic}_{date}.md"
   ```

6. **依赖更新** `requirements.txt`
   - 新增：`arxiv>=2.1.0`
   - 新增：`scholarly>=1.7.0`
   - 使用：`certifi>=2023.0.0`（SSL证书管理）

7. **SSL证书修复** `certs/`
   - 下载arXiv完整证书链
   - 自动安装到certifi证书库
   - 解决企业网络自签名证书问题

**功能特点**：

✅ **独立命令模式** - 不影响现有RSS聚合流程
✅ **多数据源** - arXiv（快速稳定）+ Google Scholar（覆盖全面）
✅ **灵活配置** - 命令行参数可覆盖配置文件
✅ **智能总结** - LLM分析研究趋势和技术创新点
✅ **完整元数据** - 包含作者、日期、链接、PDF、引用数等
✅ **防限流机制** - 内置请求延迟，避免被封禁
✅ **企业网络兼容** - 自动检测并修复SSL证书问题

**使用示例**：

```bash
# 单主题探索
python main.py --explore "Transformer优化技术"

# 多主题探索
python main.py --explore "RAG optimization" --explore "vision transformer"

# 自定义参数
python main.py --explore "LLM reasoning" --explore-months 3 --explore-limit 15
```

**输出示例**：

文件位置：`output/explorations/explore_Transformer优化技术_2026-02-10.md`

包含内容：
- AI智能总结（研究趋势、重点论文、技术创新点）
- arXiv论文详细列表（标题、作者、摘要、PDF链接）
- Google Scholar论文列表（标题、作者、引用数、链接）

**技术细节**：

| 模块 | 修改类型 | 代码行数 | 主要改动 |
|------|---------|---------|---------|
| `src/explorer.py` | 新增 | 178 | ContentExplorer类，arXiv/Scholar搜索，SSL证书自动修复 |
| `src/summarizer.py` | 扩展 | +75 | summarize_exploration方法 |
| `src/output.py` | 扩展 | +98 | save_exploration方法 |
| `main.py` | 扩展 | +75 | run_explorer函数，命令行参数 |
| `config/config.yaml` | 扩展 | +10 | explorer配置块，cert_path配置 |
| `certs/` | 新增 | 2文件 | arxiv_cert.pem, arxiv_fullchain.pem |

**注意事项**：

⚠️ **Google Scholar限流风险** - scholarly库可能被限流，已内置2秒延迟
⚠️ **API成本** - 每个主题调用一次LLM API生成总结
⚠️ **时间范围** - 冷门主题建议增加 `--explore-months` 参数

**企业网络SSL证书修复**：

**问题**：企业网络环境中使用自签名代理证书，导致arXiv API连接时出现SSL证书验证错误：
```
SSLError: certificate verify failed: self signed certificate in certificate chain
```

**解决方案**（已实现）：

1. **自动下载证书**：
   ```bash
   mkdir -p certs
   echo | openssl s_client -showcerts -servername export.arxiv.org \
     -connect export.arxiv.org:443 2>/dev/null | \
     sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > certs/arxiv_fullchain.pem
   ```

2. **自动安装证书**：
   - `ContentExplorer` 初始化时自动检测连接
   - 如遇SSL错误，自动将 `certs/arxiv_fullchain.pem` 追加到 `certifi.where()` 证书库
   - 参考实现：与paddleocr证书安装方式一致
   - 一次性配置，永久生效

3. **技术实现**（`src/explorer.py`）：
   ```python
   def _setup_ssl_cert(self, cert_path: str = None):
       try:
           test = requests.get('https://export.arxiv.org')
       except requests.exceptions.SSLError:
           cafile = certifi.where()
           with open(cert_path, 'r') as infile:
               customca = infile.read()
           with open(cafile, 'ab') as outfile:
               outfile.write(customca.encode())
   ```

4. **文件结构**：
   ```
   certs/
   ├── arxiv_cert.pem          # 单个证书
   └── arxiv_fullchain.pem     # 完整证书链（使用此文件）
   ```

**运行效果**：
- 首次运行：自动检测并添加证书，输出提示信息
- 后续运行：直接连接成功，无需重复配置

**未来优化方向**：

1. 添加Google Custom Search API支持技术博客搜索
2. 集成Podcast平台API（需转录文本）
3. 实现结果缓存机制（避免重复查询）
4. 添加Scholar代理池（应对限流）
5. 支持导出为PDF/Notion/Obsidian格式

**相关资源**：

- **arXiv API**: https://arxiv.org/help/api/
- **scholarly库**: https://github.com/scholarly-python-package/scholarly

---

### 版本 v1.1.1 - 2026-02-10

#### Bug修复和改进

**1. 修复 scholarly 搜索功能无法工作的问题**

**问题根源** (`src/explorer.py:187-202`):
- `search_arxiv()` 返回 tuple: `(论文列表, 搜索URL)`
- `search_scholar()` 返回 list: `论文列表`
- 代码试图将 tuple 和 list 直接相加导致类型错误

**修复内容**:
```python
# 修复前
arxiv_results = self.search_arxiv(topic, limit=arxiv_limit)

# 修复后
arxiv_results, arxiv_url = self.search_arxiv(topic, limit=arxiv_limit)
```

**改进**:
- 在 `explore_topic()` 返回字典中添加 `arxiv_url` 字段
- 在输出文件中显示 arXiv 网页搜索链接，方便用户查看完整结果

**影响文件**:
- `src/explorer.py:187` - 正确解包 arXiv 返回值
- `src/explorer.py:199` - 添加 arxiv_url 到返回字典
- `src/output.py:211-213` - 在 Markdown 输出中显示搜索链接

---

**2. 添加完整的日志系统**

**问题根源**:
- `main.py` 从未配置日志系统
- 虽然 `explorer.py` 使用了 logger，但日志未初始化导致无输出
- 缺少文件日志记录，难以排查问题

**实现内容**:

1. **新增日志配置函数** (`main.py:23-38`):
   ```python
   def setup_logging(log_level: str = 'INFO'):
       log_dir = 'logs'
       log_file = f'rss_aggregator_{datetime.now().strftime("%Y%m%d")}.log'

       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
           handlers=[
               logging.FileHandler(log_file, encoding='utf-8'),
               logging.StreamHandler()
           ]
       )
   ```

2. **关键位置添加日志记录**:
   - ✅ 程序启动和配置加载 (`main.py:280-295`)
   - ✅ RSS源加载和文章抓取 (`main.py:71-87`)
   - ✅ LLM总结生成过程 (`main.py:108-134`)
   - ✅ 内容探索流程 (`main.py:167-220`)
   - ✅ 文件保存操作 (`main.py:144-157`)
   - ✅ 异常错误（包含完整堆栈跟踪）

3. **日志输出**:
   - 位置: `logs/rss_aggregator_YYYYMMDD.log`
   - 格式: 时间戳 - 模块名 - 级别 - 消息
   - 编码: UTF-8（支持中文）
   - 同时输出到控制台和文件

**使用示例**:
```bash
# 运行程序
python main.py --explore "Transformer"

# 查看日志
cat logs/rss_aggregator_20260210.log
```

**日志内容示例**:
```
2026-02-10 14:30:15 - __main__ - INFO - RSS聚合助手启动
2026-02-10 14:30:15 - __main__ - INFO - 日志文件: logs/rss_aggregator_20260210.log
2026-02-10 14:30:15 - __main__ - INFO - 配置文件加载成功: config/config.yaml
2026-02-10 14:30:15 - __main__ - INFO - 运行模式: 内容探索 - 主题: ['Transformer']
2026-02-10 14:30:16 - explorer - INFO - arXiv搜索 'Transformer': 找到 4 篇论文
2026-02-10 14:30:20 - explorer - INFO - Scholar搜索 'Transformer': 找到 3 篇论文
```

**修改文件**:
- `main.py:8` - 导入 logging 模块
- `main.py:23-38` - 新增 setup_logging() 函数
- `main.py:71-220` - 在关键位置添加 logging 调用（共15处）

**技术债务清单更新**:
- ~~添加日志系统~~ ✅ 已完成 (v1.1.1)

---

### 版本 v1.1.2 - 2026-02-10

#### 优化和Bug修复

**1. 修复 Google Scholar 时间过滤导致0结果的问题**

**问题根源** (`src/explorer.py:141-143`):
- Scholar只返回年份信息（如 2024），代码将其转换为 `2024-01-01`
- 与 cutoff_date（如 `2026-01-10`，最近30天）比较
- 导致所有非当年的论文被过滤，返回0结果

**修复方案**:
- 完全移除 Scholar 的时间过滤（方案2）
- 原因：Google Scholar 只有年份信息不够精确
- Scholar 本身已返回最相关和最新的结果，无需额外过滤

**修复内容**:
```python
# 移除前
if pub_year:
    pub_date = datetime(int(pub_year), 1, 1)
    if pub_date < self.cutoff_date:
        continue

# 修复后
# Scholar不做时间过滤，因为只有年份信息不够精确
# Google Scholar通常只返回最近和相关的论文，无需额外过滤
```

**影响文件**:
- `src/explorer.py:153-154` - 移除时间过滤逻辑
- `src/explorer.py:135` - 移除 `filtered` 变量
- `src/explorer.py:182` - 更新日志输出

**注意**: arXiv 仍保留精确时间过滤（因为有完整发布日期）

---

**2. 添加 RSS 源分类过滤功能**

**需求背景**:
- RSS源列表包含 90+ 个源，但只有少数源进行了分类标注
- 需要只抓取已分类的高质量源，忽略未分类的源

**实现内容**:

**修改 `RSSFetcher.load_feeds()` 方法** (`src/fetcher.py:27-64`):
```python
# 只加载分类不是"未分类"的源
if category != '未分类':
    feeds.append({
        'url': url,
        'category': category
    })
else:
    skipped_count += 1
```

**新增功能**:
- ✅ 自动跳过分类为"未分类"的RSS源
- ✅ 统计并显示跳过的源数量
- ✅ 添加详细的日志记录（DEBUG级别记录每个源的处理结果）
- ✅ 如果所有源都是未分类，输出警告信息

**输出示例**:
```
RSS源加载完成: 总共 90 个源, 已加载 5 个已分类源, 跳过 85 个未分类源
```

**日志示例**:
```
2026-02-10 ... - INFO - RSS源加载完成: 总共 90 个源, 已加载 5 个已分类源, 跳过 85 个未分类源
2026-02-10 ... - DEBUG - 加载RSS源: https://simonwillison.net/... - 分类: AI, data journalism
2026-02-10 ... - DEBUG - 跳过未分类RSS源: https://pluralistic.net/feed/
```

**当前已分类源** (5个):
1. `simonwillison.net` - [AI, data journalism, blogging]
2. `krebsonsecurity.com` - [security, malware, fraud]
3. `garymarcus.substack.com` - [AI, cognitive science, technology]
4. `wheresyoured.at` - [tech industry, AI, media criticism]
5. `geohot.github.io` - [technology, hacking, AI]

**影响文件**:
- `src/fetcher.py:10` - 导入 logging 模块
- `src/fetcher.py:27-64` - 修改 `load_feeds()` 添加过滤逻辑

**使用建议**:
- 继续在 `config/rss_feeds.txt` 中为更多源添加分类标签
- 分类标签格式：`URL [分类1, 分类2, ...] # 注释`

---

**版本总结**:
- 修复 Scholar 搜索返回0结果的bug
- 添加 RSS 源分类过滤，提升信息源质量
- 增强日志记录，便于调试

---

> **提示**: 每次进行重大更新或添加新功能后，请更新此文档的相应章节，保持长期记忆的准确性。
