from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QHBoxLayout, QSizePolicy, QApplication, QStyleOption, QStyle
from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QObject, pyqtSlot
from PyQt5.QtGui import QDoubleValidator, QPainter, QColor, QPen, QPaintEvent

import logging
logger = logging.getLogger('GDJ_App')

# Import direct du module de thème et des signaux
from utils import theme as theme_module
from utils.signals import signals

class NumericInputWithUnit(QWidget):
    """
    Un widget personnalisé combinant un QLineEdit pour une valeur numérique
    et un QLabel pour afficher une unité non modifiable.
    L'ensemble est stylisé pour ressembler à un QLineEdit unique.
    """
    valueChanged = pyqtSignal(float) # Signal émis lorsque la valeur numérique change

    def __init__(self, unit_text="km", initial_value=0.0, parent=None):
        super().__init__(parent)
        self.setObjectName("MyNumericInputWithUnit")
        # self.setAttribute(Qt.WA_StyledBackground, True) # Peut être nécessaire si le QSS doit dessiner le fond
        # self.setAttribute(Qt.WA_OpaquePaintEvent, True) # COMMENTÉ POUR TEST
        self._unit_text = unit_text
        self._value = initial_value
        self._is_focused = False # Nouveau drapeau pour le focus du line_edit

        # Utiliser directement les constantes globales du module theme.py
        self._border_color_focus_str = theme_module.COLOR_ACCENT
        raw_radius_str = theme_module.RADIUS_DEFAULT

        try:
            self._radius = int(str(raw_radius_str).replace('px', ''))
        except ValueError:
            logger.warning(
                f"NumericInputWithUnit: Valeur RADIUS_DEFAULT ('{raw_radius_str}') invalide depuis theme.py. Utilisation de 4px."
            )
            self._radius = 4

        # Les couleurs spécifiques au thème seront chargées par _update_theme_specific_colors
        self._border_color_normal_str = None
        self._input_background_color_str = None

        self._init_ui()
        self.setValue(self._value) # Met à jour l'affichage initial

        # Charger les couleurs initiales basées sur le thème sombre par défaut et se connecter au signal
        self._update_theme_specific_colors('Sombre') # Thème par défaut de l'application
        try:
            signals.theme_changed_signal.connect(self._update_theme_specific_colors)
        except AttributeError:
            logger.error("NumericInputWithUnit: Impossible de se connecter à signals.theme_changed_signal. L'objet 'signals' est-il initialisé ?")
        except Exception as e:
            logger.error(f"NumericInputWithUnit: Erreur lors de la connexion à theme_changed_signal: {e}")

    @pyqtSlot(str)
    def _update_theme_specific_colors(self, theme_name: str):
        logger.debug(f"NumericInputWithUnit: Réception du signal de changement de thème ou appel initial. Application du thème: {theme_name}")
        current_theme_dict = theme_module.get_theme_vars(theme_name)
        
        self._border_color_normal_str = current_theme_dict.get("COLOR_PRIMARY_LIGHTEST")
        self._input_background_color_str = current_theme_dict.get("COLOR_SEARCH_BACKGROUND")

        if self._border_color_normal_str is None:
            logger.warning(f"NumericInputWithUnit: 'COLOR_PRIMARY_LIGHTEST' non trouvée dans theme_module pour le thème '{theme_name}'. Utilisation de #CCCCCC.")
            self._border_color_normal_str = "#CCCCCC" # Fallback absolu
        
        if self._input_background_color_str is None:
            logger.warning(f"NumericInputWithUnit: 'COLOR_SEARCH_BACKGROUND' non trouvée dans theme_module pour le thème '{theme_name}'. Utilisation de #3A3A3A.")
            self._input_background_color_str = "#3A3A3A" # Fallback absolu

        logger.debug(f"NumericInputWithUnit - Couleurs après _update_theme_specific_colors ('{theme_name}') :")
        logger.debug(f"  _border_color_normal_str: {self._border_color_normal_str}")
        logger.debug(f"  _input_background_color_str: {self._input_background_color_str}")
        logger.debug(f"  _border_color_focus_str (constant): {self._border_color_focus_str}")
        logger.debug(f"  _radius (constant from theme): {self._radius}")

        self.update() # Déclencher un repaint

    def _init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Marges gérées par le style du parent
        self.main_layout.setSpacing(0) # Pas d'espacement entre le QLineEdit et le QLabel

        # QLineEdit pour la valeur numérique
        self.line_edit = QLineEdit(self)
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Validateur pour n'accepter que les nombres (flottants pour l'instant)
        # Vous pouvez ajuster la plage et le nombre de décimales si nécessaire
        self.validator = QDoubleValidator() 
        self.line_edit.setValidator(self.validator)
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.editingFinished.connect(self._on_editing_finished)

        # QLabel pour l'unité
        self.unit_label = QLabel(self._unit_text, self)
        self.unit_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # MODIFIÉ: Rendre la suppression de la bordure du QLineEdit interne plus explicite
        self.line_edit.setStyleSheet("border: 0px solid transparent; background-color: transparent; padding: 0px;")
        # Le QLabel pour l'unité aura besoin d'un peu de padding pour l'alignement visuel
        # et pour correspondre au padding du QLineEdit parent.
        # La couleur du texte devrait hériter ou être définie via le thème.
        self.unit_label.setStyleSheet("border: none; background-color: transparent; padding-right: 5px; padding-left: 5px;")

        self.main_layout.addWidget(self.line_edit)
        self.main_layout.addWidget(self.unit_label)
        
        # Installer le filtre d'événements sur le line_edit
        self.line_edit.installEventFilter(self)

        # Assurer la focus policy
        self.setFocusPolicy(Qt.StrongFocus) # Pour que le widget parent puisse recevoir le focus
        self.setFocusProxy(self.line_edit) # Transférer le focus au QLineEdit interne

        # Hauteur minimale basée sur la hauteur du QLineEdit
        # Cela aide à obtenir une taille par défaut raisonnable.
        # La hauteur réelle sera déterminée par le style QSS appliqué au NumericInputWithUnit.
        self.setMinimumHeight(self.line_edit.sizeHint().height())

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.line_edit:
            if event.type() == QEvent.FocusIn:
                self._is_focused = True
                self.repaint()
            elif event.type() == QEvent.FocusOut:
                self._is_focused = False
                self.repaint()
        return super().eventFilter(watched, event)

    def paintEvent(self, event: QPaintEvent) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True) # Garder l'anti-aliasing pour les coins lisses

        # Sauvegarder l'état du painter avant la translation
        painter.save()
        # Appliquer une translation de 0.5px pour potentiellement améliorer la netteté des lignes de 1px
        painter.translate(0.5, 0.5)

        # 1. Fond transparent (rien à dessiner pour le fond ici)

        # 2. Dessiner la bordure
        current_border_color_str = self._border_color_focus_str if self._is_focused else self._border_color_normal_str
        border_color = QColor(current_border_color_str)

        pen = QPen(border_color)
        pen.setWidth(0) # Revenir au stylo cosmétique pour une ligne de 1 pixel physique
        
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Le rectangle est ajusté pour que la ligne soit dessinée à l'intérieur.
        # Avec la translation de 0.5, les coordonnées (0,0) du rect_border 
        # correspondent maintenant au centre du pixel (0,0) du widget.
        rect_border = self.rect().adjusted(0, 0, -1, -1) 
        painter.drawRoundedRect(rect_border, self._radius, self._radius)

        # Restaurer l'état du painter (annule la translation)
        painter.restore()

    def _on_text_changed(self, text):
        # Tentative de conversion en float pendant la frappe pour une validation "douce"
        # ou pour permettre une mise à jour en temps réel si nécessaire.
        # Pour l'instant, on attend editingFinished pour émettre le signal.
        pass

    def _on_editing_finished(self):
        current_text = self.line_edit.text()
        try:
            # Utiliser la locale pour la conversion peut être important (virgule vs point)
            # Pour l'instant, on suppose un format standard que QDoubleValidator gère bien.
            val = float(current_text) # Ou self.validator.locale().toDouble(current_text)[0]
            if self._value != val:
                self._value = val
                self.valueChanged.emit(self._value)
        except ValueError:
            # Si la valeur n'est pas valide (ne devrait pas arriver avec QDoubleValidator seul),
            # réinitialiser au dernier _value connu.
            logger.warning(f"NumericInputWithUnit: Valeur invalide '{current_text}', réinitialisation à {self._value}")
            self.line_edit.setText(str(self._value))

    def value(self) -> float:
        """Retourne la valeur numérique actuelle."""
        return self._value

    def setValue(self, value: float):
        """Définit la valeur numérique."""
        try:
            val = float(value)
            self._value = val
            # Mettre à jour le QLineEdit. Bloquer les signaux pour éviter une boucle.
            self.line_edit.blockSignals(True)
            self.line_edit.setText(str(self._value))
            self.line_edit.blockSignals(False)
            # Émettre le signal si la valeur a effectivement changé via cet appel externe.
            # self.valueChanged.emit(self._value) # Discutable: émettre ici ou seulement sur interaction user?
        except ValueError:
            logger.error(f"NumericInputWithUnit: Impossible de définir la valeur sur '{value}'")

    def unitText(self) -> str:
        """Retourne le texte de l'unité actuelle."""
        return self._unit_text

    def setUnitText(self, unit_text: str):
        """Définit le texte de l'unité."""
        self._unit_text = unit_text
        self.unit_label.setText(self._unit_text)
        # Ajuster la taille du label si nécessaire
        self.unit_label.adjustSize()

    # Pour l'intégration du style (uniformité):
    # Ce widget (NumericInputWithUnit) doit être stylé via QSS (dans votre fichier global.qss par exemple)
    # en ciblant son objectName ou sa classe. Le style devrait définir :
    # - border (ex: 1px solid #CouleurBordure)
    # - border-radius
    # - background-color
    # - padding (important pour que le contenu ne touche pas la bordure)
    # 
    # Exemple QSS pour ce widget (à adapter à votre thème) :
    # NumericInputWithUnit {
    #     background-color: #CouleurFondInput;
    #     border: 1px solid #CouleurBordureInput;
    #     border-radius: 3px; /* Ou votre RADIUS_DEFAULT */
    #     padding-left: 5px; /* Ou padding du QLineEdit standard */
    # }
    # NumericInputWithUnit:focus { /* Ou :focus-within si supporté/nécessaire */
    #     border: 1px solid #CouleurBordureFocus;
    # }

    # Il faut s'assurer que le QLineEdit interne n'a pas de padding propre qui interfère.
    # Le padding du NumericInputWithUnit dictera l'espacement entre la bordure et le texte.
    # Le QLabel d'unité a un padding-right de 5px pour le séparer un peu du bord droit du widget.

    # Si vous voulez que la hauteur corresponde exactement à un QLineEdit standard,
    # vous devrez peut-être appliquer explicitement min-height et max-height dans le QSS
    # du NumericInputWithUnit, basées sur celles de vos QLineEdit. 