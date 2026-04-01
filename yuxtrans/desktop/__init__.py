"""
桌面客户端模块
"""

from yuxtrans.desktop.hotkey import DefaultHotkeys, Hotkey, HotkeyManager, HotkeyState
from yuxtrans.desktop.selection import SelectionButton, SelectionManager, SelectionResult
from yuxtrans.desktop.settings import SettingsDialog
from yuxtrans.desktop.tray import TrayApplication, TrayIcon, main
from yuxtrans.desktop.window import TranslationWindow, TranslationWorker

__all__ = [
    "TrayApplication",
    "TrayIcon",
    "main",
    "HotkeyManager",
    "Hotkey",
    "HotkeyState",
    "DefaultHotkeys",
    "SelectionManager",
    "SelectionResult",
    "SelectionButton",
    "TranslationWindow",
    "TranslationWorker",
    "SettingsDialog",
]
