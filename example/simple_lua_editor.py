from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QLuaHighlighter
from pyqcodeeditor.completers import QLuaCompleter

app = QApplication([])
editor = QCodeEditor()
editor.setCompleter(QLuaCompleter())
editor.setHighlighter(QLuaHighlighter())
editor.resize(800, 600)
editor.setPlainText("")
editor.show()
app.exec_()
