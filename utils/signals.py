from PyQt5.QtCore import pyqtSignal, QObject

# Créer une classe QObject simple pour héberger le signal
# car les signaux doivent appartenir à une instance QObject.
class ThemeSignalEmitter(QObject):
    # Signal qui émet le nouveau nom de thème (str)
    theme_changed_signal = pyqtSignal(str)

# Créer une instance globale unique de l'émetteur
signals = ThemeSignalEmitter()

print("utils/signals.py defined.") 