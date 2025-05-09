# controllers/about/about_controller.py # <- Chemin mis à jour
# Contient la logique principale pour la page "A Propos", gère l'instanciation
# et la navigation entre les sous-contrôleurs/pages (README, Notes de version).

import sys # Ajout sys pour append path si nécessaire (bonne pratique)
import os # Ajout os pour path manipulation
import logging # AJOUT Logging
from PyQt5.QtCore import QObject, pyqtSlot as Slot
from PyQt5.QtWidgets import QListWidgetItem # AJOUT pour type hint/vérif
from PyQt5.QtCore import Qt # AJOUT pour Qt.MatchExactly

# Import de la vue principale et des vues/contrôleurs des sous-pages
from pages.about.about_page import AboutPage # Importer la vue parente
from pages.about.about_readme_page import AboutReadmePage
from .about_readme_controller import AboutReadmeController
from pages.about.about_release_notes_page import AboutReleaseNotesPage
from .about_release_notes_controller import AboutReleaseNotesController

logger = logging.getLogger('GDJ_App') # OBTENIR LE LOGGER

class AboutController(QObject):
    # Utiliser le type spécifique pour la vue
    def __init__(self, view: AboutPage, version_str: str = "?.?.?"):
        # Passer la vue comme parent à QObject
        super().__init__(view)
        # self.view référence toujours la vue, qui est maintenant aussi self.parent()
        self.view = view
        self.version_str = version_str # Stocker la version
        
        logger.debug(f"AboutController.__init__: Received view id={id(self.view)}")
        stack_exists = hasattr(self.view, 'stack')
        logger.debug(f"AboutController.__init__: hasattr(self.view, 'stack') -> {stack_exists}")
        if stack_exists:
            stack_value = self.view.stack
            logger.debug(f"AboutController.__init__: self.view.stack is id={id(stack_value)} (type: {type(stack_value)}) - Is None: {stack_value is None}")
        else:
            logger.warning("AboutController.__init__: self.view.stack attribute does not exist") # Warn ici
        
        # --- Instancier les vues et contrôleurs des sous-pages --- 
        self.readme_page = AboutReadmePage()
        # Instanciation simple, sans passer de couleurs
        self.readme_controller = AboutReadmeController(
            self.readme_page, 
            version_str=self.version_str
        )
        
        self.notes_page = AboutReleaseNotesPage()
        self.notes_controller = AboutReleaseNotesController(self.notes_page)
        
        # --- Ajouter les vues au QStackedWidget de la vue principale (AboutPage) --- 
        logger.debug(f"AboutController.__init__: Just BEFORE adding widgets check - hasattr(stack)? {hasattr(self.view, 'stack')}, stack is None? {getattr(self.view, 'stack', None) is None}")

        # Récupérer explicitement le stack AVANT le if
        stack_widget = getattr(self.view, 'stack', None)
        logger.debug(f"AboutController.__init__: Got stack_widget: id={id(stack_widget) if stack_widget else 'None'}, is None? {stack_widget is None}")

        # Simplifier la condition et ajouter des logs dedans
        if stack_widget is not None:
            logger.debug(f"AboutController.__init__: Condition 'stack_widget is not None' PASSED. Attempting addWidget.")
            try:
                logger.debug(f"Attempting addWidget(readme_page)... Stack ID: {id(stack_widget)}")
                stack_widget.addWidget(self.readme_page)
                logger.debug(f"Added readme_page. Attempting addWidget(notes_page)... Stack ID: {id(stack_widget)}")
                stack_widget.addWidget(self.notes_page)
                logger.debug("AboutController.__init__: Widgets added successfully.")
            except Exception as e:
                logger.error(f"ERROR during addWidget in AboutController: {e}", exc_info=True) # Error + trace
        else:
            logger.error("ERREUR: stack_widget was None LORS DE L'AJOUT in AboutController") # Error ici
        
        self._connect_signals()
        # Vérifier l'état du stack juste avant show_readme
        final_stack_check = getattr(self.view, 'stack', None)
        logger.debug(f"AboutController.__init__: Just BEFORE calling show_readme - stack exists? {final_stack_check is not None}")
        self.show_readme() # Afficher le README par défaut

    def _connect_signals(self):
        # Supprimer les anciennes connexions aux boutons de self.view
        # if hasattr(self.view, 'btn_show_readme'):
        #     ...
        # if hasattr(self.view, 'btn_show_notes'):
        #     ...
        
        # Connecter les signaux émis par les sous-pages aux slots de ce contrôleur
        try:
            self.readme_page.request_show_notes.connect(self.show_release_notes)
            logger.debug("Connected readme_page.request_show_notes to show_release_notes slot.")
        except AttributeError:
            logger.error("ERROR: readme_page does not have signal request_show_notes")
        except Exception as e:
             logger.error(f"ERROR connecting readme_page signal: {e}", exc_info=True)
             
        try:
            self.notes_page.request_show_readme.connect(self.show_readme)
            logger.debug("Connected notes_page.request_show_readme to show_readme slot.")
        except AttributeError:
            logger.error("ERROR: notes_page does not have signal request_show_readme")
        except Exception as e:
             logger.error(f"ERROR connecting notes_page signal: {e}", exc_info=True)

        # Ajouter d'autres connexions si les sous-contrôleurs émettent des signaux
        pass

    # --- Slots pour la navigation interne --- 
    @Slot()
    def show_readme(self):
        stack_widget = getattr(self.view, 'stack', None) # Récupérer à nouveau
        logger.debug(f"show_readme - stack exists? {stack_widget is not None}")
        if stack_widget is not None:
            stack_widget.setCurrentWidget(self.readme_page)
            logger.info("Affichage de la page README (via AboutController)")
        else:
             logger.error("ERREUR: Tentative d'affichage README mais stack non trouvé dans show_readme")

    @Slot()
    def show_release_notes(self):
        stack_widget = getattr(self.view, 'stack', None) # Récupérer à nouveau
        logger.debug(f"show_release_notes - stack exists? {stack_widget is not None}")
        if stack_widget is not None:
            stack_widget.setCurrentWidget(self.notes_page)
            logger.info("Affichage des Notes de Version (via AboutController)")
            # --- Optionnel: Forcer la sélection dans la liste de navigation ---
            # Si la vue a une référence directe à la liste, on peut chercher l'item
            if hasattr(self.view, 'navigation_widget') and self.view.navigation_widget is not None: # Check not None
                list_widget = self.view.navigation_widget
                items = list_widget.findItems("Notes de version", Qt.MatchExactly)
                if items:
                    list_widget.setCurrentItem(items[0])
                    logger.debug("Item 'Notes de version' sélectionné dans la liste de navigation.")
                else:
                    logger.warning("Avertissement: Item 'Notes de version' non trouvé dans la liste de navigation.")
            else:
                logger.warning("AboutController: navigation_widget not found or is None in view.")
            # --- Fin optionnel ---
        else:
             logger.error("ERREUR: Tentative d'affichage Notes mais stack non trouvé dans show_release_notes")

    # --- MÉTHODE POUR ACTIVATION PROGRAMMATIQUE --- 
    @Slot() # Peut aussi être appelé par un signal si besoin
    def activate_release_notes_tab(self):
        """Méthode publique pour activer l'onglet/page des notes de version."""
        logger.info("Activation programmatique de l'onglet Notes de version...")
        self.show_release_notes() # Réutilise la logique existante
    # --- FIN MÉTHODE ACTIVATION ---

    # Ajouter une méthode pour afficher la page par défaut
    def show_default_page(self):
        """Affiche la page par défaut (README)."""
        self.show_readme()

logger.info("AboutController (dans controllers/about/) initialized with subpages") # Debug -> Info 