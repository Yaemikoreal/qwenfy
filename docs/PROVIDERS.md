# 云端 API 供应商配置指南

YuxTrans v0.1.0 支持以下云端 API 供应商：

---

## 支持的供应商

| 供应商 | ID | API 格式 | 默认模型 | 特点 |
|--------|-----|----------|----------|------|
| 阿里云通义千问 | `qwen` | qwen | qwen-turbo | 国内稳定，中文优化 |
| OpenAI | `openai` | openai | gpt-4o-mini | 国际标准，多语言 |
| DeepSeek | `deepseek` | openai | deepseek-chat | 国内性价比高 |
| Anthropic | `anthropic` | anthropic | claude-3-5-haiku-latest | 高质量推理 |
| Groq | `groq` | openai | llama-3.1-8b-instant | 极速推理 (<100ms) |
| Moonshot | `moonshot` | openai | moonshot-v1-8k | 长文本支持 |
| Siliconflow | `siliconflow` | openai | Qwen/Qwen2.5-7B-Instruct | 多模型选择 |
| 自定义 | `custom` | openai | 自定义 | OpenAI 兼容 API |

---

## API 格式说明

### OpenAI 格式（兼容最多）

适用于：`openai`, `deepseek`, `groq`, `moonshot`, `siliconflow`, `custom`

```json
// 请求格式
{
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "..."}],
  "temperature": 0.3,
  "stream": false
}

// 响应格式
{
  "choices": [{
    "message": {"content": "翻译结果"}
  }]
}
```

### Anthropic 格式（Claude）

适用于：`anthropic`

```json
// 请求格式
{
  "model": "claude-3-5-haiku-latest",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "..."}]
}

// 请求头
{
  "x-api-key": "your-api-key",
  "anthropic-version": "2023-06-01",
  "Content-Type": "application/json"
}

// 响应格式
{
  "content": [{"text": "翻译结果"}]
}
```

### Qwen 格式（阿里云 DashScope）

适用于：`qwen`

```json
// 请求格式
{
  "model": "qwen-turbo",
  "input": {"messages": [{"role": "user", "content": "..."}]},
  "parameters": {"temperature": 0.3}
}

// 响应格式
{
  "output": {"text": "翻译结果"}
}
```

---

## 使用示例

### Python API

```python
from yuxtrans.engine.cloud import CloudTranslator
from yuxtrans.engine.base import TranslationRequest
import asyncio

# OpenAI
translator = CloudTranslator(
    provider="openai",
    api_key="sk-xxx",
    model="gpt-4o-mini"
)

# Anthropic Claude
translator = CloudTranslator(
    provider="anthropic",
    api_key="sk-ant-xxx",
    model="claude-3-5-haiku-latest"
)

# Groq（极速）
translator = CloudTranslator(
    provider="groq",
    api_key="gsk_xxx",
    model="llama-3.1-8b-instant"
)

# 自定义 OpenAI 兼容 API（如本地 Ollama、vLLM）
translator = CloudTranslator(
    provider="custom",
    api_key="not-needed",
    model="qwen2.5-7b",
    custom_endpoint="http://localhost:8000/v1/chat/completions"
)

# 翻译
async def translate():
    request = TranslationRequest(text="Hello, world!", source_lang="en", target_lang="zh")
    result = await translator.translate(request)
    print(result.text)

asyncio.run(translate())
```

### 查看支持的供应商

```python
from yuxtrans.engine.cloud import CloudTranslator

providers = CloudTranslator.get_supported_providers()
for id, info in providers.items():
    print(f"{info['name']}: {info['api_key_url']}")
```

---

## API Key 获取地址

| 供应商 | 获取地址 |
|--------|----------|
| Qwen | https://dashscope.console.aliyun.com/apiKey |
| OpenAI | https://platform.openai.com/api-keys |
| DeepSeek | https://platform.deepseek.com/api_keys |
| Anthropic | https://console.anthropic.com/settings/keys |
| Groq | https://console.groq.com/keys |
| Moonshot | https://platform.moonshot.cn/console/api-keys |
| Siliconflow | https://cloud.siliconflow.cn/account/ak |

---

## 配置文件示例

```yaml
# ~/.yuxtrans/config.yaml
engine:
  prefer_local: false
  cloud_provider: anthropic
  cloud_model: claude-3-5-haiku-latest
  cloud_api_key: sk-ant-xxx
  custom_endpoint: ""  # 仅 custom 供应商需要
```

---

## 推荐配置

| 场景 | 推荐 | 原因 |
|------|------|------|
| 国内用户 | `qwen` 或 `deepseek` | 稳定、中文优化、性价比 |
| 国际用户 | `openai` 或 `anthropic` | 质量、多语言 |
| 极速响应 | `groq` | < 100ms 推理速度 |
| 长文本 | `moonshot` | 支持 200K token |
| 多模型 | `siliconflow` | Qwen/Llama/GLM 等多选择 |
| 本地部署 | `custom` | 连接本地 Ollama/vLLM |