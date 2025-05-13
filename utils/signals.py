from PyQt5.QtCore import pyqtSignal, QObject, QCoreApplication
import logging

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

# Créer une classe QObject simple pour héberger le signal
# car les signaux doivent appartenir à une instance QObject.
class ThemeSignalEmitter(QObject):
    # Signal qui émet le nouveau nom de thème (str)
    theme_changed_signal = pyqtSignal(str)
    # Signal émis quand un document est modifié (ajout, suppression, duplication d'entrée)
    document_modified = pyqtSignal()
    # Signal pour afficher des messages de statut dans la barre de statut principale
    # Args: message (str), type (str: "success", "error", "info", "warning"), duration (int, ms)
    status_message_updated = pyqtSignal(str, str, int)

signals = None # Initialiser à None

def initialize_global_signals(app_instance=None):
    """
    Initialise l'émetteur de signaux global 'signals'.
    Doit être appelé APRÈS la création de QApplication.
    """
    global signals # Nécessaire pour modifier la variable globale
    
    parent = app_instance
    if not parent:
        parent = QCoreApplication.instance()

    if parent:
        signals = ThemeSignalEmitter(parent=parent)
        logger.info(f"ThemeSignalEmitter (signals) initialized with parent: {parent}.")
    else:
        # Cela ne devrait pas arriver si appelé correctement depuis main.py
        signals = ThemeSignalEmitter() 
        logger.critical("CRITICAL: ThemeSignalEmitter (signals) initialized WITHOUT a Qt parent. "
                        "QCoreApplication.instance() returned None even during explicit initialization.")
    
    if signals is None:
        # Mesure de sécurité extrême
        logger.critical("CRITICAL: Global 'signals' instance is still None after initialization attempt!")
        # On pourrait lever une exception ici pour arrêter l'application
        # raise RuntimeError("Failed to initialize global signals.")

logger.info("utils/signals.py defined (signals will be initialized later).") 