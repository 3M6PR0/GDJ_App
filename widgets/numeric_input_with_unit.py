from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QHBoxLayout, QSizePolicy, QApplication
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator # Pour la validation des nombres décimaux

import logging
logger = logging.getLogger('GDJ_App')

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
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._unit_text = unit_text
        self._value = initial_value

        self._init_ui()
        self.setValue(self._value) # Met à jour l'affichage initial

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
        
        # Style interne pour que le QLineEdit et le QLabel s'intègrent bien
        # Le QLineEdit interne ne devrait pas avoir de bordure propre ni de fond,
        # car c'est le widget NumericInputWithUnit (parent) qui sera stylé.
        self.line_edit.setStyleSheet("border: none; background-color: transparent;")
        # Le QLabel pour l'unité aura besoin d'un peu de padding pour l'alignement visuel
        # et pour correspondre au padding du QLineEdit parent.
        # La couleur du texte devrait hériter ou être définie via le thème.
        self.unit_label.setStyleSheet("border: none; background-color: transparent; padding-right: 5px; padding-left: 5px;")

        self.main_layout.addWidget(self.line_edit)
        self.main_layout.addWidget(self.unit_label)
        
        # Assurer la focus policy
        self.setFocusPolicy(Qt.StrongFocus) # Pour que le widget parent puisse recevoir le focus
        self.setFocusProxy(self.line_edit) # Transférer le focus au QLineEdit interne

        # Hauteur minimale basée sur la hauteur du QLineEdit
        # Cela aide à obtenir une taille par défaut raisonnable.
        # La hauteur réelle sera déterminée par le style QSS appliqué au NumericInputWithUnit.
        self.setMinimumHeight(self.line_edit.sizeHint().height())

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