from __future__ import annotations

import json
import traceback
import warnings
from typing import Dict, Any

from qtpy.QtCore import QObject
from qtpy.QtGui import QTextCharFormat, QColor, QFont
from . import utils


UNDERLINE_STYLES = {
    "SingleUnderline": QTextCharFormat.UnderlineStyle.SingleUnderline,
    "DashUnderline": QTextCharFormat.UnderlineStyle.DashUnderline,
    "DotLine": QTextCharFormat.UnderlineStyle.DotLine,
    "DashDotLine": QTextCharFormat.UnderlineStyle.DashDotLine,
    "DashDotDotLine": QTextCharFormat.UnderlineStyle.DashDotDotLine,
    "WaveUnderline": QTextCharFormat.UnderlineStyle.WaveUnderline,
    "SpellCheckUnderline": QTextCharFormat.UnderlineStyle.SpellCheckUnderline,
    "NoUnderline": QTextCharFormat.UnderlineStyle.NoUnderline,
}


# noinspection PyPep8Naming
class QSyntaxStyle(object):

    _defaultStyle: QSyntaxStyle | None = None

    def __init__(self):
        self._name: str = ""
        self._loaded: bool = False
        self._data: Dict[str, QTextCharFormat] = {}

    def load(self, file: str, encoding="utf-8", errors="strict") -> bool:
        self._loaded = False
        try:
            with utils.open_resource_text_file(file, encoding, errors) as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self._processStyleSchema(data)
        except Exception as e:
            warnings.warn(f"Can't load style schema: {e}")
            traceback.print_exc()
        return self._loaded

    def name(self) -> str:
        return self._name

    def isLoaded(self) -> bool:
        return self._loaded

    def getFormat(self, name: str) -> QTextCharFormat:
        return self._data.get(name, QTextCharFormat())

    def _processStyleSchema(self, style_schema: Dict[str, Any]):
        name = style_schema.get("name", None)
        if not isinstance(name, str) or name.strip() == "":
            return
        styles = style_schema.get("style", None)
        if not isinstance(styles, list):
            return
        self._loaded = True

        for style in styles:
            if not isinstance(style, dict):
                continue
            style_name = style.get("name", None)
            if not isinstance(style_name, str) or style_name.strip() == "":
                continue
            style_format = QTextCharFormat()

            background = style.get("background", None)
            if background:
                style_format.setBackground(QColor(str(background)))

            foreground = style.get("foreground", None)
            if foreground:
                style_format.setForeground(QColor(str(foreground)))

            bold = style.get("bold", "")
            if bold == "true":
                style_format.setFontWeight(QFont.Bold)

            italic = style.get("italic", "")
            if italic == "true":
                style_format.setFontItalic(True)

            underlineStyle = style.get("underlineStyle", "")
            underlineStyle = UNDERLINE_STYLES.get(
                underlineStyle, QTextCharFormat.UnderlineStyle.NoUnderline
            )
            style_format.setUnderlineStyle(underlineStyle)
            self._data[style_name] = style_format

    def clear(self):
        self._loaded = False
        self._data.clear()
        self._name = ""

    @classmethod
    def defaultStyle(cls) -> "QSyntaxStyle":
        if not isinstance(cls._defaultStyle, QSyntaxStyle):
            cls._defaultStyle = QSyntaxStyle()
        if cls._defaultStyle.isLoaded():
            return cls._defaultStyle
        file = utils.get_resource_file("default_style.json")
        if not cls._defaultStyle.load(file):
            warnings.warn("Can't load default style.")
        return cls._defaultStyle
