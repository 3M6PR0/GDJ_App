from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QSizePolicy
from PyQt5.QtCore import Qt
import logging

# Importer LamicoidDocument pour l'annotation de type et l'accès aux données
from models.documents.lamicoid.lamicoid import LamicoidDocument 

logger = logging.getLogger('GDJ_App')

class LamicoidPage(QWidget):
    """Page UI pour afficher et éditer un document Lamicoid."""
    def __init__(self, document: LamicoidDocument, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidPage")
        self.document = document
        
        self._init_ui()
        logger.debug(f"LamicoidPage initialisée pour document: {document.title}")

    def _init_ui(self):
        """Construit l'interface utilisateur de base."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Affichage du titre (non éditable ici, géré ailleurs si besoin)
        title_label = QLabel(f"Titre: {self.document.title}")
        title_label.setObjectName("DocumentTitleLabel") # Pour stylisation QSS éventuelle
        title_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # Permettre la sélection
        main_layout.addWidget(title_label)

        # Zone de contenu éditable
        self.content_edit = QTextEdit()
        self.content_edit.setObjectName("DocumentContentEdit")
        self.content_edit.setPlaceholderText("Saisissez ici le contenu de votre Lamicoid...")
        self.content_edit.setText(self.document.content)
        self.content_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Connecter la modification du texte à la mise à jour du document
        self.content_edit.textChanged.connect(self._on_content_changed)
        main_layout.addWidget(self.content_edit)

        self.setLayout(main_layout)

    def _on_content_changed(self):
        """Met à jour le contenu du document lorsque le QTextEdit change."""
        self.document.content = self.content_edit.toPlainText()
        # logger.debug(f"Contenu de Lamicoid '{self.document.title}' mis à jour.") # Peut être verbeux

    def get_document_content_for_save(self) -> str:
        """Retourne le contenu actuel de la page pour la sauvegarde."""
        # S'assure que le document a bien le dernier contenu du QTextEdit
        # Normalement _on_content_changed s'en charge, mais c'est une sécurité.
        self.document.content = self.content_edit.toPlainText()
        return self.document.content

    # Si des actions spécifiques sont nécessaires lors de la fermeture de l'onglet de cette page,
    # elles peuvent être ajoutées ici (ex: vérifier les modifications non sauvegardées).
    # def about_to_close(self):
    #     pass

    def get_document(self) -> LamicoidDocument:
        return self.document

    # Vous pourriez avoir besoin d'une méthode save_document si des actions spécifiques sont nécessaires
    # avant de sauvegarder, ou si la page gère des aspects de la sauvegarde.
    # def save_document(self):
    #     # Actions spécifiques à la sauvegarde pour la page Lamicoid si nécessaire
    #     pass

    # Ajouter d'autres méthodes nécessaires pour la gestion de la page Lamicoid 