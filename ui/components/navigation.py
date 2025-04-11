from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem

class NavigationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self._populate()

    def _populate(self):
        # Liste des pages et leur identifiant
        pages = [
            ("Dashboard", "dashboard"),
            ("Rapport Dépense", "rapport_depense"),
            ("Écriture Comptable", "ecriture_comptable")
        ]
        for title, identifier in pages:
            item = QListWidgetItem(title)
            item.setData(1, identifier)
            self.list_widget.addItem(item)
