from PyQt5.QtWidgets import QComboBox, QLineEdit, QWidget, QVBoxLayout


class ComboBoxFullText(QComboBox):
    def showPopup(self):
        popup_width = self.minimumSizeHint().width()
        font_metrics = self.view().fontMetrics()
        longest_text_width = max([font_metrics.width(self.itemText(i)) for i in range(self.count())])
        popup_width = max(popup_width, longest_text_width + 20)
        self.view().setMinimumWidth(popup_width)
        super().showPopup()

class Entry(QWidget):
    def __init__(self, presets: list = None):
        super().__init__()
        self._has_dropdown = presets is not None
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if self._has_dropdown:
            self.widget = ComboBoxFullText()
            self.widget.addItems([str(p) for p in presets])
            self.widget.setEditable(True)
        else:
            self.widget = QLineEdit()
        layout.addWidget(self.widget)

    def addCustomItem(self, value: str):
        if self._has_dropdown:
            self.widget.insertItem(self.widget.count()-1, value)

    @property
    def textChanged(self):
        if self._has_dropdown:
            return self.widget.editTextChanged
        else:
            return self.widget.textChanged

    def setText(self, text):
        if self._has_dropdown:
            self.widget.setEditText(text)
        else:
            self.widget.setText(text)

    def text(self):
        if self._has_dropdown:
            return self.widget.currentText()
        else:
            return self.widget.text()
