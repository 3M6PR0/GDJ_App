from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel
from PyQt5.QtCore import Qt

class TextInputDialog(QDialog):
    def __init__(self, parent=None, current_text=""):
        super().__init__(parent)
        self.setWindowTitle("Saisir le texte")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.label = QLabel("Veuillez entrer le texte à afficher :")
        layout.addWidget(self.label)

        self.text_edit = QLineEdit(self)
        if current_text:
            self.text_edit.setText(current_text)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_text(self) -> str | None:
        if self.result() == QDialog.Accepted:
            return self.text_edit.text().strip()
        return None

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QPushButton

    app = QApplication(sys.argv)

    def open_dialog():
        dialog = TextInputDialog(current_text="Texte initial")
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.get_text()
            print(f"Texte saisi: '{text}'")
        else:
            print("Dialogue annulé")

    main_widget = QWidget()
    btn = QPushButton("Ouvrir dialogue de saisie de texte", main_widget)
    btn.clicked.connect(open_dialog)
    main_widget.show()
    
    sys.exit(app.exec_()) 