from qtpy.QtWidgets import QApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QJSONHighlighter

app = QApplication([])
editor = QCodeEditor()
editor.setHighlighter(QJSONHighlighter())
editor.resize(800, 600)
editor.setPlainText('{\n"a": [1,2,3]\n}')
editor.show()
app.exec_()
