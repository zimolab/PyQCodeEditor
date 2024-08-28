from __future__ import annotations

import os
import warnings
from typing import List

from qtpy.QtCore import QRegularExpression
from qtpy.QtGui import QTextDocument

from .. import utils
from ..QStyleSyntaxHighlighter import QStyleSyntaxHighlighter
from .QHighlightRule import QHighlightRule


# noinspection PyPep8Naming
class QCXXHighlighter(QStyleSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None = None):
        super().__init__(document)

        self.m_highlightRules: List[QHighlightRule] = []

        self.m_includePattern: QRegularExpression = QRegularExpression(
            r'(^\s*#\s*include\s*([<"][^:?"<>\|]+[">]))'
        )
        self.m_functionPattern: QRegularExpression = QRegularExpression(
            r"(\b([_a-zA-Z][_a-zA-Z0-9]*\s+)?((?:[_a-zA-Z][_a-zA-Z0-9]*\s*::\s*)*[_a-zA-Z][_a-zA-Z0-9]*)(?=\s*\())"
        )
        self.m_defTypePattern: QRegularExpression = QRegularExpression(
            r"(\b([_a-zA-Z][_a-zA-Z0-9]*)\s+[_a-zA-Z][_a-zA-Z0-9]*\s*[;=])"
        )
        self.m_commentStartPattern: QRegularExpression = QRegularExpression(r"(/\*)")
        self.m_commentEndPattern: QRegularExpression = QRegularExpression(r"(\*/)")

        self._loadLanguageRules()

        # Numbers
        numRule = QHighlightRule(
            QRegularExpression(
                r"((?<=\b|\s|^)(?i)(?:(?:(?:(?:(?:\d+(?:'\d+)*)?\.(?:\d+(?:'\d+)*)(?:e[+-]?(?:\d+(?:'\d+)*))?)|(?:(?:\d+(?:'\d+)*)\.(?:e[+-]?(?:\d+(?:'\d+)*))?)|(?:(?:\d+(?:'\d+)*)(?:e[+-]?(?:\d+(?:'\d+)*)))|(?:0x(?:[0-9a-f]+(?:'[0-9a-f]+)*)?\.(?:[0-9a-f]+(?:'[0-9a-f]+)*)(?:p[+-]?(?:\d+(?:'\d+)*)))|(?:0x(?:[0-9a-f]+(?:'[0-9a-f]+)*)\.?(?:p[+-]?(?:\d+(?:'\d+)*))))[lf]?)|(?:(?:(?:[1-9]\d*(?:'\d+)*)|(?:0[0-7]*(?:'[0-7]+)*)|(?:0x[0-9a-f]+(?:'[0-9a-f]+)*)|(?:0b[01]+(?:'[01]+)*))(?:u?l{0,2}|l{0,2}u?)))(?=\b|\s|$))"
            ),
            "Number",
        )
        self.m_highlightRules.append(numRule)
        # Strings
        strRule = QHighlightRule(QRegularExpression(r'("[^\n"]*")'), "String")
        self.m_highlightRules.append(strRule)

        # Defines
        defRule = QHighlightRule(QRegularExpression(r"(#[a-zA-Z_]+)"), "Preprocessor")
        self.m_highlightRules.append(defRule)

        # Single line comment
        slcRule = QHighlightRule(QRegularExpression(r"(//[^\n]*)"), "Comment")
        self.m_highlightRules.append(slcRule)

    def highlightBlock(self, text: str):
        self._checkForInclude(text)
        self._checkForFunction(text)
        self._checkForDefType(text)

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
        if self.previousBlockState() != 1:
            startIndex = utils.index_of(text, self.m_commentStartPattern, 0)

        while startIndex >= 0:
            match = self.m_commentStartPattern.match(text, startIndex)
            endIndex = match.capturedStart()
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + match.capturedLength()
            self.setFormat(
                startIndex, commentLength, self.syntaxStyle().getFormat("Comment")
            )
            startIndex = utils.index_of(
                text, self.m_commentEndPattern, startIndex + commentLength
            )

    def _checkForInclude(self, text: str):
        matchIterator = self.m_includePattern.globalMatch(text)
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

    def _loadLanguageRules(self):
        language = utils.load_builtin_language("cxx.json")
        if not language:
            return
        for key in language.keys():
            names = language.names(key)
            if not names:
                continue
            for name in names:
                rule = QHighlightRule(
                    QRegularExpression(rf"(\b{name}\b)"),
                    key,
                )
                self.m_highlightRules.append(rule)
