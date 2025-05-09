from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QLineEdit, QLabel, QApplication, QSizePolicy
from PyQt5.QtGui import QDoubleValidator, QPalette
from PyQt5.QtCore import Qt, pyqtSignal

class UnitInputWidget(QFrame):
    """
    Un widget combinant un QLineEdit pour une valeur numérique et un QLabel pour une unité non éditable,
    le tout dans un QFrame stylé pour ressembler à un QLineEdit standard.
    """
    # Signal émis lorsque la valeur numérique change ET est valide.
    # valueChanged = pyqtSignal(float) # Ou int si seulement des entiers sont attendus

    def __init__(self, unit_text="km", initial_value=0.0, decimals=2, parent=None):
        super().__init__(parent)
        self.setObjectName("UnitInputFrame") # Pour le styling QSS du cadre
        # Important pour que le QSS de background-color s'applique au QFrame
        self.setAttribute(Qt.WA_StyledBackground, True) 

        self._unit_text = unit_text
        self._decimals = decimals

        self._init_ui()
        self.setValue(initial_value)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2) # Marges internes similaires à un QLineEdit (ajuster au besoin)
        layout.setSpacing(2) # Petit espacement entre le nombre et l'unité

        self.line_edit = QLineEdit(self)
        self.line_edit.setObjectName("UnitValueLineEdit") # Pour un style QSS très ciblé si nécessaire
        # Style pour que le QLineEdit se fonde dans le QFrame
        self.line_edit.setStyleSheet("QLineEdit#UnitValueLineEdit { border: none; background-color: transparent; padding: 0; }")
        self.line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Validateur pour n'accepter que des nombres (flottants ici)
        # Note: QDoubleValidator utilise la locale pour le séparateur décimal (virgule ou point)
        self.validator = QDoubleValidator(self)
        self.validator.setDecimals(self._decimals)
        # self.validator.setBottom(0) # Si vous ne voulez que des valeurs positives
        self.line_edit.setValidator(self.validator)

        self.unit_label = QLabel(self._unit_text, self)
        self.unit_label.setObjectName("UnitTextLabel")
        # Essayer de faire correspondre la couleur du texte à celle du QLineEdit
        # Cela peut être hérité ou défini explicitement si nécessaire, ou via QSS global.
        # self.unit_label.setForegroundRole(QPalette.Text) # Tente d'utiliser la couleur de texte standard
        # Ou récupérer dynamiquement la couleur du texte d'un QLineEdit standard
        # temp_le = QLineEdit()
        # text_color = temp_le.palette().color(QPalette.Text)
        # self.unit_label.setStyleSheet(f"color: {text_color.name()}; background-color: transparent;")
        # Pour l'instant, on laisse le style par défaut ou via QSS global.

        layout.addWidget(self.line_edit, 1) # Le line_edit prend l'espace disponible
        layout.addWidget(self.unit_label)

        # Connecter le signal editingFinished pour valider/formater la valeur
        self.line_edit.editingFinished.connect(self._on_editing_finished)
        # self.line_edit.textChanged.connect(self._handle_text_changed_for_signal) # Si signal en temps réel

    def _on_editing_finished(self):
        """ Appelé lorsque l'édition du QLineEdit est terminée (Entrée ou perte de focus). """
        current_text = self.line_edit.text()
        state, num_str, _ = self.validator.validate(current_text, 0)

        if state == QDoubleValidator.Acceptable:
            try:
                # Essayer de convertir en float, puis reformater avec le bon nombre de décimales
                # QDoubleValidator peut accepter des formats locaux (ex: virgule), float() peut nécessiter un point.
                # Il est plus sûr de se fier à num_str qui devrait être déjà "nettoyé" par le validateur
                # si la locale est bien gérée.
                # Pour être robuste, on remplace la virgule par un point si besoin avant float()
                value = float(num_str.replace(",", "."))
                formatted_value_str = f"{value:.{self._decimals}f}" # Formatage avec le bon nombre de décimales
                # Remplacer le point par le séparateur décimal local pour l'affichage
                locale_decimal_point = QApplication.instance().locale().decimalPoint()
                if locale_decimal_point != '.':
                    formatted_value_str = formatted_value_str.replace('.', locale_decimal_point)
                
                if self.line_edit.text() != formatted_value_str:
                    self.line_edit.setText(formatted_value_str)
                # Émettre le signal valueChanged si la valeur a effectivement changé et est valide
                # if hasattr(self, 'valueChanged'): self.valueChanged.emit(value) # À décommenter si signal utilisé
            except ValueError:
                # Devrait être rare si le validateur fonctionne bien, mais en cas de souci
                self.line_edit.setText(f"{0.0:.{self._decimals}f}".replace('.', QApplication.instance().locale().decimalPoint()))
        elif state == QDoubleValidator.Intermediate:
            # L'entrée est partiellement valide (ex: "12.") mais pas complète.
            # On pourrait essayer de la corriger ou la laisser telle quelle jusqu'à ce qu'elle soit acceptable.
            # Pour l'instant, on pourrait la forcer à une valeur valide si elle ne l'est pas devenue.
            # Ou simplement la réinitialiser si c'est plus simple.
            # Forcer à la valeur numérique la plus proche ou 0.0
            try:
                value = float(current_text.replace(",","."))
                self.setValue(value) # Cela va reformater
            except:
                 self.setValue(0.0)
        else: # QDoubleValidator.Invalid
            # Réinitialiser à une valeur valide (ex: 0.0 ou la dernière valeur valide)
            self.setValue(0.0) # Ou stocker la dernière valeur valide et la restaurer

    # def _handle_text_changed_for_signal(self, text):
    #     state, num_str, _ = self.validator.validate(text, 0)
    #     if state == QDoubleValidator.Acceptable:
    #         try:
    #             value = float(num_str.replace(",", "."))
    #             if hasattr(self, 'valueChanged'): self.valueChanged.emit(value)
    #         except ValueError:
    #             pass # Ne pas émettre si la conversion échoue malgré l'état acceptable

    def value(self) -> float:
        """ Retourne la valeur numérique actuelle sous forme de float. """
        text_val = self.line_edit.text()
        # Remplacer le séparateur décimal local par un point pour la conversion en float
        locale_decimal_point = QApplication.instance().locale().decimalPoint()
        if locale_decimal_point != '.':
            text_val = text_val.replace(locale_decimal_point, '.')
        try:
            return float(text_val)
        except ValueError:
            return 0.0 # Ou lever une exception, ou retourner None

    def setValue(self, value: float):
        """ Définit la valeur numérique. """
        try:
            val = float(value)
            # Formatage avec le bon nombre de décimales et le séparateur local
            formatted_str = f"{val:.{self._decimals}f}"
            locale_decimal_point = QApplication.instance().locale().decimalPoint()
            if locale_decimal_point != '.':
                formatted_str = formatted_str.replace('.', locale_decimal_point)
            self.line_edit.setText(formatted_str)
        except (ValueError, TypeError):
            # En cas d'erreur, mettre une valeur par défaut
            default_str = f"{0.0:.{self._decimals}f}"
            locale_decimal_point = QApplication.instance().locale().decimalPoint()
            if locale_decimal_point != '.':
                default_str = default_str.replace('.', locale_decimal_point)
            self.line_edit.setText(default_str)

    def setUnitText(self, unit_text: str):
        """ Change le texte de l'unité. """
        self._unit_text = unit_text
        self.unit_label.setText(self._unit_text)

    def setReadOnly(self, readonly: bool):
        """ Rend le QLineEdit interne read-only. """
        self.line_edit.setReadOnly(readonly)
        # On pourrait aussi griser le label d'unité si read-only
        # pal = self.unit_label.palette()
        # pal.setColor(QPalette.WindowText, QGuiApplication.palette().color(QPalette.Disabled, QPalette.WindowText) if readonly else QGuiApplication.palette().color(QPalette.Active, QPalette.WindowText))
        # self.unit_label.setPalette(pal)

    # On pourrait surcharger d'autres méthodes de QLineEdit si nécessaire (ex: clear, setText)
    # ou des signaux. 