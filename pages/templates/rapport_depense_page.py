from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel #, QLineEdit, QFormLayout
from PyQt5.QtCore import Qt

# Supposer qu'une classe RapportDepense existe dans vos modèles
# from models.documents.rapport_depense import RapportDepense

class RapportDepensePage(QWidget):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.setObjectName("RapportDepensePage")
        self.document = document # Garder une référence au modèle de données
        
        self._setup_ui()
        # self._load_data() # Pas besoin avec le QLabel simple

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Contenu simplifié pour test --- 
        test_label = QLabel(f"Ceci est la page pour: {getattr(self.document, 'title', 'Document inconnu')}")
        test_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(test_label)
        # ------------------------------------

        # --- Ancien formulaire commenté --- 
        # title_label = QLabel(\"Rapport de Dépense\")
        # ... (form layout et champs commentés) ...
        # self.setLayout(main_layout) # Déjà fait à la fin
        # ----------------------------------

        self.setLayout(main_layout)

    # --- Méthodes commentées car non utilisées avec le QLabel --- 
    # def _load_data(self):
    #     ...
    # def get_document_data(self):
    #     ...
    # -----------------------------------------------------------

# Bloc de test simple
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Simuler un objet document
    class MockRapportDepense:
        def __init__(self):
            self.nom_rapport = "Rapport Test"
            self.titre = "Déjeuner Client X"
            self.montant_total = 123.45
            
    app = QApplication(sys.argv)
    doc = MockRapportDepense()
    page = RapportDepensePage(document=doc)
    page.setWindowTitle("Test RapportDepensePage (Simplifié)")
    page.resize(400, 300)
    page.show()
    sys.exit(app.exec_()) 