from __future__ import annotations

import warnings
from abc import abstractmethod
from typing import List

from qtpy.QtCore import QStringListModel, Qt, QObject
from qtpy.QtWidgets import QCompleter

from . import utils
from .QLanguage import QLanguage


# noinspection PyPep8Naming
class QLanguageCompleter(QCompleter):
    def __init__(self, parent: QObject | None = None):
        super().__init__([], parent)

        languageDefines = self._loadLanguageDefines()
        self.setModel(QStringListModel(languageDefines, self))
        self.setCompletionColumn(0)
        self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.setCaseSensitivity(Qt.CaseSensitive)
        self.setWrapAround(True)

    @abstractmethod
    def languageFile(self) -> str:
        pass

    @abstractmethod
    def isBuiltinLanguage(self) -> bool:
        pass

    def _loadLanguageDefines(self) -> List[str]:
        langFile = self.languageFile()
        if not langFile:
            warnings.warn("No language file specified for this completer")
            return []

        if self.isBuiltinLanguage():
            language = utils.load_builtin_language(langFile)
            if not language:
                return []
        else:
            language = QLanguage(langFile)
            if not language.isLoaded():
                warnings.warn(f"Failed to load language file: {langFile}")
                return []

        defines = []
        for key in language.keys():
            names = language.names(key)
            if not names:
                continue
            defines.extend(names)
        return defines
