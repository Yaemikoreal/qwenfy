"""
术语库/自定义词典
P5-001: 专业领域准确率提升
"""

import json
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class Term:
    """术语条目"""

    source: str
    target: str
    category: str = "general"
    case_sensitive: bool = False
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "category": self.category,
            "case_sensitive": self.case_sensitive,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Term":
        return cls(
            source=data["source"],
            target=data["target"],
            category=data.get("category", "general"),
            case_sensitive=data.get("case_sensitive", False),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )


class TerminologyDatabase:
    """
    术语数据库

    功能：
    - 术语存储与查询
    - 分类管理
    - 优先级匹配
    - 导入导出
    """

    DEFAULT_DB_PATH = "~/.yuxtrans/terminology.json"

    DEFAULT_TERMS = {
        "tech": [
            ("API", "应用程序接口"),
            ("SDK", "软件开发工具包"),
            ("CPU", "中央处理器"),
            ("GPU", "图形处理器"),
            ("RAM", "随机存取存储器"),
            ("SSD", "固态硬盘"),
            ("HTTP", "超文本传输协议"),
            ("HTTPS", "安全超文本传输协议"),
            ("JSON", "JavaScript对象表示法"),
            ("XML", "可扩展标记语言"),
        ],
        "business": [
            ("ROI", "投资回报率"),
            ("KPI", "关键绩效指标"),
            ("B2B", "企业对企业"),
            ("B2C", "企业对消费者"),
            ("CEO", "首席执行官"),
            ("CTO", "首席技术官"),
            ("IPO", "首次公开募股"),
        ],
        "medical": [
            ("DNA", "脱氧核糖核酸"),
            ("RNA", "核糖核酸"),
            ("MRI", "磁共振成像"),
            ("CT", "计算机断层扫描"),
            ("ICU", "重症监护室"),
        ],
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or self.DEFAULT_DB_PATH).expanduser()
        self._terms: Dict[str, Term] = {}
        self._index: Dict[str, Set[str]] = {}
        self._categories: Set[str] = set()
        self._lock = threading.RLock()

        self._load_database()

    def _load_database(self):
        """加载数据库"""
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for term_data in data.get("terms", []):
                    term = Term.from_dict(term_data)
                    self._add_term_internal(term)

            except Exception:
                self._load_defaults()
        else:
            self._load_defaults()

    def _load_defaults(self):
        """加载默认术语"""
        for category, terms in self.DEFAULT_TERMS.items():
            for source, target in terms:
                term = Term(
                    source=source,
                    target=target,
                    category=category,
                    priority=10,
                )
                self._add_term_internal(term)

        self.save()

    def _add_term_internal(self, term: Term):
        """内部添加术语"""
        key = self._make_key(term.source, term.case_sensitive)
        self._terms[key] = term
        self._categories.add(term.category)

        if term.category not in self._index:
            self._index[term.category] = set()
        self._index[term.category].add(key)

    def _make_key(self, source: str, case_sensitive: bool = False) -> str:
        """生成键"""
        return source if case_sensitive else source.lower()

    def add_term(
        self,
        source: str,
        target: str,
        category: str = "general",
        case_sensitive: bool = False,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加术语

        Args:
            source: 源术语
            target: 目标翻译
            category: 分类
            case_sensitive: 是否区分大小写
            priority: 优先级
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        with self._lock:
            term = Term(
                source=source,
                target=target,
                category=category,
                case_sensitive=case_sensitive,
                priority=priority,
                metadata=metadata or {},
            )

            key = self._make_key(source, case_sensitive)

            if key in self._terms:
                existing = self._terms[key]
                if existing.priority > priority:
                    return False

            self._add_term_internal(term)
            return True

    def remove_term(self, source: str, case_sensitive: bool = False) -> bool:
        """删除术语"""
        with self._lock:
            key = self._make_key(source, case_sensitive)

            if key in self._terms:
                term = self._terms[key]
                del self._terms[key]

                if term.category in self._index:
                    self._index[term.category].discard(key)

                return True

            return False

    def lookup(self, source: str, category: Optional[str] = None) -> Optional[Term]:
        """
        查询术语

        Args:
            source: 源术语
            category: 限制分类

        Returns:
            Term 或 None
        """
        with self._lock:
            key_lower = source.lower()

            if key_lower in self._terms:
                term = self._terms[key_lower]
                if category is None or term.category == category:
                    return term

            if source in self._terms:
                term = self._terms[source]
                if term.case_sensitive and (category is None or term.category == category):
                    return term

            return None

    def apply_to_text(self, text: str, category: Optional[str] = None) -> str:
        """
        应用术语到文本

        将文本中的术语替换为目标翻译

        Args:
            text: 原始文本
            category: 限制分类

        Returns:
            处理后的文本
        """
        with self._lock:
            terms_to_apply = []

            for key, term in self._terms.items():
                if category and term.category != category:
                    continue
                terms_to_apply.append(term)

            terms_to_apply.sort(key=lambda t: len(t.source), reverse=True)

            result = text
            for term in terms_to_apply:
                if term.case_sensitive:
                    result = result.replace(term.source, term.target)
                else:
                    pattern = re.compile(re.escape(term.source), re.IGNORECASE)
                    result = pattern.sub(term.target, result)

            return result

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        with self._lock:
            return sorted(self._categories)

    def get_terms_by_category(self, category: str) -> List[Term]:
        """获取分类下的所有术语"""
        with self._lock:
            if category not in self._index:
                return []

            return [self._terms[key] for key in self._index[category]]

    def search(self, query: str, limit: int = 20) -> List[Term]:
        """搜索术语"""
        with self._lock:
            query_lower = query.lower()
            results = []

            for term in self._terms.values():
                if query_lower in term.source.lower() or query_lower in term.target.lower():
                    results.append(term)
                    if len(results) >= limit:
                        break

            return results

    def save(self):
        """保存数据库"""
        with self._lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "terms": [term.to_dict() for term in self._terms.values()],
                "categories": list(self._categories),
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_file(self, filepath: str, format: str = "json"):
        """导出到文件"""
        path = Path(filepath)

        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    [term.to_dict() for term in self._terms.values()],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

        elif format == "csv":
            import csv

            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["source", "target", "category", "priority"])
                for term in self._terms.values():
                    writer.writerow([term.source, term.target, term.category, term.priority])

        elif format == "txt":
            with open(path, "w", encoding="utf-8") as f:
                for term in self._terms.values():
                    f.write(f"{term.source}\t{term.target}\t{term.category}\n")

    def import_from_file(self, filepath: str, format: str = "json"):
        """从文件导入"""
        path = Path(filepath)

        if format == "json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for term_data in data:
                term = Term.from_dict(term_data)
                self._add_term_internal(term)

        elif format == "csv":
            import csv

            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.add_term(
                        source=row["source"],
                        target=row["target"],
                        category=row.get("category", "general"),
                        priority=int(row.get("priority", 0)),
                    )

        elif format == "txt":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        self.add_term(
                            source=parts[0],
                            target=parts[1],
                            category=parts[2] if len(parts) > 2 else "general",
                        )

        self.save()

    def clear(self):
        """清空数据库"""
        with self._lock:
            self._terms.clear()
            self._index.clear()
            self._categories.clear()

    @property
    def stats(self) -> Dict[str, Any]:
        """统计信息"""
        with self._lock:
            return {
                "total_terms": len(self._terms),
                "categories": len(self._categories),
                "terms_per_category": {
                    cat: len(self._index.get(cat, set())) for cat in self._categories
                },
            }


class TerminologyEnhancer:
    """
    术语增强器

    在翻译前后应用术语处理
    """

    def __init__(self, db: TerminologyDatabase):
        self.db = db

    def preprocess(self, text: str, categories: Optional[List[str]] = None) -> str:
        """
        预处理：标记术语

        将术语用特殊标记包裹，防止被错误翻译
        """
        result = text

        if categories:
            for cat in categories:
                result = self._mark_terms(result, cat)
        else:
            result = self._mark_terms(result, None)

        return result

    def _mark_terms(self, text: str, category: Optional[str]) -> str:
        """标记术语"""
        terms = (
            self.db.get_terms_by_category(category) if category else list(self.db._terms.values())
        )

        for term in sorted(terms, key=lambda t: len(t.source), reverse=True):
            pattern = re.compile(
                re.escape(term.source), re.IGNORECASE if not term.case_sensitive else 0
            )
            text = pattern.sub(f"[TERM:{term.target}]", text)

        return text

    def postprocess(self, text: str, categories: Optional[List[str]] = None) -> str:
        """
        后处理：应用术语

        确保翻译结果中的术语使用正确的翻译
        """
        return self.db.apply_to_text(text, categories[0] if categories else None)

    def restore_markers(self, text: str) -> str:
        """恢复标记的术语"""
        return re.sub(r"\[TERM:([^\]]+)\]", r"\1", text)
