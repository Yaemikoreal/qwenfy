"""
统一翻译模型接口
P0-003: 抽象类支持 translate() 和 stream()
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional


class TranslationError(Exception):
    """翻译错误基类"""

    def __init__(
        self,
        message: str,
        engine: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.engine = engine
        self.original_error = original_error


class EngineType(Enum):
    """翻译引擎类型"""

    LOCAL = "local"
    CLOUD = "cloud"
    CACHE = "cache"


class EngineStatus(Enum):
    """引擎状态"""

    READY = "ready"
    LOADING = "loading"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class TranslationResult:
    """翻译结果"""

    text: str
    source_lang: str
    target_lang: str
    engine: EngineType
    response_time_ms: float
    cached: bool = False
    confidence: Optional[float] = None
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return bool(self.text)


@dataclass
class TranslationRequest:
    """翻译请求"""

    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    use_cache: bool = True
    stream: bool = False
    timeout_ms: int = 3000
    context: Optional[str] = None
    style: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise TranslationError("翻译文本不能为空")
        self.text = self.text.strip()


class BaseTranslator(ABC):
    """
    翻译引擎基类
    所有翻译引擎（本地/云端/缓存）必须实现此接口
    """

    engine_type: EngineType = EngineType.LOCAL
    max_retries: int = 3
    retry_delay_ms: int = 100

    def __init__(self):
        self._status: EngineStatus = EngineStatus.READY
        self._error_count: int = 0
        self._total_requests: int = 0
        self._total_time_ms: float = 0.0

    @abstractmethod
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """
        翻译文本

        Args:
            request: 翻译请求

        Returns:
            TranslationResult: 翻译结果

        Raises:
            TranslationError: 翻译失败时抛出
        """
        pass

    @abstractmethod
    async def translate_stream(self, request: TranslationRequest) -> AsyncGenerator[str, None]:
        """
        流式翻译

        Args:
            request: 翻译请求

        Yields:
            str: 翻译结果的增量文本

        Raises:
            TranslationError: 翻译失败时抛出
        """
        if False:
            yield

    @property
    def status(self) -> EngineStatus:
        """引擎状态"""
        return self._status

    @property
    def is_available(self) -> bool:
        """引擎是否可用"""
        return self._status == EngineStatus.READY

    @property
    def avg_response_time_ms(self) -> float:
        """平均响应时间(ms)"""
        if self._total_requests == 0:
            return 0.0
        return self._total_time_ms / self._total_requests

    @property
    def error_rate(self) -> float:
        """错误率"""
        if self._total_requests == 0:
            return 0.0
        return self._error_count / self._total_requests

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 引擎是否健康
        """
        try:
            test_request = TranslationRequest(text="Hello", source_lang="en", target_lang="zh")
            result = await self.translate(test_request)
            return result.is_success
        except Exception:
            return False

    def _record_success(self, response_time_ms: float):
        """记录成功请求"""
        self._total_requests += 1
        self._total_time_ms += response_time_ms

    def _record_error(self):
        """记录错误请求"""
        self._total_requests += 1
        self._error_count += 1

    async def _with_retry(self, request: TranslationRequest, translate_func) -> TranslationResult:
        """
        带重试机制的翻译

        Args:
            request: 翻译请求
            translate_func: 翻译函数

        Returns:
            TranslationResult: 翻译结果
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                return await translate_func(request)
            except TranslationError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await self._sleep(self.retry_delay_ms * (attempt + 1))
            except Exception as e:
                last_error = TranslationError(
                    str(e), engine=self.engine_type.value, original_error=e
                )
                if attempt < self.max_retries - 1:
                    await self._sleep(self.retry_delay_ms * (attempt + 1))

        raise TranslationError(
            f"翻译失败，已重试{self.max_retries}次",
            engine=self.engine_type.value,
            original_error=last_error,
        )

    @staticmethod
    async def _sleep(ms: int):
        """异步睡眠"""
        import asyncio

        await asyncio.sleep(ms / 1000.0)

    @staticmethod
    def _measure_time(start_time: float) -> float:
        """测量耗时(ms)"""
        return (time.perf_counter() - start_time) * 1000


class BaseEngineFactory(ABC):
    """引擎工厂基类"""

    @abstractmethod
    def create_translator(self, config: Dict[str, Any]) -> BaseTranslator:
        """创建翻译器实例"""
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        pass
