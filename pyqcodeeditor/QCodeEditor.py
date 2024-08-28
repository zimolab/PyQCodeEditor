from __future__ import annotations

from typing import List

from qtpy.QtCore import QRect, QMimeData, Qt
from qtpy.QtGui import (
    QTextCursor,
    QKeyEvent,
    QPaintEvent,
    QFontDatabase,
    QPalette,
    QTextDocument,
    QResizeEvent,
    QBrush,
)
from qtpy.QtWidgets import QCompleter, QTextEdit, QWidget, QAbstractItemView

from . import utils

# from .QFramedTextAttribute import QFramedTextAttribute
from .QLineNumberArea import QLineNumberArea
from .QStyleSyntaxHighlighter import QStyleSyntaxHighlighter
from .QSyntaxStyle import QSyntaxStyle

DEFAULT_TAB_WIDTH = 4

PARENTHESES = [
    ("(", ")"),
    ("{", "}"),
    ("[", "]"),
    ('"', '"'),
    ("'", "'"),
]


# noinspection PyPep8Naming
class QCodeEditor(QTextEdit):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.m_highlighter: QStyleSyntaxHighlighter | None = None
        self.m_syntaxStyle: QSyntaxStyle = QSyntaxStyle.defaultStyle()
        self.m_lineNumberArea: QLineNumberArea = QLineNumberArea(self)
        self.m_completer: QCompleter | None = None
        # self.m_framedAttribute: QFramedTextAttribute = QFramedTextAttribute(self)
        self.m_autoIndentation: bool = True
        self.m_autoParentheses: bool = True
        self.m_replaceTab: bool = True
        self.m_tabReplace: str = " " * 4
        self.m_defaultIndent: int = self.tabReplaceSize()
        self.m_fontSize: int = 20

        self._initDocumentLayoutHandlers()
        self._initFont()
        self._performConnections()

        self.setSyntaxStyle(QSyntaxStyle.defaultStyle())

        # init update of line number area
        self.updateLineNumberAreaWidth(0)

    def getFirstVisibleBlock(self) -> int:
        doc: QTextDocument = self.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.Start)

        doc: QTextDocument = self.document()

        for i in range(0, doc.blockCount()):
            block = cursor.block()
            r1: QRect = self.viewport().geometry()
            _layout = doc.documentLayout()
            _bRect = _layout.blockBoundingRect(block)
            _x = self.viewport().geometry().x()
            _y = (
                self.viewport().geometry().y()
                - self.verticalScrollBar().sliderPosition()
            )
            _r = _bRect.translate(_x, _y)
            if _r is None:
                continue
            r2 = _r.toRect()
            if r1.intersects(r2):
                return i
            cursor.movePosition(QTextCursor.NextBlock)
        return 0

    def setHighlighter(self, highlighter: QStyleSyntaxHighlighter):
        if self.m_highlighter is not None:
            self.m_highlighter.setSyntaxStyle(None)
            self.m_highlighter.deleteLater()
            self.m_highlighter = None

        self.m_highlighter = highlighter
        if self.m_highlighter:
            self.m_highlighter.setSyntaxStyle(self.m_syntaxStyle)
            self.m_highlighter.setDocument(self.document())

            if self.m_highlighter.parent() is None:
                highlighter.setParent(self)

    def setSyntaxStyle(self, syntaxStyle: QSyntaxStyle):
        assert syntaxStyle is not None
        if syntaxStyle != QSyntaxStyle.defaultStyle():
            self.m_syntaxStyle.clear()
            self.m_syntaxStyle.deleteLater()
            self.m_syntaxStyle = None

        self.m_syntaxStyle = syntaxStyle
        # self.m_framedAttribute.setSyntaxStyle(syntaxStyle)
        self.m_lineNumberArea.setSyntaxStyle(syntaxStyle)
        if self.m_highlighter:
            self.m_highlighter.setSyntaxStyle(syntaxStyle)
            if self.m_syntaxStyle.parent() is None:
                self.m_syntaxStyle.setParent(self)
        self.updateStyle()

    def setAutoParentheses(self, enable: bool):
        self.m_autoParentheses = enable

    def autoParentheses(self) -> bool:
        return self.m_autoParentheses

    def setTabReplace(self, enable: bool):
        self.m_replaceTab = enable

    def tabReplace(self) -> bool:
        return self.m_replaceTab

    def setTabReplaceSize(self, val: int):
        self.m_tabReplace = " " * val

    def tabReplaceSize(self) -> int:
        return len(self.m_tabReplace)

    def setAutoIndentation(self, enable: bool):
        self.m_autoIndentation = enable

    def autoIndentation(self) -> bool:
        return self.m_autoIndentation

    def setCompleter(self, completer: QCompleter | None):
        if self.m_completer is not None:
            popup: QAbstractItemView = self.m_completer.popup()
            if popup:
                popup.hide()
            # noinspection PyUnresolvedReferences
            self.m_completer.activated.disconnect(self.insertCompletion)
            self.m_completer.deleteLater()
            self.m_completer = None

        self.m_completer = completer
        if not self.m_completer:
            return

        self.m_completer.setWidget(self)
        self.m_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        # noinspection PyUnresolvedReferences
        self.m_completer.activated.connect(self.insertCompletion)
        if self.m_completer.parent() is None:
            completer.setParent(self)

    def completer(self) -> QCompleter | None:
        return self.m_completer

    def insertCompletion(self, s: str):
        if self.m_completer.widget() != self:
            return
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.insertText(s)
        self.setTextCursor(tc)

    # noinspection PyUnusedLocal
    def updateLineNumberAreaWidth(self, w: int):
        self.setViewportMargins(self.m_lineNumberArea.sizeHint().width(), 0, 0, 0)

    def updateLineNumberArea(self, rect: QRect):
        # noinspection PyArgumentList
        self.m_lineNumberArea.update(
            0, rect.y(), self.m_lineNumberArea.sizeHint().width(), rect.height()
        )

    def updateExtraSelection(self):
        extra = []
        self._highlightCurrentLine(extra)
        self._highlightParenthesis(extra)
        self.setExtraSelections(extra)

    def updateStyle(self):
        if self.m_highlighter:
            self.m_highlighter.rehighlight()

        if self.m_syntaxStyle:
            currentPalette = self.palette()
            currentPalette.setColor(
                QPalette.ColorRole.Text,
                self.m_syntaxStyle.getFormat("Text").foreground().color(),
            )
            currentPalette.setColor(
                QPalette.Base, self.m_syntaxStyle.getFormat("Text").background().color()
            )
            currentPalette.setColor(
                QPalette.Highlight,
                self.m_syntaxStyle.getFormat("Selection").background().color(),
            )
            self.setPalette(currentPalette)

        self.updateExtraSelection()

    def onSelectionChanged(self):
        cursor = self.textCursor()

        if cursor.isNull():
            return
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        # blocker = QSignalBlocker(self)
        # selected = self.textCursor().selectedText()
        # self.m_framedAttribute.clear(cursor)

        # FIXME: Sometimes below code will case a infinite loop(in function _handleSelectionQuery)
        #  and i dont know exactly why and how to fix it.
        # if len(selected) > 1 and cursor.selectedText() == selected:
        #     backup = self.textCursor()
        #     self._handleSelectionQuery(cursor)
        #     self.setTextCursor(backup)

    def insertFromMimeData(self, source: QMimeData, **kwargs):
        self.insertPlainText(source.text())

    def paintEvent(self, e: QPaintEvent, **kwargs):
        self.updateLineNumberArea(e.rect())
        super().paintEvent(e)

    def resizeEvent(self, e: QResizeEvent, **kwargs):
        super().resizeEvent(e)
        self._updateLineGeometry()

    def keyPressEvent(self, e: QKeyEvent, **kwargs):
        completerSkip = self._proceedCompleterBegin(e)
        key = e.key()
        modifiers = e.modifiers()

        if completerSkip:
            self._proceedCompleterEnd(e)
            return

        # Insert tab replace only
        if self.m_replaceTab and key == Qt.Key_Tab and modifiers == Qt.NoModifier:
            self.insertPlainText(self.m_tabReplace)
            return

        indentationLevel = self.getIndentationSpaces()
        tabCounts = self._tabCounts(indentationLevel)
        defaultIndent = self.defaultIndent()
        # Have Qt Editor like behaviour, if {|} and enter is pressed
        # indent the two parenthesis
        if (
            self.m_autoIndentation
            and (key == Qt.Key_Return or key == Qt.Key_Enter)
            and self._charUnderCursor() == "}"
            and self._charUnderCursor(-1) == "{"
        ):
            self._indentParenthesis(indentationLevel, tabCounts, defaultIndent)
            return

        # Do back tap
        if self.m_replaceTab and key == Qt.Key_Backtab:
            self._doBackTab(indentationLevel)
            return

        super().keyPressEvent(e)

        # Do auto indentation
        if self.m_autoIndentation and (key == Qt.Key_Return or key == Qt.Key_Enter):
            self._doAutoIndentation(indentationLevel, tabCounts)

        # Do auto parentheses
        if self.m_autoParentheses:
            self._doAutoParentheses(text=e.text())

        self._proceedCompleterEnd(e)

    def focusInEvent(self, e, **kwargs):
        if self.m_completer:
            self.m_completer.setWidget(self)
        super().focusInEvent(e)

    def _initDocumentLayoutHandlers(self):
        # self.document().documentLayout().registerHandler(
        #     QFramedTextAttribute.type(), self.m_framedAttribute
        # )
        pass

    def _initFont(self):
        # noinspection PyArgumentList
        fnt = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fnt.setFixedPitch(True)
        fnt.setPointSize(self.m_fontSize)
        self.setFont(fnt)

    def _performConnections(self):
        doc = self.document()
        # noinspection PyUnresolvedReferences
        doc.blockCountChanged.connect(self.updateLineNumberAreaWidth)

        def _vbar_changed(_):
            self.m_lineNumberArea.update()

        vbar = self.verticalScrollBar()
        # noinspection PyUnresolvedReferences
        vbar.valueChanged.connect(_vbar_changed)

        # noinspection PyUnresolvedReferences
        self.cursorPositionChanged.connect(self.updateExtraSelection)
        # noinspection PyUnresolvedReferences
        self.selectionChanged.connect(self.onSelectionChanged)

    # FIXME
    # def _handleSelectionQuery(self, cursor: QTextCursor):
    #     searchIterator = cursor
    #     searchIterator.movePosition(QTextCursor.Start)
    #     searchIterator = self.document().find(cursor.selectedText(), searchIterator)
    #     while searchIterator.hasSelection():
    #         self.m_framedAttribute.frame(searchIterator)
    #         searchIterator = self.document().find(cursor.selectedText(), searchIterator)

    def _updateLineGeometry(self):
        cr = self.contentsRect()
        x = cr.left()
        y = cr.top()
        w = self.m_lineNumberArea.sizeHint().width()
        h = cr.height()
        self.m_lineNumberArea.setGeometry(QRect(x, y, w, h))

    def _proceedCompleterBegin(self, e: QKeyEvent) -> bool:
        if self.m_completer and self.m_completer.popup().isVisible():
            key = e.key()
            shouldIgnore = key == Qt.Key_Enter
            shouldIgnore = shouldIgnore or key == Qt.Key_Return
            shouldIgnore = shouldIgnore or key == Qt.Key_Escape
            shouldIgnore = shouldIgnore or key == Qt.Key_Tab
            shouldIgnore = shouldIgnore or key == Qt.Key_Backtab
            if shouldIgnore:
                e.ignore()
                return True
        isShortcut = utils.is_shortcut(e, Qt.ControlModifier, Qt.Key_Space)
        return not (not self.m_completer or not isShortcut)

    def _proceedCompleterEnd(self, e: QKeyEvent):
        key = e.key()
        ctrlOrShift = utils.has_modifier(e, Qt.ControlModifier, Qt.ShiftModifier)
        text = e.text()
        isEmpty = len(text) <= 0
        if not self.m_completer or (ctrlOrShift and isEmpty) or key == Qt.Key_Delete:
            return
        eow = r""""(~!@#$%^&*()_+{}|:"<>?,./;'[]\-=)"""
        isShortcut = utils.is_shortcut(e, Qt.ControlModifier, Qt.Key_Space)
        completionPrefix = self._wordUnderCursor()
        isContainChar = len(text) > 0 and (text[-1] in eow)
        if (not isShortcut) and (isEmpty or len(completionPrefix) < 2 or isContainChar):
            self.m_completer.popup().hide()
            return

        if completionPrefix != self.m_completer.completionPrefix():
            self.m_completer.setCompletionPrefix(completionPrefix)
            self.m_completer.popup().setCurrentIndex(
                self.m_completer.completionModel().index(0, 0)
            )

        cursRect = self.cursorRect()
        cursRect.setWidth(
            self.m_completer.popup().sizeHintForColumn(0)
            + self.m_completer.popup().verticalScrollBar().sizeHint().width()
        )
        self.m_completer.complete(cursRect)

    def _charUnderCursor(self, offset: int = 0) -> str:
        cursor: QTextCursor = self.textCursor()
        doc: QTextDocument = self.document()
        block = cursor.blockNumber()
        index = cursor.positionInBlock()
        text = doc.findBlockByNumber(block).text()

        index += offset

        if index < 0 or index >= len(text):
            return ""
        return text[index]

    def _wordUnderCursor(self) -> str:
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText() or ""

    def _highlightCurrentLine(self, extraSelection: List[QTextEdit.ExtraSelection]):
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format = self.m_syntaxStyle.getFormat("CurrentLine")
            selection.format.setForeground(QBrush())
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extraSelection.append(selection)

    def _highlightParenthesis(self, extraSelection: List[QTextEdit.ExtraSelection]):
        currentSymbol = self._charUnderCursor()
        prevSymbol = self._charUnderCursor(-1)

        for pair in PARENTHESES:
            position = self.textCursor().position()

            first = pair[0]
            second = pair[1]

            if first == currentSymbol:
                direction = 1
                counterSymbol = second[0]
                activeSymbol = currentSymbol
            elif second == prevSymbol:
                direction = -1
                counterSymbol = first
                activeSymbol = prevSymbol
                position -= 1
            else:
                continue
            counter = 1

            _charCount = self.document().characterCount() - 1
            while counter != 0 and 0 <= position < _charCount:
                position += direction
                character = self.document().characterAt(position)
                if character == activeSymbol:
                    counter += 1
                elif character == counterSymbol:
                    counter -= 1
                else:
                    pass
            format_ = self.m_syntaxStyle.getFormat("Parentheses")

            if counter == 0:
                selection = QTextEdit.ExtraSelection()
                directionEnum = (
                    QTextCursor.MoveOperation.Left
                    if direction < 0
                    else QTextCursor.MoveOperation.Right
                )
                selection.format = format_
                selection.cursor = QTextCursor(self.textCursor())
                selection.cursor.clearSelection()
                _foundPos = abs(self.textCursor().position() - position)
                selection.cursor.movePosition(
                    directionEnum, QTextCursor.MoveMode.MoveAnchor, _foundPos
                )
                selection.cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1
                )

                extraSelection.append(selection)

                selection2 = QTextEdit.ExtraSelection()
                selection2.format = format_
                selection2.cursor = QTextCursor(self.textCursor())
                selection2.cursor.clearSelection()
                selection2.cursor.movePosition(
                    directionEnum, QTextCursor.MoveMode.KeepAnchor, 1
                )
                extraSelection.append(selection2)

    def getIndentationSpaces(self) -> int:
        blockText = self.textCursor().block().text()
        indentationLevel: int = 0
        bSize_ = len(blockText)
        for i in range(bSize_):
            if blockText[i] not in "\t ":
                break
            if blockText[i] == " ":
                indentationLevel += 1
            else:
                avgCharWidth = self.fontMetrics().averageCharWidth()
                indentationLevel += int(self._tabWidth() / avgCharWidth)
        return indentationLevel

    def setDefaultIndent(self, indent: int):
        self.m_defaultIndent = max(0, indent)

    def defaultIndent(self) -> int:
        return self.m_defaultIndent

    def _tabCounts(self, indentationLevel: int) -> int:
        avgCharWidth = self.fontMetrics().averageCharWidth()
        counts = int(indentationLevel * avgCharWidth / self._tabWidth())
        return counts

    def _tabWidth(self) -> int:
        if hasattr(self, "tabStopDistance"):
            return int(self.tabStopDistance())
        else:
            return int(self.tabStopWidth())

    def _indentParenthesis(
        self, indentationLevel: int, tabCounts: int, defaultIndent: int
    ):
        charsBack = 0
        self.insertPlainText("\n")

        if self.m_replaceTab:
            _indentStr = " " * (indentationLevel + defaultIndent)
            self.insertPlainText(_indentStr)
        else:
            _indentStr = "\t" * (tabCounts + 1)
            self.insertPlainText(_indentStr)

        self.insertPlainText("\n")
        charsBack += 1

        if self.m_replaceTab:
            self.insertPlainText(" " * indentationLevel)
            charsBack += indentationLevel
        else:
            self.insertPlainText("\t" * tabCounts)
            charsBack += tabCounts

        while charsBack > 0:
            self.moveCursor(QTextCursor.MoveOperation.Left)
            charsBack -= 1

    def _doBackTab(self, indentationLevel: int):
        indentationLevel = min(indentationLevel, self.tabReplaceSize())
        cursor: QTextCursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            indentationLevel,
        )
        cursor.removeSelectedText()

    def _doAutoIndentation(self, indentationLevel: int, tabCounts: int):
        indentChars = " " * indentationLevel if self.m_replaceTab else "\t" * tabCounts
        self.insertPlainText(indentChars)

    def _doAutoParentheses(self, text: str):
        for pair in PARENTHESES:
            left = pair[0]
            right = pair[1]

            if left == text:
                self.insertPlainText(right)
                self.moveCursor(QTextCursor.MoveOperation.Left)
                break

            if right == text:
                syb = self._charUnderCursor()
                if syb == right:
                    self.textCursor().deletePreviousChar()
                    self.moveCursor(QTextCursor.MoveOperation.Right)
                break
