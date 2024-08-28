from __future__ import annotations

from typing import List

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QTextDocument

from .QHighlightBlockRule import QHighlightBlockRule
from .QHighlightRule import QHighlightRule
from .. import utils
from ..QStyleSyntaxHighlighter import QStyleSyntaxHighlighter


# noinspection PyPep8Naming
class QLuaHighlighter(QStyleSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None = None):
        super().__init__(document)

        self.m_highlightRules: List[QHighlightRule] = []
        self.m_highlightBlockRules: List[QHighlightBlockRule] = []

        self.m_requirePattern: QRegularExpression = QRegularExpression(
            r"""(require\s*([("'][a-zA-Z0-9*._]+['")]))"""
        )
        self.m_functionPattern: QRegularExpression = QRegularExpression(
            r"(\b([A-Za-z0-9_]+(?:\s+|::))*([A-Za-z0-9_]+)(?=\())"
        )
        self.m_defTypePattern: QRegularExpression = QRegularExpression(
            r"(\b([A-Za-z0-9_]+)\s+[A-Za-z]{1}[A-Za-z0-9_]+\s*[=])"
        )
        self._loadLanguageRules()

        # Numbers
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"(\b(0b|0x){0,1}[\d.']+\b)"), "Number")
        )

        # Strings
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"""(["'][^\n"]*["'])"""), "String")
        )

        # Preprocessor
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"(#\![a-zA-Z_]+)"), "Preprocessor")
        )

        # Single line
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"(--[^\n]*)"), "Comment")
        )

        # Multiline comments
        rule = QHighlightBlockRule(
            QRegularExpression(R"(--\[\[)"), QRegularExpression(R"(--\]\])"), "Comment"
        )
        self.m_highlightBlockRules.append(rule)

        # Multiline string
        rule = QHighlightBlockRule(
            QRegularExpression(R"(\[\[)"), QRegularExpression(R"(\]\])"), "String"
        )
        self.m_highlightBlockRules.append(rule)

    def highlightBlock(self, text: str):
        self._checkForRequire(text)
        self._checkForFunction(text)
        self._checkForDefType(text)
        self._checkForLanguageRules(text)
        self.setCurrentBlockState(0)
        startIndex = 0
        highlightRuleId = self.previousBlockState()
        if highlightRuleId < 1 or highlightRuleId > len(self.m_highlightBlockRules):
            for i in range(len(self.m_highlightBlockRules)):
                startIndex = utils.index_of(
                    text, self.m_highlightBlockRules[i].startPattern, 0
                )
                if startIndex >= 0:
                    highlightRuleId = i + 1
                    break
        while startIndex >= 0:
            blockRules = self.m_highlightBlockRules[highlightRuleId - 1]
            match = blockRules.endPattern.match(text, startIndex)
            endIndex = match.capturedStart()
            if endIndex == -1:
                self.setCurrentBlockState(highlightRuleId)
                matchLength = len(text) - startIndex
            else:
                matchLength = endIndex - startIndex + match.capturedLength()

            self.setFormat(
                startIndex,
                matchLength,
                self.syntaxStyle().getFormat(blockRules.formatName),
            )
            startIndex = utils.index_of(
                text, blockRules.startPattern, startIndex + matchLength
            )

    def _checkForRequire(self, text: str):
        matchIterator = self.m_requirePattern.globalMatch(text)
        while matchIterator.hasNext():
            match = matchIterator.next()
            self.setFormat(
                match.capturedStart(),
                match.capturedLength(),
                self.syntaxStyle().getFormat("Preprocessor"),
            )
            self.setFormat(
                match.capturedStart(1),
                match.capturedLength(1),
                self.syntaxStyle().getFormat("String"),
            )

    def _checkForFunction(self, text: str):
        matchIterator = self.m_functionPattern.globalMatch(text)
        while matchIterator.hasNext():
            match = matchIterator.next()
            self.setFormat(
                match.capturedStart(),
                match.capturedLength(),
                self.syntaxStyle().getFormat("Type"),
            )
            self.setFormat(
                match.capturedStart(2),
                match.capturedLength(2),
                self.syntaxStyle().getFormat("Function"),
            )

    def _checkForDefType(self, text: str):
        matchIterator = self.m_defTypePattern.globalMatch(text)
        while matchIterator.hasNext():
            match = matchIterator.next()
            self.setFormat(
                match.capturedStart(1),
                match.capturedLength(1),
                self.syntaxStyle().getFormat("Type"),
            )

    def _checkForLanguageRules(self, text: str):
        for rule in self.m_highlightRules:
            matchIterator = rule.pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    self.syntaxStyle().getFormat(rule.formatName),
                )

    def _loadLanguageRules(self):
        language = utils.load_builtin_language("lua.json")
        if not language:
            return
        for key in language.keys():
            names = language.names(key)
            if not names:
                continue
            for name in names:
                rule = QHighlightRule(
                    QRegularExpression(
                        r"(\b\s{0,1}%1\s{0,1}\b)".replace("%1", str(name))
                    ),
                    key,
                )
                self.m_highlightRules.append(rule)
