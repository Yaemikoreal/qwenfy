"""
YuxTrans - AI Translation Tool
响应速度是生命，翻译准度是底线
"""

__version__ = "0.1.0"
__author__ = "YuxTrans Team"

from yuxtrans.cache.database import TranslationCache
from yuxtrans.engine.base import BaseTranslator, TranslationError, TranslationResult

__all__ = [
    "BaseTranslator",
    "TranslationResult",
    "TranslationError",
    "TranslationCache",
    "__version__",
]
