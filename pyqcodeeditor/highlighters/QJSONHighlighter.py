from __future__ import annotations

from typing import List

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QTextDocument

from .QHighlightRule import QHighlightRule
from ..QStyleSyntaxHighlighter import QStyleSyntaxHighlighter

_KEYWORDS = [
    "true",
    "false",
    "null",
]


# noinspection PyPep8Naming
class QJSONHighlighter(QStyleSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None = None):
        super().__init__(document)
        self.m_highlightRules: List[QHighlightRule] = []
        self.m_keyRegex: QRegularExpression = QRegularExpression(
            r'(("[ ^\r\n:]+?")\s*:)'
        )

        for kw in _KEYWORDS:
            self.m_highlightRules.append(
                QHighlightRule(QRegularExpression(rf"(\b{kw}\b)"), "Keyword")
            )

        # Numbers
        self.m_highlightRules.append(
            (QHighlightRule(QRegularExpression(R"(\b(0b|0x){0,1}[\d.']+\b)"), "Number"))
        )

        # Strings
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r'("[^\n"]*")'), "String")
        )

    def highlightBlock(self, text: str):
        for rule in self.m_highlightRules:
            matchIterator = rule.pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    self.syntaxStyle().getFormat(rule.formatName),
                )

        matchIterator = self.m_keyRegex.globalMatch(text)
        while matchIterator.hasNext():
            match = matchIterator.next()
            self.setFormat(
                match.capturedStart(1),
                match.capturedLength(1),
                self.syntaxStyle().getFormat("Keyword"),
            )
