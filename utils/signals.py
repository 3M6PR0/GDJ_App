from PyQt5.QtCore import pyqtSignal, QObject
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

# Créer une instance globale unique de l'émetteur
signals = ThemeSignalEmitter()

logger.info("utils/signals.py defined.") 