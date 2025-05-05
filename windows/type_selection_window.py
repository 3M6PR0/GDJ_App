# windows/type_selection_window.py
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSlot as Slot
from ui.components.custom_titlebar import CustomTitleBar
from pages.documents.documents_type_selection_page import DocumentsTypeSelectionPage # <-- Importer la page cible
# --- AJOUT IMPORT CONTROLEUR ---
from controllers.documents.documents_type_selection_controller import DocumentsTypeSelectionController
# --------------------------------
# --- AJOUT IMPORTS POUR CONFIG ---
import json
import os
from utils.paths import get_resource_path
# --------------------------------
# Importer le contrôleur de préférences (nécessaire pour le contrôleur de sélection)
from controllers.preferences.preferences_controller import PreferencesController

logger = logging.getLogger(__name__)

class TypeSelectionWindow(QWidget):
    """Fenêtre dédiée à l'affichage de la page de sélection du type de document."""
    def __init__(self, preferences_controller: PreferencesController, parent=None):
        super().__init__(parent)
        # Utiliser les flags standards pour une fenêtre indépendante sans cadre natif
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setObjectName("TypeSelectionWindow")
        self.setWindowTitle("Nouveau Document - Sélection du Type")
        self.setMinimumSize(400, 300) # Taille minimale indicative

        self.preferences_controller = preferences_controller

        # --- Charger les données de config ICI --- 
        self._load_config_data()
        # ----------------------------------------

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barre de titre personnalisée
        # Masquer le bouton menu par défaut car cette fenêtre est simple?
        self.title_bar = CustomTitleBar(self, title=self.windowTitle(), icon_base_name="logo-gdj.png", show_menu_button_initially=False) 
        main_layout.addWidget(self.title_bar)

        # Séparateur (optionnel, pour style)
        separator_line = QFrame(self)
        separator_line.setObjectName("TitleSeparatorLine")
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Plain)
        separator_line.setFixedHeight(1)
        main_layout.addWidget(separator_line)

        # Contenu principal : La page de sélection
        try:
            # Instancier la page
            # Faut-il passer des arguments à DocumentsTypeSelectionPage? Supposons non pour l'instant.
            self.selection_page = DocumentsTypeSelectionPage() 
            # Ajouter la page au layout principal, en lui donnant l'espace restant
            main_layout.addWidget(self.selection_page, 1) 
            logger.info("Page DocumentsTypeSelectionPage instanciée et ajoutée à TypeSelectionWindow.")
            
            # --- MODIFICATION: Passer les données au contrôleur --- 
            self.selection_controller = DocumentsTypeSelectionController(
                view=self.selection_page, 
                document_types=self.document_types, # <- Passer les types chargés
                document_fields_map=self.document_fields_map, # <- Passer la map chargée
                preferences_controller=self.preferences_controller # <- Passer le contrôleur reçu
            )
            logger.info("Contrôleur DocumentsTypeSelectionController instancié avec les données.")
            # ------------------------------------------------------
            
            # Connecter les signaux du CONTROLEUR (et non plus de la page directement)
            # Le contrôleur gère maintenant les actions
            self.selection_controller.creation_requested.connect(self.handle_creation_request)
            self.selection_controller.cancel_requested.connect(self.close) # Annuler ferme la fenêtre
            logger.info("Signaux du DocumentsTypeSelectionController connectés.")

            # Supprimer les anciennes connexions directes à la page
            # if hasattr(self.selection_page, 'type_selected'):
            #      pass 
            # if hasattr(self.selection_page, 'cancel_requested'):
            #      self.selection_page.cancel_requested.connect(self.close)
            #      logger.info("Connecté cancel_requested de la page à self.close.")

        except Exception as e_page:
            logger.error(f"Erreur lors de l'instanciation de DocumentsTypeSelectionPage dans TypeSelectionWindow: {e_page}", exc_info=True)
            # Afficher un message d'erreur si la page ne peut être chargée
            from PyQt5.QtWidgets import QLabel
            error_label = QLabel(f"Erreur: Impossible de charger la page de sélection.\n{e_page}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red;")
            main_layout.addWidget(error_label, 1)

        self.setLayout(main_layout)
        # Définir une taille par défaut raisonnable
        self.resize(600, 450) 
        logger.info("TypeSelectionWindow instance créée.")

    # --- COPIE DE LA MÉTHODE DE DocumentsController --- 
    def _load_config_data(self, relative_filepath="data/config_data.json"):
        """Charge la config depuis le chemin relatif via get_resource_path."""
        self.document_types = []
        self.document_fields_map = {}
        # Pas besoin de charger Jacmar ici

        config_full_path = get_resource_path(relative_filepath)
        logger.debug(f"TypeSelectionWindow: Chargement config depuis: {config_full_path}")

        try:
            if not os.path.exists(config_full_path):
                logger.warning(f"Fichier config introuvable: {config_full_path}")
                return
            
            with open(config_full_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            document_config = config_data.get("document", {})
            self.document_types = list(document_config.keys())
            self.document_fields_map = document_config
            logger.info(f"Types de documents chargés par TypeSelectionWindow: {self.document_types}")

        except Exception as e:
            logger.error(f"Erreur chargement config dans TypeSelectionWindow ({config_full_path}): {e}")
    # -------------------------------------------------
    
    # --- MÉTHODE POUR GÉRER LE SIGNAL DU CONTROLEUR ---
    @Slot(str, dict)
    def handle_creation_request(self, selected_type, form_data):
        """Gère la demande de création reçue du contrôleur."""
        logger.info(f"TypeSelectionWindow: Demande de création reçue pour '{selected_type}' avec data: {form_data}")
        # TODO: Que faire ici?
        # 1. Ouvrir la DocumentWindow? 
        # 2. Émettre un autre signal vers la fenêtre parente (DocumentWindow)?
        # Pour l'instant, on ferme juste la fenêtre de sélection.
        self.close()
        
        # Exemple si on voulait ouvrir DocumentWindow directement depuis ici:
        # try:
        #    from windows.document_window import DocumentWindow
        #    # Passer les données à la nouvelle fenêtre
        #    self.doc_win = DocumentWindow(initial_doc_type=selected_type, initial_doc_data=form_data, parent=self.parent()) # parent() de TypeSelectionWindow
        #    self.doc_win.showMaximized()
        # except Exception as e_docwin:
        #    logger.error(f"Erreur ouverture DocumentWindow depuis TypeSelection: {e_docwin}")
    # ---------------------------------------------------

    # --- Méthodes potentielles pour gérer la sélection (Commentées) ---
    # def handle_type_selection(self, selected_type):

# --- Bloc de test pour la nouvelle fenêtre ---
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Configurer logging basique pour voir les messages
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
    
    app = QApplication(sys.argv)
    
    # Simuler les dépendances si nécessaire (ex: icon_loader, signals)
    try:
        from utils import icon_loader, theme, signals # Assurez-vous que ces modules peuvent être importés
        theme.set_current_theme('Sombre') # Exemple pour icon_loader
    except ImportError as e:
        print(f"Avertissement: Dépendances pour le test non trouvées ({e}), l'apparence peut être affectée.")

    # Créer un contrôleur de préférences factice pour le test
    prefs_controller = PreferencesController() 
    window = TypeSelectionWindow(preferences_controller=prefs_controller)
    window.show()
    sys.exit(app.exec_()) 