"""
长文本分段策略
P5-003: 保持上下文连贯
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class SplitStrategy(Enum):
    """分段策略"""

    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FIXED_LENGTH = "fixed_length"
    SMART = "smart"


@dataclass
class TextSegment:
    """文本段"""

    index: int
    text: str
    start: int
    end: int
    context_before: Optional[str] = None
    context_after: Optional[str] = None


class TextSplitter:
    """
    文本分段器

    智能分割长文本，保持语义完整性
    """

    DEFAULT_MAX_LENGTH = 1000
    DEFAULT_OVERLAP = 100

    SENTENCE_ENDINGS = [
        "。",
        "！",
        "？",
        "…",
        ".",
        "!",
        "?",
        "．",
        "！",
        "？",
    ]

    PARAGRAPH_SEPARATORS = [
        "\n\n",
        "\r\n\r\n",
        "\n",
        "\r\n",
    ]

    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        overlap: int = DEFAULT_OVERLAP,
        strategy: SplitStrategy = SplitStrategy.SMART,
    ):
        self.max_length = max_length
        self.overlap = overlap
        self.strategy = strategy

    def split(self, text: str) -> List[TextSegment]:
        """
        分割文本

        Args:
            text: 原始文本

        Returns:
            文本段列表
        """
        if len(text) <= self.max_length:
            return [
                TextSegment(
                    index=0,
                    text=text,
                    start=0,
                    end=len(text),
                )
            ]

        if self.strategy == SplitStrategy.SENTENCE:
            return self._split_by_sentence(text)
        elif self.strategy == SplitStrategy.PARAGRAPH:
            return self._split_by_paragraph(text)
        elif self.strategy == SplitStrategy.FIXED_LENGTH:
            return self._split_by_length(text)
        else:
            return self._split_smart(text)

    def _split_by_sentence(self, text: str) -> List[TextSegment]:
        """按句子分割"""
        sentences = []
        current = ""

        for char in text:
            current += char
            if char in self.SENTENCE_ENDINGS:
                sentences.append(current.strip())
                current = ""

        if current.strip():
            sentences.append(current.strip())

        return self._merge_sentences(sentences)

    def _split_by_paragraph(self, text: str) -> List[TextSegment]:
        """按段落分割"""
        paragraphs = []
        current = ""

        for char in text:
            current += char
            if char == "\n":
                paragraphs.append(current.strip())
                current = ""

        if current.strip():
            paragraphs.append(current.strip())

        return self._create_segments(paragraphs)

    def _split_by_length(self, text: str) -> List[TextSegment]:
        """按固定长度分割"""
        segments = []

        for i in range(0, len(text), self.max_length - self.overlap):
            chunk = text[i : i + self.max_length]

            segments.append(
                TextSegment(
                    index=len(segments),
                    text=chunk,
                    start=i,
                    end=min(i + self.max_length, len(text)),
                )
            )

        return segments

    def _split_smart(self, text: str) -> List[TextSegment]:
        """
        智能分割

        结合句子边界和长度限制
        """
        sentences = []
        current = ""

        for char in text:
            current += char
            if char in self.SENTENCE_ENDINGS:
                if len(current.strip()) > 0:
                    sentences.append(current.strip())
                current = ""

        if current.strip():
            sentences.append(current.strip())

        segments = []
        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.max_length and current_chunk:
                segments.append(
                    TextSegment(
                        index=len(segments),
                        text=current_chunk.strip(),
                        start=current_start,
                        end=current_start + len(current_chunk),
                    )
                )

                if self.overlap > 0 and segments:
                    last_text = segments[-1].text
                    overlap_text = (
                        last_text[-self.overlap :] if len(last_text) > self.overlap else last_text
                    )
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence

                current_start = current_start + len(current_chunk) - len(sentence)
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk.strip():
            segments.append(
                TextSegment(
                    index=len(segments),
                    text=current_chunk.strip(),
                    start=current_start,
                    end=len(text),
                )
            )

        return segments

    def _merge_sentences(self, sentences: List[str]) -> List[TextSegment]:
        """合并句子到合适长度"""
        segments = []
        current = ""
        current_start = 0
        offset = 0

        for sentence in sentences:
            if len(current) + len(sentence) > self.max_length and current:
                segments.append(
                    TextSegment(
                        index=len(segments),
                        text=current.strip(),
                        start=current_start,
                        end=offset,
                    )
                )
                current = sentence
                current_start = offset
            else:
                current += " " + sentence if current else sentence

            offset += len(sentence) + 1

        if current.strip():
            segments.append(
                TextSegment(
                    index=len(segments),
                    text=current.strip(),
                    start=current_start,
                    end=offset,
                )
            )

        return segments

    def _create_segments(self, chunks: List[str]) -> List[TextSegment]:
        """创建文本段"""
        segments = []
        offset = 0

        for chunk in chunks:
            if chunk:
                segments.append(
                    TextSegment(
                        index=len(segments),
                        text=chunk,
                        start=offset,
                        end=offset + len(chunk),
                    )
                )
            offset += len(chunk) + 1

        return segments


class ContextManager:
    """
    上下文管理器

    管理分段翻译的上下文信息
    """

    DEFAULT_CONTEXT_LENGTH = 200

    def __init__(self, context_length: int = DEFAULT_CONTEXT_LENGTH):
        self.context_length = context_length

    def add_context(self, segments: List[TextSegment]) -> List[TextSegment]:
        """
        为每个段添加上下文

        Args:
            segments: 文本段列表

        Returns:
            带上下文的文本段列表
        """
        if not segments:
            return segments

        result = []

        for i, segment in enumerate(segments):
            context_before = None
            context_after = None

            if i > 0:
                prev_text = segments[i - 1].text
                context_before = (
                    prev_text[-self.context_length :]
                    if len(prev_text) > self.context_length
                    else prev_text
                )

            if i < len(segments) - 1:
                next_text = segments[i + 1].text
                context_after = (
                    next_text[: self.context_length]
                    if len(next_text) > self.context_length
                    else next_text
                )

            result.append(
                TextSegment(
                    index=segment.index,
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    context_before=context_before,
                    context_after=context_after,
                )
            )

        return result

    def build_prompt_with_context(
        self,
        segment: TextSegment,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """构建带上下文的翻译提示"""
        prompt = f"Translate the following text from {source_lang} to {target_lang}.\n\n"

        if segment.context_before:
            prompt += f"[Previous context: ...{segment.context_before}]\n\n"

        prompt += f"Text to translate:\n{segment.text}\n\n"

        if segment.context_after:
            prompt += f"[Following context: {segment.context_after}...]\n"

        prompt += "\nProvide only the translation, maintaining coherence with the context."

        return prompt


class LongTextTranslator:
    """
    长文本翻译器

    处理超过长度限制的文本
    """

    def __init__(
        self,
        translator,
        splitter: Optional[TextSplitter] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        self.translator = translator
        self.splitter = splitter or TextSplitter()
        self.context_manager = context_manager or ContextManager()

    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
    ) -> Tuple[str, Dict]:
        """
        翻译长文本

        Args:
            text: 原始文本
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            (翻译结果, 元数据)
        """
        segments = self.splitter.split(text)

        if len(segments) == 1:
            from yuxtrans.engine.base import TranslationRequest

            request = TranslationRequest(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
            )
            result = await self.translator.translate(request)
            return result.text, {"segments": 1}

        segments = self.context_manager.add_context(segments)

        translations = []

        for segment in segments:
            prompt = self.context_manager.build_prompt_with_context(
                segment,
                source_lang,
                target_lang,
            )

            from yuxtrans.engine.base import TranslationRequest

            request = TranslationRequest(
                text=prompt,
                source_lang=source_lang,
                target_lang=target_lang,
            )

            result = await self.translator.translate(request)
            translations.append(result.text)

        merged = self._merge_translations(translations)

        return merged, {
            "segments": len(segments),
            "original_length": len(text),
            "translated_length": len(merged),
        }

    def _merge_translations(self, translations: List[str]) -> str:
        """合并翻译结果"""
        cleaned = []

        for t in translations:
            t = t.strip()

            if t.startswith("[Previous context:") or t.startswith("[Following context:"):
                lines = t.split("\n")
                t = "\n".join(
                    line
                    for line in lines
                    if not line.startswith("[Previous context:")
                    and not line.startswith("[Following context:")
                )

            cleaned.append(t)

        result = ""
        for t in cleaned:
            if result and not result.endswith(("\n", "。", ".", "！", "!", "？", "?")):
                result += " "
            result += t

        return result
