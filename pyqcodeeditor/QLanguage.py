from __future__ import annotations

import json
from typing import List, Dict


# noinspection PyPep8Naming
class QLanguage(object):
    def __init__(self, file: str | None = None):
        super().__init__()
        self._loaded: bool = False
        self._list: Dict[str, List[str]] = {}
        if file:
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
            self._list[section_name] = section
            self._loaded = True
        return self._loaded

    def keys(self) -> List[str]:
        return list(self._list.keys())

    def names(self, key: str) -> List[str]:
        if key in self._list:
            return self._list[key]
        return []

    def isLoaded(self) -> bool:
        return self._loaded
