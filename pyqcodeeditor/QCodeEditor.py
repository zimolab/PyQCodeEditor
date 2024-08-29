from __future__ import annotations

from typing import List

# noinspection PyUnresolvedReferences
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


PARENTHESES = [
    ("(", ")"),
    ("{", "}"),
    ("[", "]"),
    ('"', '"'),
    ("'", "'"),
]

DEFAULT_FONT_POINT_SIZE: int = 14
DEFAULT_TAB_WIDTH: int = 4


# noinspection PyPep8Naming
class QCodeEditor(QTextEdit):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._highlighter: QStyleSyntaxHighlighter | None = None
        self._syntaxStyle: QSyntaxStyle = QSyntaxStyle.defaultStyle()
        self._lineNumberArea: QLineNumberArea = QLineNumberArea(self)
        self._completer: QCompleter | None = None
        # self.m_framedAttribute: QFramedTextAttribute = QFramedTextAttribute(self)
        self._autoIndentation: bool = True
        self._autoParentheses: bool = True
        self._replaceTab: bool = True
        self._tabReplace: str = " " * DEFAULT_TAB_WIDTH
        self._defaultIndent: int = self.tabReplaceSize()
        self._fontSize: int = DEFAULT_FONT_POINT_SIZE

        self._initDocumentLayoutHandlers()
        self._initFont()
        self._performConnections()

        self.setSyntaxStyle(QSyntaxStyle.defaultStyle())

        # init update of line number area
        self._updateLineNumberAreaWidth(0)

    def _getFirstVisibleBlock(self) -> int:
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


    def setFontSize(self, fontSize: int):
        assert fontSize > 0
        self._fontSize = fontSize
        fnt = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fnt.setFixedPitch(True)
        fnt.setPointSize(self._fontSize)
        self.setFont(fnt)

    def fontSize(self) -> int:
        return self._fontSize

    def setHighlighter(self, highlighter: QStyleSyntaxHighlighter):
        if self._highlighter is not None:
            self._highlighter.setSyntaxStyle(None)
            self._highlighter.deleteLater()
            self._highlighter = None

        self._highlighter = highlighter
        if self._highlighter:
            self._highlighter.setSyntaxStyle(self._syntaxStyle)
            self._highlighter.setDocument(self.document())

            if self._highlighter.parent() is None:
                highlighter.setParent(self)

    def setSyntaxStyle(self, syntaxStyle: QSyntaxStyle):
        assert syntaxStyle is not None
        if syntaxStyle != QSyntaxStyle.defaultStyle():
            self._syntaxStyle.clear()
            self._syntaxStyle.deleteLater()
            self._syntaxStyle = None

        self._syntaxStyle = syntaxStyle
        # self.m_framedAttribute.setSyntaxStyle(syntaxStyle)
        self._lineNumberArea.setSyntaxStyle(syntaxStyle)
        if self._highlighter:
            self._highlighter.setSyntaxStyle(syntaxStyle)
            if self._syntaxStyle.parent() is None:
                self._syntaxStyle.setParent(self)
        self._updateStyle()

    def setAutoParentheses(self, enable: bool):
        self._autoParentheses = enable

    def autoParentheses(self) -> bool:
        return self._autoParentheses

    def setTabReplace(self, enable: bool):
        self._replaceTab = enable

    def tabReplace(self) -> bool:
        return self._replaceTab

    def setTabReplaceSize(self, val: int):
        self._tabReplace = " " * val

    def tabReplaceSize(self) -> int:
        return len(self._tabReplace)

    def setAutoIndentation(self, enable: bool):
        self._autoIndentation = enable

    def autoIndentation(self) -> bool:
        return self._autoIndentation

    def setCompleter(self, completer: QCompleter | None):
        if self._completer is not None:
            popup: QAbstractItemView = self._completer.popup()
            if popup:
                popup.hide()
            # noinspection PyUnresolvedReferences
            self._completer.activated.disconnect(self._insertCompletion)
            self._completer.deleteLater()
            self._completer = None

        self._completer = completer
        if not self._completer:
            return

        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        # noinspection PyUnresolvedReferences
        self._completer.activated.connect(self._insertCompletion)
        if self._completer.parent() is None:
            completer.setParent(self)

    def completer(self) -> QCompleter | None:
        return self._completer

    def _insertCompletion(self, s: str):
        if self._completer.widget() != self:
            return
        tc: QTextCursor = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.insertText(s)
        self.setTextCursor(tc)

    # noinspection PyUnusedLocal
    def _updateLineNumberAreaWidth(self, w: int):
        self.setViewportMargins(self._lineNumberArea.sizeHint().width(), 0, 0, 0)

    def _updateLineNumberArea(self, rect: QRect):
        # noinspection PyArgumentList
        self._lineNumberArea.update(
            0, rect.y(), self._lineNumberArea.sizeHint().width(), rect.height()
        )

    def _updateExtraSelection(self):
        extra = []
        self._highlightCurrentLine(extra)
        self._highlightParenthesis(extra)
        self.setExtraSelections(extra)

    def _updateStyle(self):
        if self._highlighter:
            self._highlighter.rehighlight()

        if self._syntaxStyle:
            currentPalette = self.palette()
            currentPalette.setColor(
                QPalette.ColorRole.Text,
                self._syntaxStyle.getFormat("Text").foreground().color(),
            )
            currentPalette.setColor(
                QPalette.Base, self._syntaxStyle.getFormat("Text").background().color()
            )
            currentPalette.setColor(
                QPalette.Highlight,
                self._syntaxStyle.getFormat("Selection").background().color(),
            )
            self.setPalette(currentPalette)

        self._updateExtraSelection()

    def _onSelectionChanged(self):
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

    # noinspection PyUnusedLocal
    def insertFromMimeData(self, source: QMimeData, **kwargs):
        self.insertPlainText(source.text())

    # noinspection PyUnusedLocal
    def paintEvent(self, e: QPaintEvent, **kwargs):
        self._updateLineNumberArea(e.rect())
        super().paintEvent(e)

    # noinspection PyUnusedLocal
    def resizeEvent(self, e: QResizeEvent, **kwargs):
        super().resizeEvent(e)
        self._updateLineGeometry()

    # noinspection PyUnusedLocal
    def keyPressEvent(self, e: QKeyEvent, **kwargs):
        completerSkip = self._proceedCompleterBegin(e)
        key = e.key()
        modifiers = e.modifiers()

        if completerSkip:
            self._proceedCompleterEnd(e)
            return

        # Insert tab replace only
        if self._replaceTab and key == Qt.Key_Tab and modifiers == Qt.NoModifier:
            self.insertPlainText(self._tabReplace)
            return

        indentationLevel = self.getIndentationSpaces()
        tabCounts = self._tabCounts(indentationLevel)
        defaultIndent = self.defaultIndent()
        # Have Qt Editor like behaviour, if {|} and enter is pressed
        # indent the two parenthesis
        if (
            self._autoIndentation
            and (key == Qt.Key_Return or key == Qt.Key_Enter)
            and self._charUnderCursor() == "}"
            and self._charUnderCursor(-1) == "{"
        ):
            self._indentParenthesis(indentationLevel, tabCounts, defaultIndent)
            return

        # Do back tap
        if self._replaceTab and key == Qt.Key_Backtab:
            self._doBackTab(indentationLevel)
            return

        super().keyPressEvent(e)

        # Do auto indentation
        if self._autoIndentation and (key == Qt.Key_Return or key == Qt.Key_Enter):
            self._doAutoIndentation(indentationLevel, tabCounts)

        # Do auto parentheses
        if self._autoParentheses:
            self._doAutoParentheses(text=e.text())

        self._proceedCompleterEnd(e)

    # noinspection PyUnusedLocal
    def focusInEvent(self, e, **kwargs):
        if self._completer:
            self._completer.setWidget(self)
        super().focusInEvent(e)

    def _initDocumentLayoutHandlers(self):
        # self.document().documentLayout().registerHandler(
        #     QFramedTextAttribute.type(), self.m_framedAttribute
        # )
        pass

    def _initFont(self):
        self.setFontSize(DEFAULT_FONT_POINT_SIZE)

    def _performConnections(self):
        doc = self.document()
        # noinspection PyUnresolvedReferences
        doc.blockCountChanged.connect(self._updateLineNumberAreaWidth)

        def _vbar_changed(_):
            self._lineNumberArea.update()

        vbar = self.verticalScrollBar()
        # noinspection PyUnresolvedReferences
        vbar.valueChanged.connect(_vbar_changed)

        # noinspection PyUnresolvedReferences
        self.cursorPositionChanged.connect(self._updateExtraSelection)
        # noinspection PyUnresolvedReferences
        self.selectionChanged.connect(self._onSelectionChanged)

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
        w = self._lineNumberArea.sizeHint().width()
        h = cr.height()
        self._lineNumberArea.setGeometry(QRect(x, y, w, h))

    def _proceedCompleterBegin(self, e: QKeyEvent) -> bool:
        if self._completer and self._completer.popup().isVisible():
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
        return not (not self._completer or not isShortcut)

    def _proceedCompleterEnd(self, e: QKeyEvent):
        key = e.key()
        ctrlOrShift = utils.has_modifier(e, Qt.ControlModifier, Qt.ShiftModifier)
        text = e.text()
        isEmpty = len(text) <= 0
        if not self._completer or (ctrlOrShift and isEmpty) or key == Qt.Key_Delete:
            return
        eow = r""""(~!@#$%^&*()_+{}|:"<>?,./;'[]\-=)"""
        isShortcut = utils.is_shortcut(e, Qt.ControlModifier, Qt.Key_Space)
        completionPrefix = self._wordUnderCursor()
        isContainChar = len(text) > 0 and (text[-1] in eow)
        if (not isShortcut) and (isEmpty or len(completionPrefix) < 2 or isContainChar):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0)
            )

        cursRect = self.cursorRect()
        cursRect.setWidth(
            self._completer.popup().sizeHintForColumn(0)
            + self._completer.popup().verticalScrollBar().sizeHint().width()
        )
        self._completer.complete(cursRect)

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
            selection.format = self._syntaxStyle.getFormat("CurrentLine")
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
            format_ = self._syntaxStyle.getFormat("Parentheses")

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
        self._defaultIndent = max(0, indent)

    def defaultIndent(self) -> int:
        return self._defaultIndent

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

        if self._replaceTab:
            _indentStr = " " * (indentationLevel + defaultIndent)
            self.insertPlainText(_indentStr)
        else:
            _indentStr = "\t" * (tabCounts + 1)
            self.insertPlainText(_indentStr)

        self.insertPlainText("\n")
        charsBack += 1

        if self._replaceTab:
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
        indentChars = " " * indentationLevel if self._replaceTab else "\t" * tabCounts
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
