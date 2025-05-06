# windows/new_document_window.py
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from ui.components.custom_titlebar import CustomTitleBar
# Importer la page de sélection de type
from pages.documents_open.documents_open_page import DocumentsOpenPage

import logging
logger = logging.getLogger('GDJ_App')

class NewDocumentWindow(QWidget):
    def __init__(self, initial_doc_type=None, initial_doc_data=None, parent=None):
        super().__init__(parent)
        # Supprimer la référence au contrôleur externe
        # self.controller = None 
        
        # Stocker les données initiales
        self.initial_doc_type = initial_doc_type
        self.initial_doc_data = initial_doc_data if initial_doc_data is not None else {}

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # Rendre la fenêtre modale pour bloquer les autres
        self.setWindowModality(Qt.ApplicationModal)
        self.setObjectName("NewDocumentWindow")
        # --- Titre dynamique basé sur le type initial? --- 
        window_title = f"Nouveau Document - {self.initial_doc_type}" if self.initial_doc_type else "Nouveau Document"
        self.setWindowTitle(window_title)
        # -------------------------------------------------

        self._init_ui()
        self.resize(800, 600) # Augmenter la taille par défaut pour les onglets
        logger.info(f"NewDocumentWindow instance créée pour type: {self.initial_doc_type}")

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Barre de titre (sans bouton menu visible par défaut)
        self.title_bar = CustomTitleBar(self, title=self.windowTitle(), icon_base_name="logo-gdj.png") 
        outer_layout.addWidget(self.title_bar)
        # Connecter la fermeture de la barre de titre à la fermeture de la fenêtre
        self.title_bar.close_requested.connect(self.close)

        # --- Contenu: DocumentsOpenPage --- 
        try:
            logger.info(f"Instanciation de DocumentsOpenPage avec type='{self.initial_doc_type}' et data='{self.initial_doc_data}'")
            self.documents_open_page = DocumentsOpenPage(initial_doc_type=self.initial_doc_type, initial_doc_data=self.initial_doc_data)
            outer_layout.addWidget(self.documents_open_page, 1) # 1 pour étendre
        except Exception as e_page:
            logger.error(f"Erreur lors de l\'instanciation de DocumentsOpenPage: {e_page}", exc_info=True)
            # Ajouter un QLabel d'erreur si la page ne peut être créée
            error_label = QLabel(f"Erreur: Impossible de charger la page de document.\n{e_page}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red;")
            outer_layout.addWidget(error_label, 1)
        # -----------------------------------

        self.setLayout(outer_layout)
        
    def closeEvent(self, event):
        """Surcharge pour logger la fermeture."""
        logger.info("NewDocumentWindow closed.")
        super().closeEvent(event)

# Bloc de test
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    # logging.basicConfig(level=logging.INFO) # -> COMMENTÉ
    
    # Charger styles et theme pour le test
    from utils.stylesheet_loader import load_stylesheet
    from utils import icon_loader, theme
    app = QApplication(sys.argv)
    try:
        qss_files = ["resources/styles/global.qss", "resources/styles/frame.qss"]
        style = load_stylesheet(qss_files, theme_name="DARK")
        app.setStyleSheet(style)
        icon_loader.set_active_theme("DARK")
    except Exception as e:
        logger.error(f"Erreur chargement style/theme pour test: {e}", exc_info=True)

    window = NewDocumentWindow()
    # Dans un vrai scénario, le MainController créerait et lierait le NewDocumentController
    window.show()
    sys.exit(app.exec_()) 