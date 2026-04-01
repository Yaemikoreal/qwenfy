"""
翻译风格选择
P5-002: 正式/口语/学术风格
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TranslationStyle(Enum):
    """翻译风格"""

    FORMAL = "formal"
    INFORMAL = "informal"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    DEFAULT = "default"


@dataclass
class StyleConfig:
    """风格配置"""

    name: str
    description: str
    temperature: float
    prompt_suffix: str
    constraints: List[str]


STYLE_CONFIGS: Dict[TranslationStyle, StyleConfig] = {
    TranslationStyle.FORMAL: StyleConfig(
        name="正式",
        description="适用于商务、官方文档",
        temperature=0.3,
        prompt_suffix="请使用正式、专业的语言风格进行翻译。避免使用口语化表达。",
        constraints=[
            "使用书面语",
            "避免缩略语",
            "保持专业性",
        ],
    ),
    TranslationStyle.INFORMAL: StyleConfig(
        name="口语",
        description="适用于日常对话、社交媒体",
        temperature=0.5,
        prompt_suffix="请使用自然、口语化的语言风格进行翻译。可以使用日常表达。",
        constraints=[
            "使用口语化表达",
            "允许使用俚语",
            "保持轻松自然",
        ],
    ),
    TranslationStyle.ACADEMIC: StyleConfig(
        name="学术",
        description="适用于学术论文、研究报告",
        temperature=0.2,
        prompt_suffix="请使用学术、严谨的语言风格进行翻译。保持专业术语的准确性。",
        constraints=[
            "使用学术用语",
            "保持严谨性",
            "术语准确",
            "逻辑清晰",
        ],
    ),
    TranslationStyle.TECHNICAL: StyleConfig(
        name="技术",
        description="适用于技术文档、编程相关",
        temperature=0.2,
        prompt_suffix="请使用技术文档的语言风格进行翻译。保持技术术语的准确性，代码和命令不要翻译。",
        constraints=[
            "保持技术术语",
            "代码不翻译",
            "精确描述",
        ],
    ),
    TranslationStyle.CREATIVE: StyleConfig(
        name="创意",
        description="适用于文学作品、广告文案",
        temperature=0.7,
        prompt_suffix="请进行创意翻译，可以适当调整表达方式以更好地传达原文的意境和情感。",
        constraints=[
            "保持原意",
            "表达优美",
            "情感传递",
        ],
    ),
    TranslationStyle.DEFAULT: StyleConfig(
        name="标准",
        description="通用翻译风格",
        temperature=0.3,
        prompt_suffix="",
        constraints=[],
    ),
}


class StyleManager:
    """
    翻译风格管理器

    管理不同翻译风格的配置和应用
    """

    def __init__(self):
        self._current_style = TranslationStyle.DEFAULT
        self._custom_styles: Dict[str, StyleConfig] = {}

    def get_style(self, style: TranslationStyle) -> StyleConfig:
        """获取风格配置"""
        return STYLE_CONFIGS.get(style, STYLE_CONFIGS[TranslationStyle.DEFAULT])

    def set_current_style(self, style: TranslationStyle):
        """设置当前风格"""
        self._current_style = style

    def get_current_style(self) -> TranslationStyle:
        """获取当前风格"""
        return self._current_style

    def get_current_config(self) -> StyleConfig:
        """获取当前风格配置"""
        return self.get_style(self._current_style)

    def get_temperature(self, style: Optional[TranslationStyle] = None) -> float:
        """获取温度参数"""
        config = self.get_style(style or self._current_style)
        return config.temperature

    def build_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        style: Optional[TranslationStyle] = None,
    ) -> str:
        """
        构建带风格的翻译提示

        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
            style: 翻译风格

        Returns:
            完整的提示词
        """
        style_config = self.get_style(style or self._current_style)

        base_prompt = f"Translate the following text from {source_lang} to {target_lang}."

        if style_config.prompt_suffix:
            base_prompt += f"\n\n{style_config.prompt_suffix}"

        constraints = style_config.constraints
        if constraints:
            base_prompt += "\n\nRequirements:"
            for i, constraint in enumerate(constraints, 1):
                base_prompt += f"\n{i}. {constraint}"

        base_prompt += f"\n\nText to translate:\n{text}"

        return base_prompt

    def add_custom_style(
        self,
        name: str,
        description: str,
        temperature: float,
        prompt_suffix: str,
        constraints: Optional[List[str]] = None,
    ):
        """添加自定义风格"""
        config = StyleConfig(
            name=name,
            description=description,
            temperature=temperature,
            prompt_suffix=prompt_suffix,
            constraints=constraints or [],
        )
        self._custom_styles[name] = config

    def get_custom_style(self, name: str) -> Optional[StyleConfig]:
        """获取自定义风格"""
        return self._custom_styles.get(name)

    def list_styles(self) -> List[Dict[str, Any]]:
        """列出所有可用风格"""
        styles = []

        for style, config in STYLE_CONFIGS.items():
            styles.append(
                {
                    "id": style.value,
                    "name": config.name,
                    "description": config.description,
                    "temperature": config.temperature,
                }
            )

        for name, config in self._custom_styles.items():
            styles.append(
                {
                    "id": f"custom_{name}",
                    "name": config.name,
                    "description": config.description,
                    "temperature": config.temperature,
                }
            )

        return styles

    def recommend_style(self, text: str, context: Optional[str] = None) -> TranslationStyle:
        """
        推荐翻译风格

        根据文本特征自动推荐合适的风格
        """
        text_lower = text.lower()

        tech_keywords = ["api", "function", "class", "variable", "code", "debug", "error", "server"]
        if any(kw in text_lower for kw in tech_keywords):
            return TranslationStyle.TECHNICAL

        academic_keywords = [
            "research",
            "study",
            "analysis",
            "theory",
            "hypothesis",
            "论文",
            "研究",
        ]
        if any(kw in text_lower for kw in academic_keywords):
            return TranslationStyle.ACADEMIC

        formal_keywords = ["dear", "sincerely", "respectfully", "尊敬", "此致敬礼"]
        if any(kw in text_lower for kw in formal_keywords):
            return TranslationStyle.FORMAL

        informal_keywords = ["hey", "cool", "awesome", "lol", "哈哈", "嘿"]
        if any(kw in text_lower for kw in informal_keywords):
            return TranslationStyle.INFORMAL

        if context:
            context_lower = context.lower()
            if "business" in context_lower or "商务" in context_lower:
                return TranslationStyle.FORMAL
            if "technical" in context_lower or "技术" in context_lower:
                return TranslationStyle.TECHNICAL
            if "academic" in context_lower or "学术" in context_lower:
                return TranslationStyle.ACADEMIC

        return TranslationStyle.DEFAULT


class StyledTranslator:
    """
    带风格的翻译器

    将风格管理集成到翻译流程中
    """

    def __init__(self, translator, style_manager: Optional[StyleManager] = None):
        self.translator = translator
        self.style_manager = style_manager or StyleManager()

    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        style: Optional[TranslationStyle] = None,
        auto_detect: bool = False,
    ):
        """
        带风格的翻译

        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
            style: 翻译风格
            auto_detect: 是否自动检测风格
        """
        if auto_detect and style is None:
            style = self.style_manager.recommend_style(text)

        if style is None:
            style = self.style_manager.get_current_style()

        prompt = self.style_manager.build_prompt(text, source_lang, target_lang, style)

        temperature = self.style_manager.get_temperature(style)

        import time

        from yuxtrans.engine.base import TranslationRequest, TranslationResult

        request = TranslationRequest(
            text=prompt,
            source_lang=source_lang,
            target_lang=target_lang,
            metadata={"style": style.value, "temperature": temperature},
        )

        start_time = time.perf_counter()
        result = await self.translator.translate(request)
        response_time = (time.perf_counter() - start_time) * 1000

        return TranslationResult(
            text=result.text,
            source_lang=source_lang,
            target_lang=target_lang,
            engine=result.engine,
            response_time_ms=response_time,
            metadata={
                **result.metadata,
                "style": style.value,
                "style_name": self.style_manager.get_style(style).name,
            },
        )
