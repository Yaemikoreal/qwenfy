"""
YuxTrans - AI Translation Tool
响应速度是生命，翻译准度是底线
"""

__version__ = "0.1.0"
__author__ = "YuxTrans Team"

from yuxtrans.cache.database import TranslationCache
from yuxtrans.engine.base import (
    BaseTranslator,
    TranslationError,
    TranslationRequest,
    TranslationResult,
)
from yuxtrans.engine.router import SmartRouter

__all__ = [
    "BaseTranslator",
    "TranslationRequest",
    "TranslationResult",
    "TranslationError",
    "TranslationCache",
    "SmartRouter",
    "__version__",
]
