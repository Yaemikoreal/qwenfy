"""
启动速度优化
P5-005: 冷启动 < 3s，热启动 < 1s
"""

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class StartupTask:
    """启动任务"""

    name: str
    func: Callable
    priority: int = 0
    delay_ms: int = 0
    required: bool = True
    duration_ms: float = 0
    completed: bool = False


@dataclass
class StartupProfile:
    """启动性能分析"""

    total_time_ms: float
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_time_ms": self.total_time_ms,
            "tasks": self.tasks,
            "timestamp": self.timestamp.isoformat(),
        }


class StartupOptimizer:
    """
    启动优化器

    通过延迟加载、并行初始化等技术加速启动
    """

    PROFILE_FILE = "~/.yuxtrans/startup_profile.json"

    def __init__(self):
        self._tasks: Dict[str, StartupTask] = {}
        self._lazy_loaders: Dict[str, Callable] = {}
        self._preload_complete = threading.Event()
        self._profile: Optional[StartupProfile] = None

    def register_task(
        self,
        name: str,
        func: Callable,
        priority: int = 0,
        delay_ms: int = 0,
        required: bool = True,
    ):
        """
        注册启动任务

        Args:
            name: 任务名称
            func: 任务函数
            priority: 优先级 (越小越先执行)
            delay_ms: 延迟执行时间
            required: 是否必须完成才能继续
        """
        self._tasks[name] = StartupTask(
            name=name,
            func=func,
            priority=priority,
            delay_ms=delay_ms,
            required=required,
        )

    def register_lazy_loader(self, name: str, loader: Callable):
        """
        注册延迟加载器

        Args:
            name: 模块名称
            loader: 加载函数
        """
        self._lazy_loaders[name] = loader

    def lazy_load(self, name: str) -> Any:
        """
        延迟加载模块

        Args:
            name: 模块名称

        Returns:
            加载的模块
        """
        if name in self._lazy_loaders:
            return self._lazy_loaders[name]()
        return None

    def run_startup(self) -> StartupProfile:
        """
        执行启动流程

        Returns:
            启动性能分析
        """
        start_time = time.perf_counter()
        task_results = []

        sorted_tasks = sorted(self._tasks.values(), key=lambda t: t.priority)

        required_tasks = [t for t in sorted_tasks if t.required]
        for task in required_tasks:
            task_start = time.perf_counter()

            try:
                if task.delay_ms > 0:
                    time.sleep(task.delay_ms / 1000)

                task.func()
                task.completed = True

            except Exception:
                if task.required:
                    raise

            task.duration_ms = (time.perf_counter() - task_start) * 1000

            task_results.append(
                {
                    "name": task.name,
                    "duration_ms": task.duration_ms,
                    "completed": task.completed,
                    "required": task.required,
                }
            )

        total_time_ms = (time.perf_counter() - start_time) * 1000

        self._profile = StartupProfile(
            total_time_ms=total_time_ms,
            tasks=task_results,
        )

        threading.Thread(target=self._run_delayed_tasks, daemon=True).start()

        self._save_profile()

        return self._profile

    def _run_delayed_tasks(self):
        """运行延迟任务"""
        delayed_tasks = [t for t in self._tasks.values() if not t.required]

        for task in sorted(delayed_tasks, key=lambda t: t.priority):
            try:
                if task.delay_ms > 0:
                    time.sleep(task.delay_ms / 1000)

                task.func()
                task.completed = True

            except Exception:
                pass

        self._preload_complete.set()

    def wait_for_preload(self, timeout_seconds: float = 10):
        """等待预加载完成"""
        self._preload_complete.wait(timeout_seconds)

    def _save_profile(self):
        """保存性能分析"""
        if self._profile is None:
            return

        path = Path(self.PROFILE_FILE).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._profile.to_dict(), f, indent=2)

    def load_previous_profile(self) -> Optional[StartupProfile]:
        """加载上次性能分析"""
        path = Path(self.PROFILE_FILE).expanduser()

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return StartupProfile(
                total_time_ms=data["total_time_ms"],
                tasks=data["tasks"],
            )
        except Exception:
            return None

    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []

        if self._profile is None:
            return ["没有启动性能分析数据"]

        if self._profile.total_time_ms > 3000:
            suggestions.append(f"启动时间 {self._profile.total_time_ms:.0f}ms 超过目标 3s")

        slow_tasks = [t for t in self._profile.tasks if t["duration_ms"] > 500]

        for task in slow_tasks:
            suggestions.append(
                f"任务 '{task['name']}' 耗时 {task['duration_ms']:.0f}ms，考虑优化或延迟加载"
            )

        if not suggestions:
            suggestions.append("启动性能良好")

        return suggestions


class LazyModule:
    """
    延迟加载模块代理

    只有在真正使用时才加载模块
    """

    def __init__(self, module_name: str, import_func: Optional[Callable] = None):
        self._module_name = module_name
        self._import_func = import_func
        self._module = None
        self._lock = threading.Lock()

    def _load(self):
        """加载模块"""
        if self._module is None:
            with self._lock:
                if self._module is None:
                    if self._import_func:
                        self._module = self._import_func()
                    else:
                        import importlib

                        self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name):
        module = self._load()
        return getattr(module, name)

    def __repr__(self):
        if self._module is None:
            return f"<LazyModule: {self._module_name} (not loaded)>"
        return repr(self._module)


class FastStartup:
    """
    快速启动管理器

    针对桌面应用的启动优化
    """

    def __init__(self):
        self.optimizer = StartupOptimizer()
        self._is_warm = False
        self._setup_default_tasks()

    def _setup_default_tasks(self):
        """设置默认启动任务"""
        self.optimizer.register_task(
            "load_config",
            self._load_config,
            priority=0,
            required=True,
        )

        self.optimizer.register_task(
            "init_cache",
            self._init_cache,
            priority=10,
            required=True,
        )

        self.optimizer.register_task(
            "warmup_cache",
            self._warmup_cache,
            priority=50,
            required=False,
            delay_ms=500,
        )

        self.optimizer.register_task(
            "init_gui",
            self._init_gui,
            priority=20,
            required=False,
        )

    def _load_config(self):
        """加载配置"""
        from yuxtrans.utils.config import ConfigManager

        self.config = ConfigManager()
        self.config.load()

    def _init_cache(self):
        """初始化缓存"""
        from yuxtrans.cache.database import TranslationCache

        self.cache = TranslationCache(preload_popular=False)

    def _warmup_cache(self):
        """预热缓存"""
        if hasattr(self, "cache"):
            import asyncio

            from yuxtrans.cache.warmup import CacheWarmupStrategy

            warmup = CacheWarmupStrategy(self.cache)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(warmup.warmup_common_words())
            loop.close()

    def _init_gui(self):
        """初始化GUI"""
        pass

    def startup(self) -> StartupProfile:
        """执行启动"""
        profile = self.optimizer.run_startup()
        self._is_warm = True
        return profile

    def is_warm(self) -> bool:
        """是否已预热"""
        return self._is_warm

    def get_router(self):
        """获取路由器"""
        from yuxtrans.engine.router import SmartRouter

        return SmartRouter(cache=getattr(self, "cache", None))


def measure_startup_time(func: Callable) -> Callable:
    """
    测量启动时间装饰器

    用法:
        @measure_startup_time
        def main():
            ...
    """

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        status = "✓" if elapsed_ms < 3000 else "✗"
        print(f"[Startup] {status} 启动完成: {elapsed_ms:.0f}ms")

        return result

    return wrapper
