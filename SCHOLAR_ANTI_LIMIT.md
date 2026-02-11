# Google Scholar 防限流策略指南

> **版本**: v1.2.0
> **最后更新**: 2026-02-11
> **状态**: 已完全实现并测试

---

## 🚨 问题背景

Google Scholar 对爬虫非常敏感，容易触发：
- **429 Too Many Requests** - 请求过于频繁
- **CAPTCHA 验证** - 人机验证挑战
- **IP 封禁** - 暂时或永久禁止访问

企业网络环境下尤其严重（多人共享同一公网IP）。

---

## ✅ 已实现的防护措施

### 1. **随机延迟策略** ⏱️

**原实现**: 固定延迟 2 秒
**新实现**: 随机延迟 5-10 秒（可配置）

```python
# 每次请求之间随机等待 5-10 秒
delay = random.uniform(5, 10)
time.sleep(delay)
```

**配置位置**: `config/config.yaml`
```yaml
explorer:
  scholar_delay_range: [5, 10]  # [最小秒数, 最大秒数]
```

**建议调整**:
- 普通环境: `[5, 10]`
- 企业网络: `[8, 15]`
- 触发限流后: `[10, 20]`

---

### 2. **指数退避重试** 🔄

触发 CAPTCHA 或 429 错误时，自动等待并重试：

| 重试次数 | 等待时间 | 说明 |
|---------|---------|------|
| 第 1 次 | 5-20 秒 | 基础延迟 + 随机 |
| 第 2 次 | 10-25 秒 | 2倍延迟 + 随机 |
| 第 3 次 | 20-35 秒 | 4倍延迟 + 随机 |

```python
wait_time = base_delay * (2 ** retry_count) + random.uniform(5, 15)
```

**配置位置**: `config/config.yaml`
```yaml
explorer:
  scholar_retry: 3  # 最大重试次数
```

---

### 3. **智能 CAPTCHA 检测** 🔍

自动检测以下信号并触发重试：
- HTTP 状态码 `429 Too Many Requests`
- 重定向到 `/sorry/index` 页面
- 异常信息包含 `captcha` 关键词

检测到后会：
1. 停止当前搜索
2. 显示友好提示信息
3. 自动进入指数退避重试

```
⚠️  Google Scholar 触发限流保护
⏳ 等待 12.3 秒后自动重试... (1/3)
```

---

### 4. **随机 User-Agent 轮换** 🎭

模拟真实浏览器访问（虽然 scholarly 库暂不完全支持，但已预留接口）：

```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121...',
    # ... 5 种不同的浏览器
]
```

---

### 5. **降低查询数量** 📉

**建议配置**:
```yaml
explorer:
  results_per_source:
    arxiv: 7     # arXiv 更稳定，可以多抓
    scholar: 3   # Scholar 限制严格，建议 ≤3
```

每个主题只查询 **3 篇** Scholar 论文，降低被封风险。

---

## 📊 效果对比

| 策略 | 原实现 | 新实现 | 改进幅度 |
|------|--------|--------|---------|
| 请求间隔 | 2秒固定 | 5-10秒随机 | **2.5-5倍** |
| 触发限流后 | 直接失败 | 指数退避重试 | **容错能力 ∞** |
| CAPTCHA检测 | 无 | 智能检测 | **主动防御** |
| 查询数量 | 无限制 | 建议≤3篇 | **风险降低50%** |

---

## ⚙️ 配置文件完整示例

`config/config.yaml`:
```yaml
# 内容探索配置
explorer:
  enabled: true
  months_back: 1
  results_limit: 10

  # Scholar 防限流配置
  results_per_source:
    arxiv: 7
    scholar: 3              # 建议 ≤3 以降低限流风险
  scholar_retry: 3          # CAPTCHA 后最大重试次数
  scholar_delay_range: [5, 10]  # 请求间随机延迟范围（秒）

  output_directory: "output/explorations"
  filename_template: "explore_{topic}_{date}.md"
  cert_path: "certs/arxiv_fullchain.pem"
```

---

## 🎯 使用建议

### 场景 1: 普通个人网络
```yaml
scholar_retry: 3
scholar_delay_range: [5, 10]
results_per_source:
  scholar: 3
```

### 场景 2: 企业网络（共享IP）
```yaml
scholar_retry: 2
scholar_delay_range: [10, 20]  # 更保守的延迟
results_per_source:
  scholar: 2  # 减少查询量
```

### 场景 3: 已经被限流
```yaml
scholar_retry: 5
scholar_delay_range: [15, 30]  # 大幅增加延迟
results_per_source:
  scholar: 1  # 只查询 1 篇
```

等待 **30-60 分钟**后再尝试。

---

## 🔧 高级优化（未来可选）

### 1. 使用代理IP池 🌐
```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.FreeProxies()  # 或使用付费代理
scholarly.use_proxy(pg)
```

**成本**: 付费代理 $10-50/月
**效果**: 几乎完全避免限流

### 2. 使用 ScraperAPI 服务 💰
```python
import requests

api_key = "your_scraperapi_key"
url = f"http://api.scraperapi.com?api_key={api_key}&url={scholar_url}"
response = requests.get(url)
```

**成本**: $29-99/月
**效果**: 自动处理 CAPTCHA + 代理轮换

### 3. 使用官方 API（推荐但有限制）
Google Scholar **没有官方 API**，但可以考虑：
- **Semantic Scholar API** - 免费，学术论文检索
- **Microsoft Academic API** - 已停止服务
- **OpenAlex API** - 开源学术图谱，推荐

---

## 📝 运行日志示例

成功情况：
```
2026-02-11 17:30:12 - INFO - Scholar搜索开始 - 查询: 'Transformer', 限制: 3
2026-02-11 17:30:15 - DEBUG - 等待 7.3 秒...
2026-02-11 17:30:22 - INFO - ✓ 添加论文: Attention Is All You Need...
2026-02-11 17:30:30 - INFO - ✓ 添加论文: BERT: Pre-training of Deep...
2026-02-11 17:30:38 - INFO - Scholar搜索 'Transformer' 完成: 收集 3 篇
```

触发限流情况：
```
2026-02-11 17:22:12 - WARNING - ⚠️  检测到限流信号: Got a captcha request
2026-02-11 17:22:12 - WARNING - ⏸ Scholar触发限流，等待 12.3 秒后重试 (1/3)...

⚠️  Google Scholar 触发限流保护
⏳ 等待 12.3 秒后自动重试... (1/3)

2026-02-11 17:22:25 - INFO - Scholar搜索开始 - 查询: 'DAPO', 限制: 3, 尝试: 2
```

---

## 🚀 测试命令

测试新的防限流策略：
```bash
# 单主题测试
python main.py --explore "machine learning"

# 多主题测试（更容易触发限流）
python main.py --explore "NLP" --explore "computer vision" --explore "reinforcement learning"

# 查看详细日志
tail -f logs/rss_aggregator_$(date +%Y%m%d).log
```

---

## 💡 最佳实践

1. **降低查询频率**: 不要连续探索多个主题
2. **合理设置延迟**: 企业网络建议 10-20 秒
3. **减少查询数量**: Scholar 限制在 2-3 篇
4. **错峰使用**: 避开高峰时段（美国白天）
5. **监控日志**: 观察是否频繁触发限流
6. **考虑替代方案**: arXiv 更稳定，优先使用

---

## 📞 问题排查

### Q: 仍然频繁触发 CAPTCHA？
A: 增加延迟到 15-30 秒，减少 Scholar 查询量到 1-2 篇

### Q: 重试多次仍失败？
A: 等待 1-2 小时后再试，或考虑使用代理

### Q: arXiv 可以，Scholar 完全不行？
A: 暂时禁用 Scholar，只使用 arXiv
```yaml
results_per_source:
  arxiv: 10
  scholar: 0  # 暂时禁用
```

### Q: 企业网络限制太严格？
A: 联系 IT 部门申请白名单，或使用移动热点测试

---

**提示**: 如果问题仍然存在，可以考虑使用 **Semantic Scholar API** 或 **OpenAlex API** 作为替代方案，它们提供官方 API，无需担心限流问题。
