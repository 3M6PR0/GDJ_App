# controllers/documents/documents_type_selection_controller.py # <- Nouveau nom
# Gère la logique de sélection du type de document et la création.

from PyQt5.QtCore import QObject, pyqtSlot as Slot

# from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage

class DocumentsTypeSelectionController(QObject): # <- Nom de classe mis à jour
    def __init__(self, view: 'QWidget'): # ou DocumentsTypeSelectionPage
        super().__init__()
        self.view = view
        self._populate_types() # Charger les types disponibles
        self._connect_signals()

    def _populate_types(self):
        # Logique pour obtenir les types de documents possibles
        # et les ajouter à self.view.type_combo
        available_types = ["Fiche Personnage", "Journal de Campagne", "Carte"] # Exemple
        if hasattr(self.view, 'type_combo'):
            self.view.type_combo.clear() # Vider au cas où
            self.view.type_combo.addItems(available_types)
        print("Chargement des types de documents...")
        pass

    def _connect_signals(self):
        # Connecter les boutons aux slots
        if hasattr(self.view, 'create_button'):
            self.view.create_button.clicked.connect(self.create_document)
        if hasattr(self.view, 'cancel_button'):
            self.view.cancel_button.clicked.connect(self.cancel_creation)
        pass

    # --- Slots ---
    @Slot()
    def create_document(self):
        # Logique pour créer un nouveau document du type sélectionné
        selected_type = ""
        if hasattr(self.view, 'type_combo'):
             selected_type = self.view.type_combo.currentText()
        print(f"Création d'un document de type: {selected_type}...")
        # Éventuellement, émettre un signal ou appeler une méthode du contrôleur parent
        # Exemple: self.parent().document_created(selected_type) ou émettre un signal
        pass

    @Slot()
    def cancel_creation(self):
        # Logique pour annuler et revenir à la page précédente (liste récente?)
        # Peut-être émettre un signal vers le contrôleur parent
        # Exemple: self.parent().show_recent_list() ou émettre un signal
        print("Annulation de la création...")
        pass

    print("DocumentsTypeSelectionController initialized") # Debug 