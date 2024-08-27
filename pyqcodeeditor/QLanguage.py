from __future__ import annotations

import json
from typing import List, Dict

from qtpy.QtCore import QObject


# noinspection PyPep8Naming
class QLanguage(QObject):

    def __init__(self, file: str = None, parent: QObject | None = None):
        super().__init__(parent)
        self.m_loaded: bool = False
        self.m_list: Dict[str, List[str]] = {}

        self.load(file)

    def load(self, file: str, encoding="utf-8", errors="strict") -> bool:
        if file is None:
            return False

        with open(file, "r", encoding=encoding, errors=errors) as f:
            data = json.load(f)

        if not isinstance(data, dict) or not data:
            return False

        for section_name, section in data.items():
            if not isinstance(section, list):
                continue
            self.m_list[section_name] = section
            self.m_loaded = True
        return self.m_loaded

    def keys(self) -> List[str]:
        return list(self.m_list.keys())

    def names(self, key: str) -> List[str]:
        if key in self.m_list:
            return self.m_list[key]
        return []

    def isLoaded(self) -> bool:
        return self.m_loaded
