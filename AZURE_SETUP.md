# Azure OpenAI 配置指南

本指南帮助你配置公司部署在Azure上的GPT-5.1 endpoint。

## 📋 前提条件

你需要从公司IT或Azure管理员获取以下信息：

1. **Azure OpenAI Endpoint URL** - 格式类似：`https://your-company.openai.azure.com/`
2. **API Key** - Azure OpenAI的访问密钥
3. **Deployment名称** - 你们部署的模型名称（如 `gpt-51`）
4. **API Version**（可选）- 默认使用 `2024-02-15-preview`

## 🚀 快速配置

### 方式一：使用示例配置文件（推荐）

1. **复制Azure配置模板：**
```bash
cp config/config.azure.example.yaml config/config.yaml
```

2. **编辑 `config/config.yaml`，填入你的信息：**

```yaml
llm:
  provider: "azure"
  api_key: "your-azure-api-key-here"  # 替换为你的API密钥
  model: "gpt-51"                      # 替换为你的deployment名称
  base_url: "https://your-company.openai.azure.com/"  # 替换为你的endpoint
  api_version: "2024-02-15-preview"
  temperature: 0.3
  max_tokens: 2000
```

### 方式二：使用环境变量（更安全）

1. **设置环境变量：**

**Linux/Mac:**
```bash
export AZURE_OPENAI_KEY="your-api-key-here"
```

**Windows PowerShell:**
```powershell
$env:AZURE_OPENAI_KEY="your-api-key-here"
```

**Windows CMD:**
```cmd
set AZURE_OPENAI_KEY=your-api-key-here
```

2. **配置文件使用环境变量：**

```yaml
llm:
  provider: "azure"
  api_key: "${AZURE_OPENAI_KEY}"  # 从环境变量读取
  model: "gpt-51"
  base_url: "https://your-company.openai.azure.com/"
  api_version: "2024-02-15-preview"
```

## 🔍 关键配置说明

### 1. Provider
```yaml
provider: "azure"  # 必须设置为 "azure"
```

### 2. Model (Deployment名称)
这里填写的是Azure中的**deployment名称**，不是模型名称。

例如：
- 如果你在Azure Portal的"Model deployments"中看到名称是 `gpt-51-deployment`
- 那么这里就填 `gpt-51-deployment`

```yaml
model: "gpt-51"  # 你的实际deployment名称
```

### 3. Base URL (Endpoint)
从Azure Portal的"Keys and Endpoint"部分获取。

格式：`https://<your-resource-name>.openai.azure.com/`

**注意：**
- 必须包含 `https://`
- 末尾的 `/` 建议保留

```yaml
base_url: "https://your-company.openai.azure.com/"
```

### 4. API Version
Azure OpenAI的API版本号，通常使用最新的preview版本。

```yaml
api_version: "2024-02-15-preview"  # 或使用公司推荐的版本
```

常用版本：
- `2024-02-15-preview` (推荐)
- `2023-12-01-preview`
- `2023-05-15`

## ✅ 测试配置

配置完成后，运行测试工具验证连接：

```bash
python tools/test_llm.py
```

如果配置正确，你会看到：
```
==============================================================
LLM连接测试
==============================================================
提供商: azure
模型: gpt-51
API密钥来源: 配置文件
API密钥: abcdef1234...
自定义URL: https://your-company.openai.azure.com/

正在测试连接...

正在使用 azure (gpt-51) 生成总结...
✓ 总结生成完成

✅ 连接成功!

测试响应:
------------------------------------------------------------
这是一篇用于测试LLM连接的示例响应...
------------------------------------------------------------
```

## 🐛 常见问题

### Q1: 连接失败 - "Resource not found"

**可能原因：**
- `base_url` 填写错误
- `model` (deployment名称) 不存在

**解决方法：**
1. 登录 [Azure Portal](https://portal.azure.com)
2. 找到你的OpenAI资源
3. 检查 "Keys and Endpoint" 中的Endpoint URL
4. 检查 "Model deployments" 中的deployment名称

### Q2: 认证失败 - "401 Unauthorized"

**可能原因：**
- API密钥错误或过期

**解决方法：**
1. 检查API密钥是否正确复制（注意空格）
2. 在Azure Portal重新生成密钥
3. 确认密钥有访问权限

### Q3: API版本错误

**错误信息：** `Invalid API version`

**解决方法：**
- 咨询公司管理员支持的API版本
- 尝试使用 `2024-02-15-preview` 或 `2023-12-01-preview`

### Q4: 公司网络限制

如果公司内部需要通过代理访问Azure：

**设置代理：**
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

或在代码中配置（联系管理员获取具体配置）。

## 📊 完整配置示例

这是一个完整的、可以直接使用的配置示例：

```yaml
# Azure OpenAI配置
llm:
  provider: "azure"
  api_key: "${AZURE_OPENAI_KEY}"
  model: "gpt-51"
  base_url: "https://contoso-ai.openai.azure.com/"
  api_version: "2024-02-15-preview"
  temperature: 0.3
  max_tokens: 2000

# RSS配置（92个源）
rss:
  feeds_file: "config/rss_feeds.txt"
  fetch_limit: 10
  days_back: 1
  timeout: 30

# 输出配置
output:
  format: "markdown"
  directory: "output/summaries"
  filename_template: "ai_digest_{date}.md"
  language: "zh"

# 总结配置
summary:
  group_by_category: true  # 建议开启，因为有92个源
  include_original_link: true
  summary_style: "concise"
  highlight_keywords:
    - "大模型"
    - "AI"
    - "机器学习"

# 定时任务
schedule:
  enabled: false
  time: "09:00"
  timezone: "Asia/Shanghai"
```

## 🚀 开始使用

配置并测试成功后，就可以运行了：

```bash
# 测试模式（仅5个源）
python main.py --test

# 正式运行（所有92个源）
python main.py

# 定时任务模式
python main.py --schedule
```

## 📞 获取帮助

如果遇到问题：
1. 查看 `README.md` 了解基本使用
2. 查看 `USAGE_GUIDE.md` 了解详细功能
3. 运行 `python main.py --help` 查看命令选项
4. 联系公司IT或Azure管理员确认配置信息

## 🔐 安全建议

1. **不要在代码中硬编码API密钥**
2. **使用环境变量存储敏感信息**
3. **不要将包含密钥的配置文件提交到git**
4. **定期更新API密钥**
5. **限制密钥的访问权限**

添加到 `.gitignore`:
```
config/config.yaml
.env
```
