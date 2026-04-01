"""
并发控制与请求队列
P2-003: 避免API限流，平滑请求
"""

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Dict, Optional


@dataclass
class RateLimitConfig:
    """限流配置"""

    requests_per_second: float = 10.0
    burst_size: int = 5
    cooldown_ms: int = 1000


@dataclass
class RequestQueueConfig:
    """请求队列配置"""

    max_queue_size: int = 100
    max_concurrent: int = 10
    timeout_ms: int = 5000
    priority_queues: bool = True


@dataclass
class QueuedRequest:
    """队列中的请求"""

    id: str
    func: Awaitable
    args: tuple
    kwargs: dict
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    result: Any = None
    error: Optional[Exception] = None
    completed: bool = False


class RateLimiter:
    """
    速率限制器

    使用令牌桶算法实现平滑限流
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()

        self._tokens = self.config.burst_size
        self._last_update = time.perf_counter()
        self._lock = threading.Lock()

    async def acquire(self) -> bool:
        """
        获取令牌

        Returns:
            bool: 是否成功获取令牌
        """
        with self._lock:
            now = time.perf_counter()
            elapsed = now - self._last_update

            self._tokens += elapsed * self.config.requests_per_second
            self._tokens = min(self._tokens, self.config.burst_size)

            self._last_update = now

            if self._tokens >= 1:
                self._tokens -= 1
                return True

            wait_time = (1 - self._tokens) / self.config.requests_per_second
            wait_time = min(wait_time, self.config.cooldown_ms / 1000)

        await asyncio.sleep(wait_time)
        return await self.acquire()

    def get_status(self) -> Dict[str, Any]:
        """获取限流器状态"""
        with self._lock:
            return {
                "tokens": self._tokens,
                "burst_size": self.config.burst_size,
                "rate": self.config.requests_per_second,
            }


class RequestQueue:
    """
    请求队列

    支持优先级队列和并发控制
    """

    def __init__(self, config: Optional[RequestQueueConfig] = None):
        self.config = config or RequestQueueConfig()

        self._queue: deque = deque()
        self._priority_queue: deque = deque()
        self._active_requests: Dict[str, QueuedRequest] = {}
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._lock = threading.Lock()
        self._request_counter = 0

    def enqueue(self, func: Awaitable, *args, priority: int = 0, **kwargs) -> str:
        """
        加入队列

        Args:
            func: 要执行的异步函数
            *args: 函数参数
            priority: 优先级 (越大越优先)
            **kwargs: 函数关键字参数

        Returns:
            str: 请求ID
        """
        with self._lock:
            if len(self._queue) + len(self._priority_queue) >= self.config.max_queue_size:
                raise RuntimeError("队列已满")

            self._request_counter += 1
            request_id = f"req_{self._request_counter}"

            request = QueuedRequest(
                id=request_id,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=priority,
            )

            if self.config.priority_queues and priority > 0:
                self._priority_queue.append(request)
            else:
                self._queue.append(request)

            return request_id

    async def process_queue(self):
        """
        处理队列中的请求
        """
        while True:
            request = self._get_next_request()

            if request is None:
                await asyncio.sleep(0.01)
                continue

            asyncio.create_task(self._process_request(request))

    def _get_next_request(self) -> Optional[QueuedRequest]:
        """获取下一个请求"""
        with self._lock:
            if self._priority_queue:
                return self._priority_queue.popleft()
            if self._queue:
                return self._queue.popleft()
            return None

    async def _process_request(self, request: QueuedRequest):
        """处理单个请求"""
        async with self._semaphore:
            self._active_requests[request.id] = request

            try:
                timeout = self.config.timeout_ms / 1000
                result = await asyncio.wait_for(
                    request.func(*request.args, **request.kwargs),
                    timeout=timeout,
                )
                request.result = result
                request.completed = True

            except Exception as e:
                request.error = e
                request.completed = True

            finally:
                with self._lock:
                    if request.id in self._active_requests:
                        del self._active_requests[request.id]

    async def execute(self, func: Awaitable, *args, priority: int = 0, **kwargs) -> Any:
        """
        执行请求 (等待结果)

        Args:
            func: 要执行的异步函数
            *args: 函数参数
            priority: 优先级
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        request_id = self.enqueue(func, *args, priority=priority, **kwargs)

        request = None
        for req in list(self._queue) + list(self._priority_queue):
            if req.id == request_id:
                request = req
                break

        if request is None:
            request = self._active_requests.get(request_id)

        if request is None:
            raise RuntimeError("请求未找到")

        start_time = time.perf_counter()
        timeout = self.config.timeout_ms / 1000

        while time.perf_counter() - start_time < timeout:
            if request.completed:
                if request.error:
                    raise request.error
                return request.result

            await asyncio.sleep(0.01)

        raise asyncio.TimeoutError("请求超时")

    def get_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "priority_queue_size": len(self._priority_queue),
                "active_requests": len(self._active_requests),
                "max_queue_size": self.config.max_queue_size,
                "max_concurrent": self.config.max_concurrent,
            }

    def clear(self):
        """清空队列"""
        with self._lock:
            self._queue.clear()
            self._priority_queue.clear()


class ConcurrencyController:
    """
    并发控制器

    组合限流器和请求队列
    """

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        queue_config: Optional[RequestQueueConfig] = None,
    ):
        self.rate_limiter = RateLimiter(rate_limit_config)
        self.queue = RequestQueue(queue_config)

    async def execute(self, func: Awaitable, *args, priority: int = 0, **kwargs) -> Any:
        """
        受控执行

        Args:
            func: 异步函数
            *args: 函数参数
            priority: 优先级
            **kwargs: 关键字参数

        Returns:
            执行结果
        """
        await self.rate_limiter.acquire()

        return await self.queue.execute(func, *args, priority=priority, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        return {
            "rate_limiter": self.rate_limiter.get_status(),
            "queue": self.queue.get_status(),
        }
