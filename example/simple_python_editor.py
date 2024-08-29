from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QPythonHighlighter
from pyqcodeeditor.completers import QPythonCompleter

app = QApplication([])
editor = QCodeEditor()
editor.setCompleter(QPythonCompleter())
editor.setHighlighter(QPythonHighlighter())
editor.resize(800, 600)
editor.setPlainText("print('hello world!')")
editor.show()
app.exec_()
