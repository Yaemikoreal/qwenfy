"""
端到端示例 - 翻译流程完整演示
"""

import asyncio
import tempfile
import os
from pathlib import Path

from yuxtrans.engine.base import TranslationRequest, EngineType
from yuxtrans.cache.database import TranslationCache
from yuxtrans.cache.warmup import CacheWarmupStrategy
from yuxtrans.engine.router import SmartRouter
from yuxtrans.engine.local import LocalTranslator
from yuxtrans.engine.cloud import CloudTranslator
from yuxtrans.metrics.benchmark import PerformanceBenchmark
from yuxtrans.metrics.quality import QualityMetrics, BLEUScore


async def demo_basic_flow():
    """基本翻译流程演示"""
    print("=" * 60)
    print("1. 基本翻译流程演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "demo_cache.db")

        cache = TranslationCache(db_path=db_path, preload_popular=False)
        warmup = CacheWarmupStrategy(cache)

        print("\n预热常用词汇...")
        count = await warmup.warmup_common_words()
        print(f"预热了 {count} 个常用词汇")

        requests = [
            TranslationRequest(text="hello world", source_lang="en", target_lang="zh"),
            TranslationRequest(text="thank you", source_lang="en", target_lang="zh"),
            TranslationRequest(text="function", source_lang="en", target_lang="zh"),
            TranslationRequest(text="this is a test", source_lang="en", target_lang="zh"),
        ]

        print("\n翻译测试:")
        for req in requests:
            try:
                result = await cache.translate(req)
                print(f"  {req.text} -> {result.text} ({result.response_time_ms:.2f}ms)")
            except Exception:
                print(f"  {req.text} -> [缓存未命中]")

        print(f"\n缓存命中率: {cache.hit_rate:.2%}")
        print(f"平均响应时间: {cache.avg_response_time_ms:.2f}ms")


async def demo_smart_router():
    """智能路由演示"""
    print("\n" + "=" * 60)
    print("2. 智能路由演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "router_cache.db")

        cache = TranslationCache(db_path=db_path, preload_popular=False)
        warmup = CacheWarmupStrategy(cache)
        await warmup.warmup_common_words()

        router = SmartRouter(cache=cache)

        print("\n可用引擎:", [e.value for e in router.available_engines])

        requests = [
            TranslationRequest(text="hello", source_lang="en", target_lang="zh"),
            TranslationRequest(text="world", source_lang="en", target_lang="zh"),
        ]

        print("\n路由翻译:")
        for req in requests:
            result = await router.translate(req)
            print(
                f"  {req.text} -> {result.text} (引擎: {result.engine.value}, 时间: {result.response_time_ms:.2f}ms)"
            )

        print(f"\n路由统计: {router.stats}")


async def demo_quality_metrics():
    """质量评估演示"""
    print("\n" + "=" * 60)
    print("3. 翻译质量评估演示")
    print("=" * 60)

    metrics = QualityMetrics()
    bleu = BLEUScore()

    test_cases = [
        ("你好世界", ["你好世界"], "精确匹配"),
        ("你好，世界！", ["你好世界", "你好，世界"], "部分匹配"),
        ("这是一个高质量的翻译", ["这是一个高质量的翻译"], "高质量"),
        ("This is a test", ["This is a test"], "英文精确"),
        ("Hello world", ["Hello World"], "英文部分"),
    ]

    print("\nBLEU评分测试:")
    for candidate, references, desc in test_cases:
        score, _ = bleu.calculate(candidate, references)
        print(f"  {desc}: BLEU = {score:.4f}")

    print("\n综合质量评估:")
    result = metrics.evaluate("这是一段高质量的翻译结果", ["这是一段高质量的翻译结果"])
    print(f"  BLEU: {result.bleu_score:.4f}")
    print(f"  WER: {result.word_error_rate:.4f}")
    print(f"  CER: {result.character_error_rate:.4f}")
    print(f"  语义相似度: {result.semantic_similarity:.4f}")
    print(f"  是否通过: {result.passed}")


async def demo_performance_benchmark():
    """性能基准测试演示"""
    print("\n" + "=" * 60)
    print("4. 性能基准测试演示")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "bench_cache.db")

        cache = TranslationCache(db_path=db_path, preload_popular=False)
        warmup = CacheWarmupStrategy(cache)
        await warmup.warmup_common_words()

        benchmark = PerformanceBenchmark()

        test_requests = [
            TranslationRequest(text="hello", source_lang="en", target_lang="zh"),
            TranslationRequest(text="world", source_lang="en", target_lang="zh"),
            TranslationRequest(text="function", source_lang="en", target_lang="zh"),
        ]

        print("\n运行基准测试...")
        result = await benchmark.run_benchmark(
            cache,
            test_requests,
            test_name="cache_benchmark",
            warmup=2,
            iterations=5,
        )

        print(f"\n性能结果:")
        print(f"  总请求: {result.total_requests}")
        print(f"  成功: {result.successful_requests}")
        print(f"  失败: {result.failed_requests}")
        print(f"  平均响应时间: {result.avg_response_time_ms:.2f}ms")
        print(f"  P50: {result.p50_response_time_ms:.2f}ms")
        print(f"  P95: {result.p95_response_time_ms:.2f}ms")
        print(f"  P99: {result.p99_response_time_ms:.2f}ms")
        print(f"  成功率: {result.success_rate:.2%}")

        thresholds = benchmark.DEFAULT_THRESHOLDS["cache"]
        passes = result.passes_threshold(thresholds)
        print(f"\n通过性能阈值: {passes}")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("YuxTrans 端到端演示")
    print("=" * 60)

    await demo_basic_flow()
    await demo_smart_router()
    await demo_quality_metrics()
    await demo_performance_benchmark()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
