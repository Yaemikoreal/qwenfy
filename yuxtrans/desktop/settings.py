"""
设置对话框
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from yuxtrans.utils.config import ConfigManager


class EngineSettingsTab(QWidget):
    """引擎设置标签页"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        local_group = QGroupBox("本地模型")
        local_layout = QFormLayout(local_group)

        self.prefer_local = QCheckBox()
        self.prefer_local.setChecked(self.config.get("engine", "prefer_local"))
        local_layout.addRow("优先使用本地模型:", self.prefer_local)

        self.local_model = QLineEdit()
        self.local_model.setText(self.config.get("engine", "local_model"))
        local_layout.addRow("模型名称:", self.local_model)

        self.local_timeout = QSpinBox()
        self.local_timeout.setRange(1000, 30000)
        self.local_timeout.setValue(self.config.get("engine", "local_timeout_ms"))
        local_layout.addRow("超时 (ms):", self.local_timeout)

        self.local_temperature = QDoubleSpinBox()
        self.local_temperature.setRange(0.0, 2.0)
        self.local_temperature.setSingleStep(0.1)
        self.local_temperature.setValue(self.config.get("engine", "local_temperature"))
        local_layout.addRow("温度:", self.local_temperature)

        layout.addWidget(local_group)

        cloud_group = QGroupBox("云端API")
        cloud_layout = QFormLayout(cloud_group)

        self.cloud_provider = QComboBox()
        self.cloud_provider.addItems(
            ["qwen", "openai", "deepseek", "anthropic", "groq", "moonshot", "siliconflow", "custom"]
        )
        self.cloud_provider.setCurrentText(self.config.get("engine", "cloud_provider"))
        cloud_layout.addRow("提供商:", self.cloud_provider)

        self.cloud_model = QLineEdit()
        self.cloud_model.setText(self.config.get("engine", "cloud_model"))
        cloud_layout.addRow("模型:", self.cloud_model)

        self.cloud_api_key = QLineEdit()
        self.cloud_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_key = self.config.get("engine", "cloud_api_key")
        if api_key:
            self.cloud_api_key.setText(api_key)
        cloud_layout.addRow("API Key:", self.cloud_api_key)

        # 自定义端点（仅 custom 供应商需要）
        self.custom_endpoint = QLineEdit()
        custom_ep = self.config.get("engine", "custom_endpoint")
        if custom_ep:
            self.custom_endpoint.setText(custom_ep)
        cloud_layout.addRow("自定义端点:", self.custom_endpoint)

        layout.addWidget(cloud_group)

        cache_group = QGroupBox("缓存")
        cache_layout = QFormLayout(cache_group)

        self.cache_enabled = QCheckBox()
        self.cache_enabled.setChecked(self.config.get("engine", "cache_enabled"))
        cache_layout.addRow("启用缓存:", self.cache_enabled)

        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 365)
        self.cache_ttl.setValue(self.config.get("engine", "cache_ttl_days"))
        cache_layout.addRow("缓存天数:", self.cache_ttl)

        # 缓存统计显示
        self.cache_stats_label = QLabel()
        self._update_cache_stats()
        cache_layout.addRow("缓存统计:", self.cache_stats_label)

        # 刷新缓存统计按钮
        refresh_stats_btn = QPushButton("刷新统计")
        refresh_stats_btn.clicked.connect(self._update_cache_stats)
        cache_layout.addRow("", refresh_stats_btn)

        layout.addWidget(cache_group)

        layout.addStretch()

    def _update_cache_stats(self):
        """更新缓存统计显示"""
        try:
            import sqlite3

            db_path = Path.home() / ".yuxtrans" / "cache" / "translations.db"
            if not db_path.exists():
                self.cache_stats_label.setText("0 词汇 | 0 KB")
                return

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM translations")
                word_count = cursor.fetchone()[0]

                # 计算数据库文件大小
                db_size = os.path.getsize(db_path)

                # 选择合适的单位
                if db_size >= 1024 * 1024 * 1024:  # >= 1GB
                    size_str = f"{db_size / (1024 * 1024 * 1024):.2f} GB"
                elif db_size >= 1024 * 1024:  # >= 1MB
                    size_str = f"{db_size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{db_size / 1024:.2f} KB"

                self.cache_stats_label.setText(f"{word_count} 词汇 | {size_str}")
        except Exception as e:
            self.cache_stats_label.setText(f"读取失败: {str(e)}")

    def apply(self):
        """应用设置"""
        self.config.update("engine", "prefer_local", self.prefer_local.isChecked())
        self.config.update("engine", "local_model", self.local_model.text())
        self.config.update("engine", "local_timeout_ms", self.local_timeout.value())
        self.config.update("engine", "local_temperature", self.local_temperature.value())

        self.config.update("engine", "cloud_provider", self.cloud_provider.currentText())
        self.config.update("engine", "cloud_model", self.cloud_model.text())
        if self.cloud_api_key.text():
            self.config.update("engine", "cloud_api_key", self.cloud_api_key.text())
        if self.custom_endpoint.text():
            self.config.update("engine", "custom_endpoint", self.custom_endpoint.text())

        self.config.update("engine", "cache_enabled", self.cache_enabled.isChecked())
        self.config.update("engine", "cache_ttl_days", self.cache_ttl.value())


class UISettingsTab(QWidget):
    """界面设置标签页"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        appearance_group = QGroupBox("外观")
        appearance_layout = QFormLayout(appearance_group)

        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])
        self.theme.setCurrentText(self.config.get("ui", "theme"))
        appearance_layout.addRow("主题:", self.theme)

        self.language = QComboBox()
        self.language.addItems(["zh", "en"])
        self.language.setCurrentText(self.config.get("ui", "language"))
        appearance_layout.addRow("语言:", self.language)

        self.show_engine = QCheckBox()
        self.show_engine.setChecked(self.config.get("ui", "show_engine_indicator"))
        appearance_layout.addRow("显示引擎:", self.show_engine)

        self.show_time = QCheckBox()
        self.show_time.setChecked(self.config.get("ui", "show_response_time"))
        appearance_layout.addRow("显示响应时间:", self.show_time)

        layout.addWidget(appearance_group)

        window_group = QGroupBox("窗口")
        window_layout = QFormLayout(window_group)

        self.window_width = QSpinBox()
        self.window_width.setRange(200, 800)
        self.window_width.setValue(self.config.get("ui", "window_width"))
        window_layout.addRow("宽度:", self.window_width)

        self.window_height = QSpinBox()
        self.window_height.setRange(200, 600)
        self.window_height.setValue(self.config.get("ui", "window_height"))
        window_layout.addRow("高度:", self.window_height)

        self.window_opacity = QDoubleSpinBox()
        self.window_opacity.setRange(0.5, 1.0)
        self.window_opacity.setSingleStep(0.05)
        self.window_opacity.setValue(self.config.get("ui", "window_opacity"))
        window_layout.addRow("透明度:", self.window_opacity)

        layout.addWidget(window_group)

        layout.addStretch()

    def apply(self):
        """应用设置"""
        self.config.update("ui", "theme", self.theme.currentText())
        self.config.update("ui", "language", self.language.currentText())
        self.config.update("ui", "show_engine_indicator", self.show_engine.isChecked())
        self.config.update("ui", "show_response_time", self.show_time.isChecked())

        self.config.update("ui", "window_width", self.window_width.value())
        self.config.update("ui", "window_height", self.window_height.value())
        self.config.update("ui", "window_opacity", self.window_opacity.value())


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config

        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        self.engine_tab = EngineSettingsTab(self.config)
        self.tabs.addTab(self.engine_tab, "引擎")

        self.ui_tab = UISettingsTab(self.config)
        self.tabs.addTab(self.ui_tab, "界面")

        layout.addWidget(self.tabs)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_and_close(self):
        """保存并关闭"""
        self.engine_tab.apply()
        self.ui_tab.apply()
        self.accept()
