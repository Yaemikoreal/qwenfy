"""
简化的端到端演示
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from yuxtrans.engine.base import TranslationRequest, EngineType
from yuxtrans.cache.database import TranslationCache
from yuxtrans.cache.warmup import CacheWarmupStrategy
from yuxtrans.engine.router import SmartRouter
from yuxtrans.metrics.quality import QualityMetrics, BLEUScore


async def demo_cache_flow():
    """缓存流程演示"""
    print("=" * 60)
    print("缓存流程演示")
    print("=" * 60)

    cache = TranslationCache(db_path="demo_cache.db", preload_popular=False)
    warmup = CacheWarmupStrategy(cache)

    print("\n预热常用词汇...")
    count = await warmup.warmup_common_words()
    print(f"预热了 {count} 个常用词汇")

    requests = [
        TranslationRequest(text="hello", source_lang="en", target_lang="zh"),
        TranslationRequest(text="world", source_lang="en", target_lang="zh"),
        TranslationRequest(text="function", source_lang="en", target_lang="zh"),
        TranslationRequest(text="class", source_lang="en", target_lang="zh"),
    ]

    print("\n翻译测试:")
    for req in requests:
        try:
            result = await cache.translate(req)
            print(f"  {req.text} -> [缓存命中] ({result.response_time_ms:.2f}ms)")
        except Exception as e:
            print(f"  {req.text} -> [缓存未命中]")

    print(f"\n缓存命中率: {cache.hit_rate:.2%}")
    print(f"平均响应时间: {cache.avg_response_time_ms:.2f}ms")


async def demo_quality_evaluation():
    """质量评估演示"""
    print("\n" + "=" * 60)
    print("翻译质量评估演示")
    print("=" * 60)

    bleu = BLEUScore()
    metrics = QualityMetrics()

    test_cases = [
        ("你好世界", ["你好世界"]),
        ("这是一段翻译", ["这是一段翻译"]),
        ("Hello World", ["hello world"]),
    ]

    print("\nBLEU评分:")
    for candidate, references in test_cases:
        score, _ = bleu.calculate(candidate, references)
        print(f"  '{candidate}' -> BLEU: {score:.4f}")

    result = metrics.evaluate("这是一段高质量的翻译", ["这是一段高质量的翻译"])
    print(f"\n综合评估:")
    print(f"  BLEU: {result.bleu_score:.4f}")
    print(f"  WER: {result.word_error_rate:.4f}")
    print(f"  通过: {result.passed}")


async def demo_smart_router():
    """智能路由演示"""
    print("\n" + "=" * 60)
    print("智能路由演示")
    print("=" * 60)

    cache = TranslationCache(db_path="router_cache.db", preload_popular=False)
    warmup = CacheWarmupStrategy(cache)
    await warmup.warmup_common_words()

    router = SmartRouter(cache=cache)

    print("\n可用引擎:", [e.value for e in router.available_engines])

    request = TranslationRequest(text="hello", source_lang="en", target_lang="zh")
    result = await router.translate(request)

    print(f"\n翻译结果: hello -> [缓存]")
    print(f"引擎: {result.engine.value}")
    print(f"响应时间: {result.response_time_ms:.2f}ms")


async def main():
    """运行演示"""
    print("\nYuxTrans 端到端演示\n")

    await demo_cache_flow()
    await demo_quality_evaluation()
    await demo_smart_router()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)

    Path("demo_cache.db").unlink(missing_ok=True)
    Path("router_cache.db").unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
