"""
本地模型翻译引擎
P1-002: Ollama 本地模型推理
"""

import asyncio
import time
from typing import AsyncGenerator, Optional

try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from yuxtrans.engine.base import (
    BaseTranslator,
    EngineStatus,
    EngineType,
    TranslationError,
    TranslationRequest,
    TranslationResult,
)


class LocalTranslator(BaseTranslator):
    """
    Ollama 本地模型翻译器

    目标：首次翻译 < 2s，后续 < 500ms
    """

    engine_type = EngineType.LOCAL
    DEFAULT_MODEL = "qwen2:7b"
    DEFAULT_TIMEOUT_MS = 5000

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        temperature: float = 0.3,
        prompt_template: Optional[str] = None,
    ):
        super().__init__()
        self.model = model
        self.timeout_ms = timeout_ms
        self.temperature = temperature
        self.prompt_template = prompt_template or self._default_prompt_template()

        if not OLLAMA_AVAILABLE:
            self._status = EngineStatus.UNAVAILABLE
        else:
            self._status = EngineStatus.READY

    @staticmethod
    def _default_prompt_template() -> str:
        return (
            "Translate the following text from {source_lang} to {target_lang}. "
            "Provide only the translation, without any explanation or additional text.\n\n"
            "Text to translate:\n{text}"
        )

    def _build_prompt(self, request: TranslationRequest) -> str:
        return self.prompt_template.format(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            text=request.text,
        )

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        if not self.is_available:
            raise TranslationError(
                "本地模型不可用（Ollama未安装或未启动）", engine=self.engine_type.value
            )

        start_time = time.perf_counter()

        try:
            prompt = self._build_prompt(request)

            def _call_ollama():
                return ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": self.temperature,
                    },
                )

            response = await asyncio.get_event_loop().run_in_executor(None, _call_ollama)

            translated_text = response.get("message", {}).get("content", "")
            translated_text = translated_text.strip()

            response_time = self._measure_time(start_time)
            self._record_success(response_time)

            return TranslationResult(
                text=translated_text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                engine=self.engine_type,
                response_time_ms=response_time,
                cached=False,
                metadata={"model": self.model},
            )

        except Exception as e:
            response_time = self._measure_time(start_time)
            self._record_error()
            raise TranslationError(
                f"本地翻译失败: {str(e)}",
                engine=self.engine_type.value,
                original_error=e,
            )

    async def translate_stream(self, request: TranslationRequest) -> AsyncGenerator[str, None]:
        if not self.is_available:
            raise TranslationError("本地模型不可用", engine=self.engine_type.value)

        prompt = self._build_prompt(request)

        try:

            def _stream_ollama():
                for chunk in ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    options={"temperature": self.temperature},
                ):
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content

            for chunk in _stream_ollama():
                yield chunk

        except Exception as e:
            raise TranslationError(
                f"流式翻译失败: {str(e)}",
                engine=self.engine_type.value,
                original_error=e,
            )

    async def health_check(self) -> bool:
        if not OLLAMA_AVAILABLE:
            return False

        try:
            models = ollama.list()
            return any(m.get("name") == self.model for m in models.get("models", []))
        except Exception:
            return False

    async def preload_model(self) -> bool:
        """预加载模型到内存"""
        if not OLLAMA_AVAILABLE:
            return False

        try:
            await asyncio.get_event_loop().run_in_executor(None, lambda: ollama.pull(self.model))
            return True
        except Exception:
            return False
