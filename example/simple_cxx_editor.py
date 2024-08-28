from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QCXXHighlighter
from pyqcodeeditor.completers import QCXXCompleter

app = QApplication([])
editor = QCodeEditor()
editor.setCompleter(QCXXCompleter())
editor.setHighlighter(QCXXHighlighter())
editor.resize(800, 600)
editor.setPlainText("")
editor.show()
app.exec_()
