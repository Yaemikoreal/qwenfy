"""
Phase 2 完整演示 - 云端兜底与质量提升
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from yuxtrans.engine.base import TranslationRequest, TranslationResult, EngineType
from yuxtrans.cache.database import TranslationCache
from yuxtrans.cache.warmup import CacheWarmupStrategy
from yuxtrans.engine.router import SmartRouter
from yuxtrans.utils.retry import RetryExecutor, RetryConfig, RetryStrategy
from yuxtrans.utils.concurrency import RateLimiter, ConcurrencyController
from yuxtrans.utils.config import ConfigManager
from yuxtrans.metrics.quality import QualityMetrics, BLEUScore
from yuxtrans.metrics.benchmark import PerformanceBenchmark


async def demo_retry_mechanism():
    """演示重试机制"""
    print("=" * 60)
    print("重试机制演示")
    print("=" * 60)

    config = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL,
        base_delay_ms=100,
        jitter=True,
    )

    executor = RetryExecutor(config)

    call_count = 0

    async def unreliable_service():
        nonlocal call_count
        call_count += 1
        print(f"  尝试 #{call_count}")

        if call_count < 3:
            raise Exception("timeout: 服务暂时不可用")

        return "翻译成功"

    print("\n模拟不稳定服务:")
    result = await executor.execute(unreliable_service)

    print(f"\n结果: {result.result}")
    print(f"成功: {result.success}")
    print(f"尝试次数: {result.attempts}")
    print(f"总耗时: {result.total_time_ms:.2f}ms")


async def demo_rate_limiter():
    """演示限流器"""
    print("\n" + "=" * 60)
    print("限流器演示")
    print("=" * 60)

    limiter = RateLimiter()

    print("\n发送5个请求:")
    times = []

    for i in range(5):
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        times.append(elapsed)
        print(f"  请求 #{i + 1}: 通过 ({elapsed:.2f}ms)")

    print(f"\n限流器状态: {limiter.get_status()}")


async def demo_concurrency_control():
    """演示并发控制"""
    print("\n" + "=" * 60)
    print("并发控制演示")
    print("=" * 60)

    controller = ConcurrencyController()

    async def task(n):
        await asyncio.sleep(0.1)
        return f"任务{n}完成"

    print("\n并发执行5个任务:")
    tasks = [controller.execute(task, i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    for r in results:
        print(f"  {r}")

    print(f"\n控制器状态: {controller.get_status()}")


async def demo_config_management():
    """演示配置管理"""
    print("\n" + "=" * 60)
    print("配置管理演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "demo_config.yaml")
        manager = ConfigManager(config_path=config_path)

        config = manager.load()

        print("\n默认配置:")
        print(f"  本地模型: {config.engine.local_model}")
        print(f"  云端提供商: {config.engine.cloud_provider}")
        print(f"  最大重试: {config.performance.max_retries}")
        print(f"  BLEU阈值: {config.performance.bleu_threshold}")

        print("\n更新配置...")
        manager.update("engine", "local_model", "qwen2:1.5b")
        manager.update("performance", "bleu_threshold", 0.75)

        updated = manager.load()
        print(f"\n更新后:")
        print(f"  本地模型: {updated.engine.local_model}")
        print(f"  BLEU阈值: {updated.performance.bleu_threshold}")


async def demo_quality_assessment():
    """演示质量评估"""
    print("\n" + "=" * 60)
    print("翻译质量评估演示")
    print("=" * 60)

    metrics = QualityMetrics()
    bleu = BLEUScore()

    translations = [
        ("这是一个高质量的翻译", ["这是一个高质量的翻译"]),
        ("这是一段技术文档", ["这是一段技术文档"]),
        ("Hello World", ["hello world"]),
        ("机器学习是人工智能的一个子集", ["机器学习是人工智能的一个子集"]),
    ]

    print("\n翻译质量评分:")
    for candidate, references in translations:
        score, _ = bleu.calculate(candidate, references)
        status = "✓ 通过" if score >= 0.7 else "✗ 未通过"
        print(f"  '{candidate[:20]}...' -> BLEU: {score:.4f} {status}")


async def demo_full_pipeline():
    """演示完整流程"""
    print("\n" + "=" * 60)
    print("完整翻译流程演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "pipeline_cache.db")

        cache = TranslationCache(db_path=db_path, preload_popular=False)
        warmup = CacheWarmupStrategy(cache)

        print("\n预热缓存...")
        count = await warmup.warmup_common_words()
        print(f"预热了 {count} 个常用词汇")

        router = SmartRouter(cache=cache)

        requests = [
            TranslationRequest(text="hello", source_lang="en", target_lang="zh"),
            TranslationRequest(text="world", source_lang="en", target_lang="zh"),
            TranslationRequest(text="function", source_lang="en", target_lang="zh"),
            TranslationRequest(text="class", source_lang="en", target_lang="zh"),
        ]

        print("\n翻译测试:")
        for req in requests:
            result = await router.translate(req)
            status = "缓存命中" if result.cached else "实时翻译"
            print(f"  {req.text} -> {status} ({result.response_time_ms:.2f}ms)")

        print(f"\n性能统计:")
        print(f"  缓存命中率: {cache.hit_rate:.2%}")
        print(f"  平均响应时间: {cache.avg_response_time_ms:.2f}ms")

        benchmark = PerformanceBenchmark()

        print("\n运行基准测试...")
        bench_result = await benchmark.run_benchmark(
            router,
            requests,
            test_name="phase2_benchmark",
            warmup=1,
            iterations=3,
        )

        print(f"\n基准测试结果:")
        print(f"  总请求: {bench_result.total_requests}")
        print(f"  成功率: {bench_result.success_rate:.2%}")
        print(f"  平均响应: {bench_result.avg_response_time_ms:.2f}ms")
        print(f"  P95响应: {bench_result.p95_response_time_ms:.2f}ms")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("Phase 2 演示 - 云端兜底与质量提升")
    print("=" * 60)

    await demo_retry_mechanism()
    await demo_rate_limiter()
    await demo_concurrency_control()
    await demo_config_management()
    await demo_quality_assessment()
    await demo_full_pipeline()

    print("\n" + "=" * 60)
    print("Phase 2 演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
