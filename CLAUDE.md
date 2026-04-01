# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

YuxTrans 是一个 AI 翻译工具，核心目标是「响应速度是生命，翻译准度是底线」。项目采用三层架构：缓存 → 本地模型 → 云端API，自动故障转移。

**性能指标**：
- 缓存命中响应 < 50ms（底线 < 100ms）
- 本地模型响应 < 500ms（底线 < 1s）
- 云端API响应 < 2s（底线 < 3s）

## 常用命令

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装桌面端依赖（可选）
pip install -e ".[desktop]"

# 安装本地模型依赖（可选）
pip install -e ".[local]"

# 运行测试
pytest                                    # 运行所有测试
pytest tests/test_cache.py               # 运行单个测试文件
pytest -k "test_cache_hit"               # 运行匹配名称的测试

# 代码检查
ruff check yuxtrans/                     # Lint 检查
ruff format yuxtrans/                    # 格式化代码

# 运行桌面客户端
python -m yuxtrans.desktop               # 直接运行
yuxtrans                                 # 安装后运行（entry point）
```

## 核心架构

### 翻译引擎三层结构

```
用户请求 → SmartRouter → 缓存检查(<10ms) → 本地Ollama(<500ms) → 云端API(<2s)
              ↓                ↓                  ↓                 ↓
           路由策略        命中返回          失败转云端          兜底返回
```

**关键文件**：
- `yuxtrans/engine/base.py` — 翻译引擎抽象基类，定义 `translate()` 和 `translate_stream()` 接口
- `yuxtrans/engine/router.py` — 智能路由器，实现 `translate_fast()` 和 `translate_quality()` 两种模式
- `yuxtrans/engine/local.py` — Ollama 本地模型（默认 qwen2:7b）
- `yuxtrans/engine/cloud.py` — 云端API（支持 qwen/openai/deepseek）
- `yuxtrans/cache/database.py` — SQLite持久化 + LRU内存缓存

### 数据流

1. `TranslationRequest` → `SmartRouter.translate()`
2. Router 按顺序尝试：`TranslationCache` → `LocalTranslator` → `CloudTranslator`
3. 成功后通过 `cache.store()` 写入缓存
4. 返回 `TranslationResult`

### 扩展新翻译引擎

继承 `BaseTranslator`，实现：
- `async translate(request: TranslationRequest) -> TranslationResult`
- `async translate_stream(request) -> AsyncGenerator[str, None]`
- 设置 `engine_type: EngineType`

## 模块结构

```
yuxtrans/yuxtrans/
├── engine/          # 翻译引擎（核心）
├── cache/           # 缓存层（SQLite + LRU）
├── desktop/         # 桌面客户端（PyQt6）
├── metrics/         # 性能监控与质量评估
├── utils/           # 工具函数（配置、重试、并发）
└── __init__.py      # 包入口

extension/           # 浏览器插件（Manifest V3）
tests/               # 单元测试
benchmark/           # 性能测试用例
examples/            # 示例脚本
```

## 配置

- 配置文件路径：`~/.yuxtrans/`
- 缓存数据库：`~/.yuxtrans/cache/translations.db`
- 默认本地模型：`qwen2:7b`（需安装 Ollama）
- 默认云端API：`qwen-turbo`

## 测试约定

- 使用 pytest + pytest-asyncio
- 异步测试标记 `@pytest.mark.asyncio`
- 测试文件命名 `test_*.py`
- 使用 tempfile 创建临时数据库进行缓存测试