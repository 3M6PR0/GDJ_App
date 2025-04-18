# pages/preferences_page.py
# Définit l'interface utilisateur (QWidget) pour la page des Préférences.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel # Correction: PyQt5

class PreferencesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("Contenu de la page Préférences (UI)")
        layout.addWidget(label)
        self.setLayout(layout)
        print("PreferencesPage UI initialized") # Debug 