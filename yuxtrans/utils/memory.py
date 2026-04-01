"""
内存优化
P5-004: 长时间运行内存稳定
"""

import gc
import threading
import time
import weakref
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional


@dataclass
class MemoryStats:
    """内存统计"""

    total_mb: float
    used_mb: float
    available_mb: float
    percent: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_mb": self.total_mb,
            "used_mb": self.used_mb,
            "available_mb": self.available_mb,
            "percent": self.percent,
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryMonitor:
    """
    内存监控器

    实时监控内存使用情况
    """

    def __init__(self, warning_threshold_mb: float = 250, critical_threshold_mb: float = 280):
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb

        self._callbacks: Dict[str, Callable] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_stats: Optional[MemoryStats] = None

    def get_memory_usage(self) -> MemoryStats:
        """获取当前内存使用"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            used_mb = memory_info.rss / 1024 / 1024

            system_memory = psutil.virtual_memory()
            total_mb = system_memory.total / 1024 / 1024
            available_mb = system_memory.available / 1024 / 1024
            percent = system_memory.percent

            return MemoryStats(
                total_mb=total_mb,
                used_mb=used_mb,
                available_mb=available_mb,
                percent=percent,
            )

        except ImportError:
            return MemoryStats(
                total_mb=0,
                used_mb=0,
                available_mb=0,
                percent=0,
            )

    def register_callback(self, name: str, callback: Callable):
        """注册回调函数"""
        self._callbacks[name] = callback

    def unregister_callback(self, name: str):
        """注销回调函数"""
        self._callbacks.pop(name, None)

    def start_monitoring(self, interval_seconds: float = 60):
        """开始监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval_seconds: float):
        """监控循环"""
        while not self._stop_event.wait(interval_seconds):
            stats = self.get_memory_usage()
            self._last_stats = stats

            if stats.used_mb >= self.critical_threshold_mb:
                self._notify_callbacks("critical", stats)
            elif stats.used_mb >= self.warning_threshold_mb:
                self._notify_callbacks("warning", stats)

    def _notify_callbacks(self, level: str, stats: MemoryStats):
        """通知回调"""
        for callback in self._callbacks.values():
            try:
                callback(level, stats)
            except Exception:
                pass


class MemoryOptimizer:
    """
    内存优化器

    自动管理内存使用
    """

    def __init__(
        self,
        target_memory_mb: float = 200,
        max_memory_mb: float = 300,
        gc_threshold: int = 100,
    ):
        self.target_memory_mb = target_memory_mb
        self.max_memory_mb = max_memory_mb
        self.gc_threshold = gc_threshold

        self.monitor = MemoryMonitor(
            warning_threshold_mb=target_memory_mb,
            critical_threshold_mb=max_memory_mb,
        )

        self.monitor.register_callback("auto_gc", self._auto_gc_callback)

        self._object_pools: Dict[str, Any] = {}
        self._weak_refs: Dict[str, weakref.ref] = {}

    def _auto_gc_callback(self, level: str, stats: MemoryStats):
        """自动GC回调"""
        if level in ("warning", "critical"):
            self.optimize()

    def optimize(self) -> Dict[str, Any]:
        """
        执行内存优化

        Returns:
            优化结果
        """
        before = self.monitor.get_memory_usage()

        gc.collect()
        gc.collect()
        gc.collect()

        unreachable = gc.collect()

        after = self.monitor.get_memory_usage()

        freed_mb = before.used_mb - after.used_mb

        return {
            "before_mb": before.used_mb,
            "after_mb": after.used_mb,
            "freed_mb": freed_mb,
            "unreachable_objects": unreachable,
        }

    def check_and_optimize(self) -> bool:
        """
        检查并在需要时优化

        Returns:
            是否执行了优化
        """
        stats = self.monitor.get_memory_usage()

        if stats.used_mb >= self.target_memory_mb:
            self.optimize()
            return True

        return False

    def create_object_pool(self, name: str, factory: Callable, max_size: int = 100):
        """创建对象池"""
        self._object_pools[name] = {
            "factory": factory,
            "pool": [],
            "max_size": max_size,
        }

    def get_from_pool(self, name: str):
        """从对象池获取对象"""
        if name in self._object_pools:
            pool_data = self._object_pools[name]
            if pool_data["pool"]:
                return pool_data["pool"].pop()
            return pool_data["factory"]()
        return None

    def return_to_pool(self, name: str, obj):
        """归还对象到池"""
        if name in self._object_pools:
            pool_data = self._object_pools[name]
            if len(pool_data["pool"]) < pool_data["max_size"]:
                pool_data["pool"].append(obj)

    def track_object(self, name: str, obj):
        """使用弱引用跟踪对象"""
        self._weak_refs[name] = weakref.ref(obj)

    def get_tracked_object(self, name: str):
        """获取跟踪的对象"""
        if name in self._weak_refs:
            return self._weak_refs[name]()
        return None

    def start(self):
        """开始监控"""
        self.monitor.start_monitoring()

    def stop(self):
        """停止监控"""
        self.monitor.stop_monitoring()

    @property
    def stats(self) -> MemoryStats:
        """获取当前统计"""
        return self.monitor.get_memory_usage()


class CacheEvictionPolicy:
    """
    缓存淘汰策略
    """

    @staticmethod
    def lru(cache: Dict, max_size: int, key: str = None) -> Optional[str]:
        """LRU 淘汰"""
        if len(cache) <= max_size:
            return None

        oldest_key = next(iter(cache))
        return oldest_key

    @staticmethod
    def lfu(cache: Dict, access_counts: Dict, max_size: int) -> Optional[str]:
        """LFU 淘汰"""
        if len(cache) <= max_size:
            return None

        min_count = float("inf")
        evict_key = None

        for key in cache:
            count = access_counts.get(key, 0)
            if count < min_count:
                min_count = count
                evict_key = key

        return evict_key

    @staticmethod
    def ttl(cache: Dict, timestamps: Dict, ttl_seconds: int) -> list:
        """TTL 淘汰"""

        current_time = time.time()

        expired_keys = []

        for key, timestamp in timestamps.items():
            if current_time - timestamp > ttl_seconds:
                expired_keys.append(key)

        return expired_keys


class MemoryEfficientCache:
    """
    内存高效缓存

    自动淘汰和内存管理
    """

    def __init__(
        self,
        max_size: int = 10000,
        max_memory_mb: float = 50,
        eviction_policy: str = "lru",
    ):
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.eviction_policy = eviction_policy

        self._cache: Dict[str, Any] = {}
        self._access_counts: Dict[str, int] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key in self._cache:
                self._access_counts[key] = self._access_counts.get(key, 0) + 1
                return self._cache[key]
            return None

    def set(self, key: str, value: Any):
        """设置缓存"""

        with self._lock:
            self._check_and_evict()

            self._cache[key] = value
            self._access_counts[key] = 1
            self._timestamps[key] = time.time()

    def _check_and_evict(self):
        """检查并淘汰"""
        while len(self._cache) >= self.max_size:
            evict_key = self._evict_one()
            if evict_key:
                self._remove(evict_key)
            else:
                break

    def _evict_one(self) -> Optional[str]:
        """淘汰一个条目"""
        if self.eviction_policy == "lru":
            return CacheEvictionPolicy.lru(self._cache, self.max_size)
        elif self.eviction_policy == "lfu":
            return CacheEvictionPolicy.lfu(self._cache, self._access_counts, self.max_size)
        return None

    def _remove(self, key: str):
        """移除条目"""
        self._cache.pop(key, None)
        self._access_counts.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_counts.clear()
            self._timestamps.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
