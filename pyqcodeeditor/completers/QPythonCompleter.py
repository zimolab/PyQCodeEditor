from __future__ import annotations

import os
import warnings

from qtpy.QtCore import QObject, QStringListModel, Qt
from qtpy.QtWidgets import QCompleter

from .. import utils
from ..QLanguage import QLanguage


class QPythonCompleter(QCompleter):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)

        _list = []

        lang_file = utils.get_language_file("python.json")
        if not os.path.isfile(lang_file):
            warnings.warn(f"Language file not found: {lang_file}")
            return

        language = QLanguage(lang_file)
        if not language.isLoaded():
            warnings.warn(f"Language file not loaded: {lang_file}")
            return
        keys = language.keys()
        for key in keys:
            names = language.names(key)
            if not names:
                continue
            _list.extend(names)
        self.setModel(QStringListModel(_list, self))
        self.setCompletionColumn(0)
        self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.setCaseSensitivity(Qt.CaseSensitive)
        self.setWrapAround(True)
