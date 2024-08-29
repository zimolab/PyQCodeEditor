from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QGLSLHighlighter
from pyqcodeeditor.completers import QGLSLCompleter

app = QApplication([])
editor = QCodeEditor()
editor.setCompleter(QGLSLCompleter())
editor.setHighlighter(QGLSLHighlighter())
editor.resize(800, 600)
editor.setPlainText("")
editor.show()
app.exec_()
