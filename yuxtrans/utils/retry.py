"""
重试与超时机制
P2-002: 失败自动重试，超时 < 3s
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional


class RetryStrategy(Enum):
    """重试策略"""

    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass
class RetryConfig:
    """重试配置"""

    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay_ms: int = 100
    max_delay_ms: int = 5000
    jitter: bool = True
    retryable_errors: List[str] = field(
        default_factory=lambda: [
            "timeout",
            "connection_error",
            "rate_limit",
            "server_error",
        ]
    )


@dataclass
class RetryResult:
    """重试结果"""

    success: bool
    attempts: int
    total_time_ms: float
    last_error: Optional[str] = None
    result: Any = None


class RetryExecutor:
    """
    重试执行器

    支持多种重试策略：
    - 固定间隔
    - 线性递增
    - 指数退避
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            RetryResult: 重试结果
        """
        start_time = time.perf_counter()
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)

                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time_ms=(time.perf_counter() - start_time) * 1000,
                    result=result,
                )

            except Exception as e:
                error_type = self._classify_error(e)

                if error_type not in self.config.retryable_errors:
                    return RetryResult(
                        success=False,
                        attempts=attempt + 1,
                        total_time_ms=(time.perf_counter() - start_time) * 1000,
                        last_error=str(e),
                    )

                last_error = e

                if attempt < self.config.max_retries:
                    delay_ms = self._calculate_delay(attempt)
                    await asyncio.sleep(delay_ms / 1000)

        return RetryResult(
            success=False,
            attempts=self.config.max_retries + 1,
            total_time_ms=(time.perf_counter() - start_time) * 1000,
            last_error=str(last_error),
        )

    def _classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        error_str = str(error).lower()

        if "timeout" in error_str or "timed out" in error_str:
            return "timeout"
        if "connection" in error_str or "network" in error_str:
            return "connection_error"
        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        if "500" in error_str or "502" in error_str or "503" in error_str:
            return "server_error"

        return "unknown"

    def _calculate_delay(self, attempt: int) -> int:
        """计算重试延迟"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay_ms

        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay_ms * (attempt + 1)

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay_ms * (2**attempt)

        else:
            delay = self.config.base_delay_ms

        delay = min(delay, self.config.max_delay_ms)

        if self.config.jitter:
            jitter_range = delay * 0.1
            delay += random.randint(-int(jitter_range), int(jitter_range))

        return max(delay, 0)


class TimeoutWrapper:
    """超时包装器"""

    def __init__(self, timeout_ms: int = 3000):
        self.timeout_ms = timeout_ms

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行带超时限制的函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            asyncio.TimeoutError: 超时时抛出
        """
        return await asyncio.wait_for(
            func(*args, **kwargs),
            timeout=self.timeout_ms / 1000,
        )


class ResilientExecutor:
    """
    弹性执行器

    组合重试和超时机制
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        timeout_ms: int = 3000,
    ):
        self.retry_executor = RetryExecutor(retry_config)
        self.timeout_wrapper = TimeoutWrapper(timeout_ms)

    async def execute(self, func: Callable, *args, **kwargs) -> RetryResult:
        """
        执行带重试和超时的函数
        """

        async def _execute_with_timeout():
            return await self.timeout_wrapper.execute(func, *args, **kwargs)

        return await self.retry_executor.execute(_execute_with_timeout)

    async def execute_with_fallback(
        self, primary_func: Callable, fallback_func: Callable, *args, **kwargs
    ) -> RetryResult:
        """
        执行带降级备选的函数

        Args:
            primary_func: 主函数
            fallback_func: 备选函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            RetryResult: 执行结果
        """
        primary_result = await self.execute(primary_func, *args, **kwargs)

        if primary_result.success:
            return primary_result

        return await self.execute(fallback_func, *args, **kwargs)
