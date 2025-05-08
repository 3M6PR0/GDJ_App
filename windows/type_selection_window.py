# windows/type_selection_window.py
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSlot as Slot, pyqtSignal
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

logger = logging.getLogger('GDJ_App')

class TypeSelectionWindow(QWidget):
    """Fenêtre dédiée à l'affichage de la page de sélection du type de document."""
    # --- AJOUT: Signal émis par cette fenêtre --- 
    document_creation_requested = pyqtSignal(str, dict)
    # -------------------------------------------

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
            self.selection_page = DocumentsTypeSelectionPage() 
            main_layout.addWidget(self.selection_page, 1) 
            logger.info("Page DocumentsTypeSelectionPage instanciée et ajoutée à TypeSelectionWindow.")
            
            # --- AJOUT: Extraire les données nécessaires du PreferencesController --- 
            default_values = {}
            jacmar_options = {}
            if self.preferences_controller:
                current_prefs = self.preferences_controller.current_preferences
                if current_prefs:
                    # Récupérer les valeurs par défaut
                    if current_prefs.profile:
                        default_values["nom"] = current_prefs.profile.nom
                        default_values["prenom"] = current_prefs.profile.prenom
                    if current_prefs.jacmar:
                        default_values["emplacements"] = current_prefs.jacmar.emplacement
                        default_values["departements"] = current_prefs.jacmar.departement
                        default_values["superviseurs"] = current_prefs.jacmar.superviseur
                        default_values["plafond_deplacement"] = current_prefs.jacmar.plafond
                    logger.info(f"Données par défaut extraites: {default_values}")
                    
                    # Récupérer les listes pour les combos Jacmar (depuis PrefsController)
                    jacmar_options["emplacements"] = getattr(self.preferences_controller, 'jacmar_emplacements', [])
                    jacmar_options["departements"] = getattr(self.preferences_controller, 'jacmar_departements', [])
                    jacmar_options["titres"] = getattr(self.preferences_controller, 'jacmar_titres', [])
                    jacmar_options["superviseurs"] = getattr(self.preferences_controller, 'jacmar_superviseurs', [])
                    jacmar_options["plafond_deplacement"] = getattr(self.preferences_controller, 'jacmar_plafonds', [])
                    logger.info(f"Options Jacmar extraites: {list(jacmar_options.keys())}")
                else:
                    logger.warning("TypeSelectionWindow: current_preferences est None dans PreferencesController.")
            else:
                logger.warning("TypeSelectionWindow: preferences_controller non fourni.")
            # ----------------------------------------------------------------------
            
            # --- AJOUT LOG: Vérifier les données extraites AVANT passage --- 
            logger.debug("-"*20 + " DEBUG TypeSelectionWindow - Données extraites " + "-"*20)
            logger.debug(f"  default_values: {default_values}")
            logger.debug(f"  jacmar_options: {jacmar_options}")
            logger.debug(f"  document_types: {self.document_types}")
            logger.debug(f"  document_fields_map: {self.document_fields_map}")
            logger.debug("-"*60)
            # -------------------------------------------------------------
            
            # --- MODIFICATION: Simplifier l'appel au constructeur --- 
            self.selection_controller = DocumentsTypeSelectionController(
                view=self.selection_page
            )
            logger.info("Contrôleur DocumentsTypeSelectionController instancié.")
            # ------------------------------------------------------
            
            # --- Connecter les signaux du CONTROLEUR --- 
            # Connecter creation_requested n'est plus nécessaire ici si on connecte create_request ci-dessous
            # self.selection_controller.creation_requested.connect(self.handle_creation_request)
            self.selection_controller.cancel_requested.connect(self.close) # Annuler ferme la fenêtre
            logger.info("Signal cancel_requested du contrôleur connecté à self.close.")

            # --- Connecter le signal interne `create_request` au signal externe --- 
            if hasattr(self.selection_controller, 'create_request'):
                self.selection_controller.create_request.connect(self.document_creation_requested.emit)
                logger.info("TypeSelectionWindow: Connecté internal controller.create_request -> self.document_creation_requested")
            else:
                logger.warning("TypeSelectionWindow: Internal selection_controller n'a pas le signal 'create_request'.")
            # ----------------------------------------------------------------------

            # --- AJOUT: Activer le contrôleur pour l'affichage initial --- 
            try:
                self.selection_controller.activate()
                logger.info("TypeSelectionWindow: selection_controller activated for initial display.")
            except Exception as e_activate:
                logger.error(f"Erreur lors de l'activation initiale du selection_controller: {e_activate}")
            # -----------------------------------------------------------

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
        logger.warning(f"Avertissement: Dépendances pour le test non trouvées ({e}), l'apparence peut être affectée.")

    # Créer un contrôleur de préférences factice pour le test
    prefs_controller = PreferencesController() 
    window = TypeSelectionWindow(preferences_controller=prefs_controller)
    window.show()
    sys.exit(app.exec_()) 