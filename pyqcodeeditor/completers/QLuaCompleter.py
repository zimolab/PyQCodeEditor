from __future__ import annotations

from qtpy.QtCore import QObject

from ..QLanguageCompleter import QLanguageCompleter


class QLuaCompleter(QLanguageCompleter):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

    def languageFile(self) -> str:
        return "lua.json"

    def isBuiltinLanguage(self) -> bool:
        return True
