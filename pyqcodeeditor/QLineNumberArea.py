from __future__ import annotations

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QPaintEvent, QPainter
from qtpy.QtWidgets import QWidget

from . import QCodeEditor
from . import QSyntaxStyle


# noinspection PyPep8Naming
class QLineNumberArea(QWidget):

    def __init__(self, parent: QCodeEditor.QCodeEditor | None = None):
        super().__init__(parent)

        self._syntaxStyle: QSyntaxStyle.QSyntaxStyle | None = None
        self._codeEditParent: QCodeEditor.QCodeEditor | None = parent

    def sizeHint(self) -> QSize:
        if self._codeEditParent is None:
            return super().sizeHint()

        digits = 1
        max_ = max(1, self._codeEditParent.document().blockCount())
        while max_ >= 10:
            max_ /= 10.0
            digits += 1
        space = 13 + self._codeEditParent.fontMetrics().width("0") * digits
        return QSize(space, 0)

    def setSyntaxStyle(self, style: QSyntaxStyle.QSyntaxStyle | None):
        self._syntaxStyle = style

    def syntaxStyle(self) -> QSyntaxStyle.QSyntaxStyle | None:
        return self._syntaxStyle

    def paintEvent(self, event: QPaintEvent, **kwargs):
        painter = QPainter(self)
        bgColor = self._syntaxStyle.getFormat("Text").background().color()
        painter.fillRect(event.rect(), bgColor)
        # noinspection PyProtectedMember
        blockNumber = self._codeEditParent._getFirstVisibleBlock()
        block = self._codeEditParent.document().findBlockByNumber(blockNumber)
        top = int(
            self._codeEditParent.document()
            .documentLayout()
            .blockBoundingRect(block)
            .translated(0, -self._codeEditParent.verticalScrollBar().value())
            .top()
        )
        bottom = top + int(
            self._codeEditParent.document()
            .documentLayout()
            .blockBoundingRect(block)
            .height()
        )
        currentLine = (
            self._syntaxStyle.getFormat("CurrentLineNumber").foreground().color()
        )
        otherLines = self._syntaxStyle.getFormat("LineNumber").foreground().color()
        painter.setFont(self._codeEditParent.font())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(currentLine if currentLine else otherLines)
                painter.drawText(
                    -5,
                    top,
                    self.sizeHint().width(),
                    self._codeEditParent.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(
                self._codeEditParent.document()
                .documentLayout()
                .blockBoundingRect(block)
                .height()
            )
            blockNumber += 1
