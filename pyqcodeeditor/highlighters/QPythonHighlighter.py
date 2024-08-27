from __future__ import annotations

import os.path
import warnings
from typing import List

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QTextDocument

from .QHighlightBlockRule import QHighlightBlockRule
from .QHighlightRule import QHighlightRule
from .. import QStyleSyntaxHighlighter, utils
from ..QLanguage import QLanguage


# noinspection PyPep8Naming
class QPythonHighlighter(QStyleSyntaxHighlighter.QStyleSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None = None):
        super().__init__(document)

        self.m_highlightRules: List[QHighlightRule] = []
        self.m_highlightBlockRules: List[QHighlightBlockRule] = []

        self.m_includePattern: QRegularExpression = QRegularExpression(r"(import \w+)")
        self.m_functionPattern: QRegularExpression = QRegularExpression(
            r"(\b([A-Za-z0-9_]+(?:\.))*([A-Za-z0-9_]+)(?=\())"
        )
        self.m_defTypePattern: QRegularExpression = QRegularExpression(
            r"(\b([A-Za-z0-9_]+)\s+[A-Za-z]{1}[A-Za-z0-9_]+\s*[;=])"
        )

        lang_file = utils.get_language_file("python.json")
        if not os.path.isfile(lang_file):
            warnings.warn(f"Language file not found: {lang_file}")
            return

        language = QLanguage(lang_file)
        if not language.isLoaded():
            warnings.warn(f"Language file not loaded: {lang_file}")
            return
        for key in language.keys():
            names = language.names(key)
            if not names:
                continue
            for name in names:
                self.m_highlightRules.append(
                    QHighlightRule(QRegularExpression(rf"\b{name}\b"), key)
                )
        # Following rules has higher priority to display
        # than language specific keys
        # So they must be applied at last.
        # Numbers
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"(\b(0b|0x){0,1}[\d.']+\b)"), "Number")
        )
        # Strings
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"""("[^\n"]*")"""), "String")
        )
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"""('[^\n"]*')"""), "String")
        )
        # Single line comment
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"#[^\n]*"), "Comment")
        )
        self.m_highlightRules.append(
            QHighlightRule(QRegularExpression(r"#[^\n]*"), "Comment")
        )
        # Multiline string
        self.m_highlightBlockRules.append(
            QHighlightBlockRule(
                QRegularExpression("(''')"),
                QRegularExpression("(''')"),
                "String",
            )
        )
        self.m_highlightBlockRules.append(
            QHighlightBlockRule(
                QRegularExpression(r'(""")'),
                QRegularExpression(r'(""")'),
                "String",
            )
        )

    def highlightBlock(self, text):
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

        for rule in self.m_highlightRules:
            matchIterator = rule.pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    self.syntaxStyle().getFormat(rule.formatName),
                )

        self.setCurrentBlockState(0)
        startIndex = 0
        highlightRuleId = self.previousBlockState()
        if highlightRuleId < 1 or (highlightRuleId > len(self.m_highlightBlockRules)):
            for i, rule in enumerate(self.m_highlightBlockRules):
                # startIndex = text.find(rule.startPattern.pattern())
                startIndex = utils.index_of(text, rule.startPattern, 0)
                if startIndex >= 0:
                    highlightRuleId = i + 1
                    break

        while startIndex >= 0:
            blockRules = self.m_highlightBlockRules[highlightRuleId - 1]
            match = blockRules.endPattern.match(text, startIndex + 1)
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
