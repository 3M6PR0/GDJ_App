# pages/documents/documents_type_selection_page.py
"""Définit la page permettant la sélection du type de document et la saisie des champs associés."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFormLayout, 
    QLineEdit, QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot as Slot
from PyQt5.QtGui import QFont, QIcon, QPixmap
import functools
import datetime
import logging

from ui.components.frame import Frame
from utils.paths import get_resource_path
from utils import icon_loader
from utils.signals import signals

# logger = logging.getLogger(__name__) # <- Commenté
logger = logging.getLogger('GDJ_App') # <- Utiliser le logger configuré

RESET_ICON_PATH = get_resource_path("resources/icons/clear/round_refresh.png")

MONTHS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

class DocumentsTypeSelectionPage(QWidget):
    """Vue pour la sélection d'un type de document et la saisie des informations.

    Cette page contient un ComboBox pour choisir le type de document. 
    En fonction du type choisi, elle affiche dynamiquement les champs 
    appropriés (QLineEdit, QComboBox) dans un QFormLayout. Elle gère 
    également la réinitialisation individuelle des champs et émet des 
    signaux lorsque l'utilisateur demande la création ou l'annulation.

    Signals:
        create_requested (pyqtSignal(str)): Émis lorsque le bouton "Créer" 
            est cliqué. Passe le type de document sélectionné.
        cancel_requested (pyqtSignal()): Émis lorsque le bouton "Annuler" est cliqué.

    Attributes:
        type_combo (QComboBox): Le ComboBox principal pour sélectionner le type de document.
        main_content_layout (QVBoxLayout): Le layout principal du contenu du Frame.
        dynamic_content_container (QWidget | None): Le conteneur pour les widgets dynamiques.
        cancel_button (QPushButton): Le bouton "Annuler".
        create_button (QPushButton): Le bouton "Créer".
        _current_dynamic_widgets (list): Liste interne pour suivre les widgets dynamiques créés.
        _reset_buttons_map (dict): Dictionnaire pour mapper les widgets d'entrée à leurs 
            boutons de réinitialisation et effets d'opacité.
        header_icon_label (QLabel): Le label affichant l'icône dans l'en-tête.
        _header_icon_base_name (str): Le nom de base de l'icône d'en-tête.
    """
    create_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialise la DocumentsTypeSelectionPage.

        Args:
            parent: Le widget parent, ou None.
        """
        super().__init__(parent)
        self.setObjectName("DocumentsTypeSelectionPageWidget")
        self._current_dynamic_widgets = []
        self.main_content_layout = None
        self.dynamic_content_container = None
        self._reset_buttons_map = {}
        self._header_icon_base_name = "round_file_add.png"
        self.header_icon_label = None
        self._setup_ui()
        signals.theme_changed_signal.connect(self.update_theme_icons)
        logger.debug("DocumentsTypeSelectionPage initialisée.")

    def _setup_ui(self):
        """Construit l'interface utilisateur initiale de la page."""
        logger.debug("Construction de l'UI pour DocumentsTypeSelectionPage...")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10) 
        page_layout.setSpacing(10) 

        # En-tête avec icône, label et ComboBox de type
        header_layout = QHBoxLayout()
        self.header_icon_label = QLabel()
        try:
            icon_path = icon_loader.get_icon_path(self._header_icon_base_name)
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.header_icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                 logger.warning(f"Icône d'en-tête '{self._header_icon_base_name}' non trouvée: {icon_path}")
            self.header_icon_label.setFixedSize(20, 20)
        except Exception as e:
            logger.error(f"Erreur chargement icône d'en-tête: {e}")
        header_layout.addWidget(self.header_icon_label)
        
        document_label = QLabel("Nouveau document:")
        document_label.setObjectName("FormLabel")
        document_label.setFixedHeight(26)
        header_layout.addWidget(document_label)
        
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("HeaderComboBox")
        self.type_combo.setFixedHeight(26)
        # Le signal currentTextChanged sera connecté par le contrôleur
        header_layout.addWidget(self.type_combo, 1)
        
        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer")
        header_container.setLayout(header_layout)

        # Frame principal
        main_box = Frame(header_widget=header_container)
        self.main_content_layout = main_box.get_content_layout()
        self.main_content_layout.setContentsMargins(10, 10, 10, 10)
        self.main_content_layout.setSpacing(10)
        
        # Conteneur initialement vide pour le contenu dynamique
        self.dynamic_content_container = QWidget()
        self.dynamic_content_container.setStyleSheet("background-color: transparent;") # Fond transparent
        self.main_content_layout.addWidget(self.dynamic_content_container)
        self.main_content_layout.addStretch(1)

        page_layout.addWidget(main_box, 1)

        # Boutons Annuler/Créer en bas
        bottom_button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("TopNavButton") 
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        bottom_button_layout.addWidget(self.cancel_button)
        bottom_button_layout.addStretch() 
        self.create_button = QPushButton("Créer")
        self.create_button.setObjectName("TopNavButton") 
        self.create_button.clicked.connect(self._on_create_clicked)
        bottom_button_layout.addWidget(self.create_button) 
        
        page_layout.addLayout(bottom_button_layout)
        logger.debug("UI pour DocumentsTypeSelectionPage construite.")

    def _on_create_clicked(self):
        """Slot appelé lors du clic sur le bouton "Créer".
        
        Récupère le type sélectionné et émet le signal `create_requested`.
        Note: La récupération et la validation des données du formulaire dynamique
        sont gérées par le contrôleur qui écoute ce signal.
        """
        selected_type = self.type_combo.currentText()
        logger.info(f"Bouton 'Créer' cliqué pour le type: {selected_type}")
        if selected_type:
            # Le contrôleur récupérera les données via get_dynamic_form_data()
            self.create_requested.emit(selected_type)
        else:
             logger.warning("Bouton 'Créer' cliqué mais aucun type n'est sélectionné.")

    def set_document_types(self, types_list: list[str]):
        """Peuple le ComboBox principal avec la liste des types de documents.

        Args:
            types_list: Liste des noms des types de documents.
        """
        logger.debug(f"Mise à jour du ComboBox des types avec: {types_list}")
        self.type_combo.clear()
        if types_list:
            self.type_combo.addItems(types_list)
        else:
            self.type_combo.addItem("Aucun type disponible")
            self.type_combo.setEnabled(False)
        
    def update_content_area(self, fields_structure: list[str], default_values: dict, jacmar_data: dict):
        """Met à jour la zone de contenu dynamique avec les champs appropriés.

        Nettoie les anciens widgets dynamiques, puis crée et affiche les nouveaux 
        (QLineEdit, QComboBox pour la date, QComboBox pour les options Jacmar) 
        basé sur la `fields_structure` fournie. Applique les `default_values` 
        et peuple les ComboBox avec les listes de `jacmar_data`.

        Args:
            fields_structure: Liste ordonnée des noms de champs à afficher.
            default_values: Dictionnaire mappant les noms de champs à leurs valeurs par défaut.
            jacmar_data: Dictionnaire mappant les noms de champs Jacmar (ex: "emplacements") 
                à leurs listes d'options.
        """
        logger.debug(f"Mise à jour de la zone de contenu pour {len(fields_structure)} champs.")
        # logger.debug(f"  Structure reçue: {fields_structure}") # Optionnel: Trop verbeux?
        # logger.debug(f"  Valeurs défaut reçues: {default_values}")
        # logger.debug(f"  Données Jacmar reçues (clés): {list(jacmar_data.keys())}")
        
        # Nettoyer l'ancien contenu
        if self.dynamic_content_container is not None:
            # Vider le layout avant de supprimer le conteneur peut aider
            layout = self.dynamic_content_container.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
            self.main_content_layout.removeWidget(self.dynamic_content_container)
            self.dynamic_content_container.deleteLater()
            self.dynamic_content_container = None
        self._current_dynamic_widgets = [] # Réinitialiser la liste de suivi
        self._reset_buttons_map.clear() # Vider la map des boutons reset
        
        # Créer le nouveau conteneur pour les champs dynamiques
        self.dynamic_content_container = QWidget()
        self.dynamic_content_container.setStyleSheet("background-color: transparent;")
        new_form_layout = QFormLayout()
        new_form_layout.setSpacing(10)
        new_form_layout.setVerticalSpacing(8)
        self.dynamic_content_container.setLayout(new_form_layout)
        
        # Ajouter le conteneur (potentiellement vide) au layout principal
        # Insérer avant le dernier élément (qui est le stretch)
        stretch_index = self.main_content_layout.count() - 1 
        self.main_content_layout.insertWidget(stretch_index, self.dynamic_content_container)

        # Si pas de champs à créer, on s'arrête ici
        if not fields_structure:
            logger.debug("Aucun champ à afficher.")
            return

        # Créer les nouveaux champs
        logger.debug(f"Création des widgets pour les champs: {fields_structure}")
        for field_name in fields_structure:
            # Déterminer le type de widget en fonction du nom du champ
            field_type = "lineedit" # Par défaut
            if field_name == "date":
                field_type = "month_year_combo"
            elif field_name in jacmar_data:
                 field_type = "combo"
            # logger.debug(f"  -> Champ: '{field_name}', Type déduit: {field_type}")
            
            # Créer le label
            # Améliorer l'affichage du nom (remplacer _, capitaliser, cas spécifiques)
            label_text = field_name.replace('_', ' ')
            if label_text == "departements": label_text = "département"
            label_text = label_text.capitalize() + ":"
            label = QLabel(label_text)
            label.setObjectName("FormLabel")
            
            # Variables pour le widget et sa valeur initiale
            widget = None
            widget_layout = None # Layout pour widget + bouton reset
            initial_value = None
            default_pref_value = default_values.get(field_name)

            # Création spécifique pour le champ "date"
            if field_type == "month_year_combo":
                month_year_layout = QHBoxLayout()
                month_year_layout.setContentsMargins(0,0,0,0)
                month_year_layout.setSpacing(5)

                month_combo = QComboBox()
                month_combo.setObjectName("dynamic_combo_month")
                month_combo.addItems(MONTHS)
                current_month_index = datetime.date.today().month - 1
                month_combo.setCurrentIndex(current_month_index)
                initial_month_text = month_combo.currentText()
                month_combo.setProperty("initial_value", initial_month_text)
                month_year_layout.addWidget(month_combo)

                year_combo = QComboBox()
                year_combo.setObjectName("dynamic_combo_year")
                current_year = datetime.date.today().year
                years = [str(y) for y in range(current_year - 1, current_year + 2)]
                year_combo.addItems(years)
                year_combo.setCurrentText(str(current_year))
                initial_year_text = year_combo.currentText()
                year_combo.setProperty("initial_value", initial_year_text)
                month_year_layout.addWidget(year_combo)

                reset_button = QPushButton()
                reset_icon = QIcon(RESET_ICON_PATH)
                if not reset_icon.isNull():
                    reset_button.setIcon(reset_icon)
                    reset_button.setIconSize(QSize(16, 16))
                else: reset_button.setText("↺")
                reset_button.setObjectName("DynamicResetButton")
                reset_button.setFixedSize(20, 20)
                reset_button.setToolTip("Réinitialiser la date au mois/année actuels")
                reset_button.setFlat(True)
                reset_button.setFocusPolicy(Qt.NoFocus)
                opacity_effect = QGraphicsOpacityEffect(reset_button)
                opacity_effect.setOpacity(0.0)
                reset_button.setGraphicsEffect(opacity_effect)
                reset_button.setEnabled(False) # Désactivé initialement
                month_year_layout.addWidget(reset_button)

                # Stocker les infos pour le reset
                self._reset_buttons_map[month_combo] = (reset_button, opacity_effect, year_combo)

                # Connecter les signaux de changement et reset
                date_change_slot = functools.partial(self._handle_dynamic_date_change, month_combo, year_combo)
                month_combo.currentTextChanged.connect(date_change_slot)
                year_combo.currentTextChanged.connect(date_change_slot)
                date_reset_slot = functools.partial(self._reset_dynamic_date, month_combo, year_combo)
                reset_button.clicked.connect(date_reset_slot)

                new_form_layout.addRow(label, month_year_layout)
                self._current_dynamic_widgets.extend([label, month_combo, year_combo, reset_button])
                continue # Passer au champ suivant car la date est gérée
            
            # Création pour les ComboBox Jacmar
            elif field_type == "combo":
                options = jacmar_data.get(field_name, [])
                widget = QComboBox()
                widget.setObjectName(f"dynamic_combo_{field_name}")
                # Peupler avec les options, ou "N/A" si la liste est vide
                if options:
                    widget.addItems(options)
                else:
                    widget.addItem("N/A")
                    widget.setEnabled(False) # Désactiver si pas d'options
                    logger.warning(f"Aucune option trouvée pour le ComboBox '{field_name}'.")
                
                initial_value = str(default_pref_value) if default_pref_value is not None else ""
                if initial_value and widget.isEnabled():
                    index = widget.findText(initial_value, Qt.MatchFixedString)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                        # La valeur initiale est celle trouvée
                    else:
                        logger.warning(f"Valeur par défaut '{initial_value}' pour '{field_name}' non trouvée dans les options. Sélection du premier item.")
                        if widget.count() > 0: widget.setCurrentIndex(0)
                        initial_value = widget.currentText() # L'initiale devient le premier item
                elif not widget.isEnabled() and widget.count() > 0:
                    initial_value = widget.currentText() # L'initiale est "N/A"
                else:
                     initial_value = "" # Pas de valeur initiale si pas de défaut
            
            # Création pour les QLineEdit
            elif field_type == "lineedit": 
                initial_value = str(default_pref_value if default_pref_value is not None else "")
                widget = QLineEdit()
                widget.setObjectName(f"dynamic_lineedit_{field_name}")
                widget.setText(initial_value)
            
            # Cas non géré (ne devrait pas arriver avec la logique actuelle)
            else: 
                logger.error(f"Type de champ non géré '{field_type}' pour le champ '{field_name}'")
                widget = QLabel(f"Erreur: Type {field_type} inconnu")
                new_form_layout.addRow(label, widget)
                self._current_dynamic_widgets.extend([label, widget])
                continue # Passer au champ suivant

            # ---- Logique commune pour LineEdit et Combo (hors Date) ----
            widget.setProperty("initial_value", initial_value)

            # Créer le bouton Reset associé
            reset_button = QPushButton() 
            reset_button.setObjectName("DynamicResetButton")
            reset_icon = QIcon(RESET_ICON_PATH)
            if not reset_icon.isNull():
                reset_button.setIcon(reset_icon)
                reset_button.setIconSize(QSize(16, 16)) 
            else:
                logger.warning(f"Icône Reset non trouvée: {RESET_ICON_PATH}, utilisation texte.")
                reset_button.setText("↺") 
                reset_button.setFont(QFont("Arial", 10))
            reset_button.setFixedSize(20, 20) 
            reset_button.setToolTip(f"Réinitialiser {field_name} à sa valeur initiale")
            reset_button.setFlat(True) 
            reset_button.setFocusPolicy(Qt.NoFocus) 
            opacity_effect = QGraphicsOpacityEffect(reset_button)
            opacity_effect.setOpacity(0.0) 
            reset_button.setGraphicsEffect(opacity_effect)
            reset_button.setEnabled(False) # Désactivé initialement

            # Stocker les infos pour le reset
            self._reset_buttons_map[widget] = (reset_button, opacity_effect)

            # Mettre le widget et le bouton reset dans un layout horizontal
            widget_layout = QHBoxLayout()
            widget_layout.setContentsMargins(0,0,0,0)
            widget_layout.setSpacing(5)
            widget_layout.addWidget(widget, 1) # Le widget prend l'espace
            widget_layout.addWidget(reset_button)

            # Connecter les signaux de changement et reset
            change_slot = functools.partial(self._handle_dynamic_field_change, widget)
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(change_slot)
            elif isinstance(widget, QComboBox):
                # Connecter seulement si le combo est activé (a des options)
                if widget.isEnabled():
                    widget.currentTextChanged.connect(change_slot)
            
            reset_slot = functools.partial(self._reset_dynamic_field, widget)
            reset_button.clicked.connect(reset_slot)
            
            # Ajouter la ligne au formulaire
            new_form_layout.addRow(label, widget_layout)
            self._current_dynamic_widgets.extend([label, widget, reset_button])
            # -------------------------------------------------------------
        
        logger.debug("Formulaire dynamique mis à jour et affiché.")

    def _handle_dynamic_field_change(self, input_widget: QWidget):
        """Slot appelé quand la valeur d'un champ dynamique (hors date) change.
        
        Compare la valeur actuelle avec la valeur initiale stockée et ajuste 
        l'apparence (opacité, état enabled) du bouton de réinitialisation.

        Args:
            input_widget: Le widget (QLineEdit ou QComboBox) dont la valeur a changé.
        """
        map_entry = self._reset_buttons_map.get(input_widget)
        if not map_entry:
            logger.warning(f"_handle_dynamic_field_change appelé pour un widget non suivi: {input_widget}")
            return
        reset_button, opacity_effect = map_entry

        initial_value = input_widget.property("initial_value")
        current_value = ""
        if isinstance(input_widget, QLineEdit):
            current_value = input_widget.text()
        elif isinstance(input_widget, QComboBox):
            current_value = input_widget.currentText()
        else:
             logger.warning(f"_handle_dynamic_field_change appelé pour un type de widget inattendu: {type(input_widget)}")
             return

        is_different = (str(current_value) != str(initial_value))
        
        # Mettre à jour l'apparence du bouton reset
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        reset_button.setEnabled(is_different)

    def _reset_dynamic_field(self, input_widget: QWidget):
        """Slot appelé lors du clic sur le bouton Reset d'un champ dynamique.
        
        Réinitialise la valeur du widget à sa valeur initiale stockée et 
        cache/désactive le bouton Reset.

        Args:
            input_widget: Le widget (QLineEdit ou QComboBox) à réinitialiser.
        """
        map_entry = self._reset_buttons_map.get(input_widget)
        if not map_entry:
             logger.warning(f"_reset_dynamic_field appelé pour un widget non suivi: {input_widget}")
             return
        reset_button, opacity_effect = map_entry
        initial_value = input_widget.property("initial_value")
        
        logger.debug(f"Réinitialisation de {input_widget.objectName()} à '{initial_value}'")
        
        try:
            input_widget.blockSignals(True) # Bloquer signaux pendant mise à jour
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(str(initial_value))
            elif isinstance(input_widget, QComboBox):
                index = input_widget.findText(str(initial_value), Qt.MatchFixedString)
                if index >= 0:
                    input_widget.setCurrentIndex(index)
                else:
                     logger.warning(f"Impossible de retrouver '{initial_value}' dans {input_widget.objectName()} lors du reset.")
                     # Que faire? Laisser tel quel ou mettre au premier index?
                     # if input_widget.count() > 0: input_widget.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Erreur pendant la réinitialisation de {input_widget.objectName()}: {e}")
        finally:
             input_widget.blockSignals(False) # Réactiver signaux
        
        # Cacher/désactiver le bouton
        opacity_effect.setOpacity(0.0)
        reset_button.setEnabled(False)

    def _handle_dynamic_date_change(self, month_combo: QComboBox, year_combo: QComboBox):
        """Slot appelé quand la valeur du mois ou de l'année change.
        
        Compare la date actuelle (mois+année) avec la date initiale stockée 
        et ajuste l'apparence du bouton Reset associé.

        Args:
            month_combo: Le ComboBox du mois.
            year_combo: Le ComboBox de l'année.
        """
        map_entry = self._reset_buttons_map.get(month_combo)
        if not map_entry:
             logger.warning("_handle_dynamic_date_change appelé pour un widget non suivi.")
             return
        reset_button, opacity_effect, _ = map_entry # On a aussi stocké year_combo mais pas besoin ici

        initial_month = month_combo.property("initial_value")
        initial_year = year_combo.property("initial_value")
        current_month = month_combo.currentText()
        current_year = year_combo.currentText()

        is_different = (current_month != initial_month or current_year != initial_year)
        
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        reset_button.setEnabled(is_different)

    def _reset_dynamic_date(self, month_combo: QComboBox, year_combo: QComboBox):
        """Slot appelé lors du clic sur le bouton Reset du champ Date.
        
        Réinitialise le mois et l'année à leurs valeurs initiales et 
        cache/désactive le bouton Reset.

        Args:
            month_combo: Le ComboBox du mois.
            year_combo: Le ComboBox de l'année.
        """
        map_entry = self._reset_buttons_map.get(month_combo)
        if not map_entry:
             logger.warning("_reset_dynamic_date appelé pour un widget non suivi.")
             return
        reset_button, opacity_effect, _ = map_entry
        initial_month = month_combo.property("initial_value")
        initial_year = year_combo.property("initial_value")
        
        logger.debug(f"Réinitialisation de la date à {initial_month} {initial_year}")
        
        try:
            month_combo.blockSignals(True)
            year_combo.blockSignals(True)
            month_index = month_combo.findText(initial_month, Qt.MatchFixedString)
            year_index = year_combo.findText(initial_year, Qt.MatchFixedString)
            if month_index >= 0: month_combo.setCurrentIndex(month_index)
            else: logger.warning(f"Impossible de retrouver le mois initial '{initial_month}' lors du reset.")
            if year_index >= 0: year_combo.setCurrentIndex(year_index)
            else: logger.warning(f"Impossible de retrouver l'année initiale '{initial_year}' lors du reset.")
        except Exception as e:
            logger.error(f"Erreur pendant la réinitialisation de la date: {e}")
        finally:
            month_combo.blockSignals(False)
            year_combo.blockSignals(False)

        opacity_effect.setOpacity(0.0)
        reset_button.setEnabled(False)

    def get_dynamic_form_data(self) -> dict:
        """Récupère les données actuellement saisies dans les champs dynamiques.
        
        Parcourt les widgets dynamiques stockés (hors labels et boutons reset) 
        et retourne un dictionnaire où les clés sont les noms des champs 
        (dérivés des objectName) et les valeurs sont les données saisies.
        Pour le champ date, retourne une chaîne "Mois Année".

        Returns:
            Un dictionnaire contenant les données du formulaire dynamique.
        """
        data = {}
        month_value, year_value = None, None # Pour stocker la date
        
        for widget in self._current_dynamic_widgets:
            obj_name = widget.objectName()
            
            # Ignorer les labels et les boutons reset
            if isinstance(widget, (QLabel, QPushButton)):
                continue 
                
            field_name = ""
            value = None

            if isinstance(widget, QLineEdit):
                # Extraire le nom du champ depuis l'objectName (ex: "dynamic_lineedit_nom")
                if obj_name.startswith("dynamic_lineedit_"):
                    field_name = obj_name.replace("dynamic_lineedit_", "")
                    value = widget.text()
            elif isinstance(widget, QComboBox):
                # Gérer les combos Jacmar
                if obj_name.startswith("dynamic_combo_") and not obj_name.endswith(("_month", "_year")):
                    field_name = obj_name.replace("dynamic_combo_", "")
                    value = widget.currentText()
                    # Ne pas inclure si la valeur est "N/A" (indique des options manquantes)
                    if value == "N/A": value = None 
                # Gérer le combo Mois
                elif obj_name == "dynamic_combo_month":
                    month_value = widget.currentText()
                    continue # Traiter la date à la fin
                # Gérer le combo Année
                elif obj_name == "dynamic_combo_year":
                    year_value = widget.currentText()
                    continue # Traiter la date à la fin
            
            # Ajouter au dictionnaire si un nom et une valeur ont été trouvés
            if field_name and value is not None:
                data[field_name] = value
            # elif not isinstance(widget, (QComboBox)): # Log si widget non géré (hors combos date traités séparément)
                 # logger.warning(f"get_dynamic_form_data: Widget non traité: {widget.objectName()} ({type(widget)})")

        # Gérer le champ date combiné à la fin
        if month_value is not None and year_value is not None:
            data["date"] = f"{month_value} {year_value}"
            
        logger.debug(f"Données extraites du formulaire dynamique: {data}")
        return data

    @Slot(str)
    def update_theme_icons(self, theme_name: str):
        """Met à jour les icônes de la page lorsque le thème change."""
        logger.debug(f"Mise à jour des icônes de DocumentsTypeSelectionPage pour le thème: {theme_name}")
        # Mettre à jour l'icône d'en-tête
        if self.header_icon_label:
            try:
                new_icon_path = icon_loader.get_icon_path(self._header_icon_base_name)
                pixmap = QPixmap(new_icon_path)
                if not pixmap.isNull():
                     self.header_icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                     self.header_icon_label.clear()
            except Exception as e:
                 logger.error(f"Erreur mise à jour icône d'en-tête: {e}")
        
        # Mettre à jour l'icône Reset (si elle existe)
        # Note: les boutons reset dynamiques sont recréés, pas besoin de les màj ici
        # Si une icône reset statique existait, il faudrait la mettre à jour ici.