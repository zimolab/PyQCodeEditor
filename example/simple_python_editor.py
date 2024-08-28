from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters.QPythonHighlighter import QPythonHighlighter
from pyqcodeeditor.completers import QPythonCompleter

app = QApplication([])
editor = QCodeEditor()
editor.setHighlighter(QPythonHighlighter())
editor.setCompleter(QPythonCompleter())
editor.resize(800, 600)
editor.setPlainText("print('hello world!')")
editor.show()
app.exec_()
