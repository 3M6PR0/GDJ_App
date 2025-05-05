# pages/documents/documents_type_selection_page.py # <- Nouveau nom
# Permet à l'utilisateur de choisir le type de nouveau document à créer.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFormLayout, 
    QLineEdit, QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot as Slot
from PyQt5.QtGui import QFont, QIcon, QPixmap
import functools
import datetime # Importer datetime
from ui.components.frame import Frame

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path
from utils import icon_loader
from utils.signals import signals

# Définir le chemin de l'icône en utilisant la fonction utilitaire
RESET_ICON_PATH = get_resource_path("resources/icons/clear/round_refresh.png")

# Liste des mois (pourrait être générée avec locale si besoin)
MONTHS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]

class DocumentsTypeSelectionPage(QWidget):
    # Ajouter les signaux manquants
    create_requested = pyqtSignal(str) # Émet le type de document choisi
    cancel_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsTypeSelectionPageWidget") # Ajouter ID si besoin
        self._current_dynamic_widgets = [] # Pour garder trace des widgets créés
        self.main_content_layout = None # Pour stocker le layout parent
        self.dynamic_content_container = None # Initialiser à None
        # Dictionnaire pour stocker (bouton, effet) associés aux widgets d'entrée
        self._reset_buttons_map = {}
        self._header_icon_base_name = "round_file_add.png" # Nom de base de l'icône d'en-tête
        self.header_icon_label = None # Pour stocker le QLabel de l'icône
        self._setup_ui()
        signals.theme_changed_signal.connect(self.update_theme_icons)

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10) 
        page_layout.setSpacing(10) 

        # --- Créer le contenu de l'en-tête --- 
        header_layout = QHBoxLayout()
        self.header_icon_label = QLabel()
        try:
            icon_path = icon_loader.get_icon_path(self._header_icon_base_name)
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.header_icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                 print(f"WARN: Header icon '{self._header_icon_base_name}' not found at {icon_path}")
            self.header_icon_label.setFixedSize(20, 20)
        except Exception as e:
            print(f"ERROR loading initial header icon: {e}")
        header_layout.addWidget(self.header_icon_label)
        document_label = QLabel("Nouveau document:")
        document_label.setObjectName("FormLabel")
        document_label.setFixedHeight(26)
        header_layout.addWidget(document_label)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("HeaderComboBox")
        self.type_combo.setFixedHeight(26)
        header_layout.addWidget(self.type_combo, 1)
        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer")
        header_container.setLayout(header_layout)

        # --- Créer le Frame principal avec l'en-tête personnalisé --- 
        main_box = Frame(header_widget=header_container)
        # Stocker la référence au layout du contenu du Frame
        self.main_content_layout = main_box.get_content_layout()
        self.main_content_layout.setContentsMargins(10, 10, 10, 10)
        self.main_content_layout.setSpacing(10)
        
        # --- Créer le placeholder initial (vide) ---
        self.dynamic_content_container = QWidget() # Créer un QWidget vide initial
        self.main_content_layout.addWidget(self.dynamic_content_container)
        self.main_content_layout.addStretch(1)

        # Ajouter le Frame au layout de la page AVEC un stretch factor
        page_layout.addWidget(main_box, 1) # Le stretch factor 1 le fait s'étendre

        # --- Ajouter les boutons Annuler/Créer SOUS le Frame --- 
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
        
        # Ajouter le layout des boutons au layout principal de la page
        page_layout.addLayout(bottom_button_layout)

        print("DocumentsTypeSelectionPage UI: Frame expands, Buttons Below")

    def _on_create_clicked(self):
        selected_type = self.type_combo.currentText()
        if selected_type:
            dynamic_data = self.get_dynamic_form_data() # Récupérer les données saisies
            # Émettre le type ET les données saisies
            # Le signal doit être modifié pour accepter un dict, ou utiliser un autre signal
            # Pour l'instant, on émet juste le type comme avant, mais avec les données disponibles
            print(f"Création demandée pour {selected_type} avec données: {dynamic_data}")
            # === Modification potentielle nécessaire ici pour passer dynamic_data ===
            self.create_requested.emit(selected_type) 

    # Méthode pour remplir la combobox depuis le contrôleur
    def set_document_types(self, types_list):
        self.type_combo.clear()
        self.type_combo.addItems(types_list) 

    def update_content_area(self, fields_structure: list, default_values: dict, jacmar_data: dict):
        """Nettoie et repeuple avec formulaire, gère le champ date spécial."""
        # --- AJOUT LOG: Afficher les arguments reçus --- 
        print("DEBUG (View - update_content_area): Received:")
        # --- MODIFICATION LOG: Afficher la liste directement --- 
        print(f"  -> fields_structure (list): {fields_structure}")
        # ------------------------------------------------------
        print(f"  -> default_values: {default_values}")
        print(f"  -> jacmar_data keys: {list(jacmar_data.keys())}")
        # ----------------------------------------------
        
        # 1. Supprimer l'ancien conteneur et nettoyer la map
        if self.dynamic_content_container is not None:
            self.main_content_layout.removeWidget(self.dynamic_content_container)
            self.dynamic_content_container.deleteLater()
            self.dynamic_content_container = None
        self._current_dynamic_widgets = []
        self._reset_buttons_map.clear()
        
        # 2. Créer le nouveau conteneur
        self.dynamic_content_container = QWidget()
        self.dynamic_content_container.setStyleSheet("background-color: transparent;")
        
        # 3. Si pas de données, ajouter conteneur vide et sortir
        if not fields_structure:
            stretch_index = self.main_content_layout.count() - 1
            self.main_content_layout.insertWidget(stretch_index, self.dynamic_content_container)
            return

        # 4. Créer et peupler le nouveau formulaire
        new_form_layout = QFormLayout()
        new_form_layout.setSpacing(10)
        new_form_layout.setVerticalSpacing(8)

        # --- AJOUT LOG: Début de la boucle --- 
        print(f"DEBUG (View): Starting loop to create {len(fields_structure)} fields...")
        # -------------------------------------
        for field_name in fields_structure:
            # --- AJOUT LOG: Champ en cours --- 
            print(f"  -> Processing field: '{field_name}'")
            # ---------------------------------
            
            # --- Déduire le type de widget DANS la boucle --- 
            field_type = "lineedit" # Type par défaut
            if field_name == "date":
                field_type = "month_year_combo"
            elif field_name in jacmar_data: # Si le nom existe comme clé dans jacmar_data, c'est un combo
                 field_type = "combo"
            # Ajouter d'autres logiques si nécessaire (ex: type explicite dans config?)
            print(f"    -> Deduced field type: {field_type}")
            # ------------------------------------------------
            
            label_text = field_name.replace('_', ' ').replace("departements", "département").capitalize() + ":"
            label = QLabel(label_text)
            label.setObjectName("FormLabel")
            
            widget = None
            widget_layout = None
            initial_value = None
            default_pref_value = default_values.get(field_name)

            # --- GESTION SPÉCIFIQUE DU CHAMP DATE --- 
            if field_type == "month_year_combo":
                month_year_layout = QHBoxLayout()
                month_year_layout.setContentsMargins(0,0,0,0)
                month_year_layout.setSpacing(5)

                # Combo Mois
                month_combo = QComboBox()
                month_combo.setObjectName("dynamic_combo_month")
                month_combo.addItems(MONTHS)
                current_month_index = datetime.date.today().month - 1
                month_combo.setCurrentIndex(current_month_index)
                initial_month_text = month_combo.currentText()
                month_combo.setProperty("initial_value", initial_month_text)
                month_year_layout.addWidget(month_combo)

                # Combo Année
                year_combo = QComboBox()
                year_combo.setObjectName("dynamic_combo_year")
                current_year = datetime.date.today().year
                years = [str(y) for y in range(current_year - 1, current_year + 2)]
                year_combo.addItems(years)
                year_combo.setCurrentText(str(current_year))
                initial_year_text = year_combo.currentText()
                year_combo.setProperty("initial_value", initial_year_text)
                month_year_layout.addWidget(year_combo)

                # Bouton Reset (unique pour les deux combos)
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
                reset_button.setEnabled(False)
                opacity_effect = QGraphicsOpacityEffect(reset_button)
                opacity_effect.setOpacity(0.0)
                reset_button.setGraphicsEffect(opacity_effect)
                month_year_layout.addWidget(reset_button)

                # Stocker pour le reset (clé = premier combo, valeur = tuple des widgets)
                self._reset_buttons_map[month_combo] = (reset_button, opacity_effect, year_combo) # Stocker year_combo aussi

                # Connecter les signaux des DEUX combos au même slot de vérification
                date_change_slot = functools.partial(self._handle_dynamic_date_change, month_combo, year_combo)
                month_combo.currentTextChanged.connect(date_change_slot)
                year_combo.currentTextChanged.connect(date_change_slot)
                
                # Connecter le clic du bouton reset
                date_reset_slot = functools.partial(self._reset_dynamic_date, month_combo, year_combo)
                reset_button.clicked.connect(date_reset_slot)

                # Ajouter au layout principal
                new_form_layout.addRow(label, month_year_layout)
                self._current_dynamic_widgets.extend([label, month_combo, year_combo, reset_button])
                continue # Passer au champ suivant
            
            # --- GESTION DES AUTRES CHAMPS (LABEL, COMBO, LINEEDIT) --- 
            elif field_type == "combo":
                options = jacmar_data.get(field_name, [])
                widget = QComboBox()
                widget.setObjectName(f"dynamic_combo_{field_name}")
                widget.addItems(options if options else ["N/A"])
                initial_value = str(default_pref_value) if default_pref_value is not None else ""
                if initial_value:
                    widget.setCurrentText(initial_value)
                    # Vérifier si la valeur a été acceptée (elle pourrait ne pas être dans la liste)
                    if widget.currentText() != initial_value: 
                        print(f"WARN: Default value '{initial_value}' for '{field_name}' not found in options.")
                        initial_value = widget.currentText() # Utiliser la valeur actuelle comme initiale
            elif field_type == "lineedit": # Tous les autres cas deviennent des lineedit
                initial_value = str(default_pref_value if default_pref_value is not None else "")
                widget = QLineEdit()
                widget.setObjectName(f"dynamic_lineedit_{field_name}")
                widget.setText(initial_value)
            else: # Cas d'erreur si field_type était autre chose?
                print(f"WARN: Unhandled field type '{field_type}' for field '{field_name}'")
                widget = QLabel(f"Type de champ non géré: {field_type}")
                new_form_layout.addRow(label, widget)
                self._current_dynamic_widgets.extend([label, widget])
                continue

            # --- Le reste (bouton reset, layout H, connexion signaux) est commun --- 
            widget.setProperty("initial_value", initial_value)

            reset_button = QPushButton() 
            reset_button.setObjectName("DynamicResetButton")
            reset_icon = QIcon(RESET_ICON_PATH)
            if not reset_icon.isNull():
                reset_button.setIcon(reset_icon)
                reset_button.setIconSize(QSize(16, 16)) 
            else:
                print(f"WARN: Icône Reset non trouvée: {RESET_ICON_PATH}, utilisation texte.")
                reset_button.setText("↺") 
                reset_button.setFont(QFont("Arial", 10))
            reset_button.setFixedSize(20, 20) 
            reset_button.setToolTip(f"Réinitialiser {field_name} à sa valeur initiale")
            reset_button.setFlat(True) 
            reset_button.setFocusPolicy(Qt.NoFocus) 
            reset_button.setEnabled(False) 

            opacity_effect = QGraphicsOpacityEffect(reset_button)
            opacity_effect.setOpacity(0.0) 
            reset_button.setGraphicsEffect(opacity_effect)

            self._reset_buttons_map[widget] = (reset_button, opacity_effect)

            widget_layout = QHBoxLayout()
            widget_layout.setContentsMargins(0,0,0,0)
            widget_layout.setSpacing(5)
            widget_layout.addWidget(widget, 1)
            widget_layout.addWidget(reset_button)

            change_slot = functools.partial(self._handle_dynamic_field_change, widget)
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(change_slot)
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(change_slot)
            
            reset_slot = functools.partial(self._reset_dynamic_field, widget)
            reset_button.clicked.connect(reset_slot)
            
            new_form_layout.addRow(label, widget_layout)
            self._current_dynamic_widgets.extend([label, widget, reset_button])
            # --- FIN GESTION AUTRES CHAMPS ---
        # --- FIN MODIFICATION BOUCLE ---

        # 5. Appliquer et ajouter le layout
        self.dynamic_content_container.setLayout(new_form_layout)
        stretch_index = self.main_content_layout.count() - 1 
        self.main_content_layout.insertWidget(stretch_index, self.dynamic_content_container)
        print("DEBUG: Formulaire dynamique mis à jour.")

    # --- Méthodes pour gérer les boutons Reset (modifiées pour opacité/enable) --- 

    def _handle_dynamic_field_change(self, input_widget):
        """Gère l'opacité et l'état enabled du bouton reset."""
        print(f"DEBUG: _handle_dynamic_field_change called for widget: {input_widget.objectName()}") # DEBUG 1
        map_entry = self._reset_buttons_map.get(input_widget)
        print(f"DEBUG: Map entry found: {map_entry is not None}") # DEBUG 2
        if not map_entry:
            return
        reset_button, opacity_effect = map_entry

        initial_value = input_widget.property("initial_value")
        current_value = ""
        if isinstance(input_widget, QLineEdit):
            current_value = input_widget.text()
        elif isinstance(input_widget, QComboBox):
            current_value = input_widget.currentText()
        
        # --- DEBUG 3: Afficher les valeurs --- 
        print(f"    Initial Value: '{initial_value}' (Type: {type(initial_value)})")
        print(f"    Current Value: '{current_value}' (Type: {type(current_value)})")
        # -------------------------------------
        
        is_different = (str(current_value) != str(initial_value if initial_value is not None else ""))
        print(f"DEBUG: Is Different: {is_different}") # DEBUG 4
        
        # Mettre à jour l'opacité ET l'état enabled
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        reset_button.setEnabled(is_different)

    def _reset_dynamic_field(self, input_widget):
        """Réinitialise le champ, cache le bouton (opacité) et le désactive."""
        map_entry = self._reset_buttons_map.get(input_widget)
        if not map_entry:
            return
        reset_button, opacity_effect = map_entry
            
        initial_value = input_widget.property("initial_value")
        print(f"Resetting field {input_widget.objectName()} to '{initial_value}'")

        input_widget.blockSignals(True)
        try:
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(str(initial_value if initial_value is not None else ""))
            elif isinstance(input_widget, QComboBox):
                # Tenter de sélectionner par texte
                input_widget.setCurrentText(str(initial_value if initial_value is not None else ""))
                # Si la valeur n'existe plus, currentText ne changera pas forcément,
                # mais le bouton reset deviendra qd même invisible car is_different sera False.
        finally:
            input_widget.blockSignals(False)

        # Cacher (opacité) et désactiver le bouton après reset
        opacity_effect.setOpacity(0.0)
        reset_button.setEnabled(False)

    # --- NOUVELLES Méthodes pour gérer le Reset du champ DATE --- 
    def _handle_dynamic_date_change(self, month_combo, year_combo):
        """Gère l'opacité/état du bouton reset unique pour la date."""
        map_entry = self._reset_buttons_map.get(month_combo) # Récupérer via month_combo
        if not map_entry or len(map_entry) != 3: # Vérifier si c'est pour le champ date
            return
        reset_button, opacity_effect, _ = map_entry # Ignorer year_combo stocké ici

        initial_month = month_combo.property("initial_value")
        initial_year = year_combo.property("initial_value")
        current_month = month_combo.currentText()
        current_year = year_combo.currentText()

        month_changed = (str(current_month) != str(initial_month))
        year_changed = (str(current_year) != str(initial_year))
        is_different = month_changed or year_changed

        print(f"DEBUG Date Change: M:{current_month}({initial_month}) Y:{current_year}({initial_year}) Diff:{is_different}") # Debug
        opacity_effect.setOpacity(1.0 if is_different else 0.0)
        reset_button.setEnabled(is_different)

    def _reset_dynamic_date(self, month_combo, year_combo):
        """Réinitialise les combos mois/année et cache/désactive le bouton reset."""
        map_entry = self._reset_buttons_map.get(month_combo) # Récupérer via month_combo
        if not map_entry or len(map_entry) != 3:
            return
        reset_button, opacity_effect, _ = map_entry
        
        initial_month = month_combo.property("initial_value")
        initial_year = year_combo.property("initial_value")
        print(f"Resetting Date to Month: '{initial_month}', Year: '{initial_year}'")

        # Bloquer les signaux des DEUX combos
        month_combo.blockSignals(True)
        year_combo.blockSignals(True)
        try:
            month_combo.setCurrentText(str(initial_month))
            year_combo.setCurrentText(str(initial_year))
        finally:
            month_combo.blockSignals(False)
            year_combo.blockSignals(False)

        opacity_effect.setOpacity(0.0)
        reset_button.setEnabled(False)

    # --- NOUVELLE MÉTHODE: Récupérer les données du formulaire --- 
    def get_dynamic_form_data(self) -> dict:
        """Récupère les valeurs actuelles des widgets du formulaire dynamique."""
        form_data = {}
        for widget in self._current_dynamic_widgets:
            object_name = widget.objectName()
            
            if object_name.startswith("dynamic_lineedit_"):
                field_name = object_name.replace("dynamic_lineedit_", "")
                try:
                    form_data[field_name] = widget.text()
                except Exception as e:
                    print(f"Erreur lecture QLineEdit {field_name}: {e}")
                    form_data[field_name] = None # Ou valeur par défaut
            elif object_name.startswith("dynamic_combo_"):
                # Gérer la date séparément si besoin, ou combiner ici
                if object_name == "dynamic_combo_month":
                    # Combiner mois et année (si l'année existe)
                    year_widget = self.findChild(QComboBox, "dynamic_combo_year")
                    if year_widget:
                        month_text = widget.currentText()
                        year_text = year_widget.currentText()
                        # Convertir le nom du mois en numéro? Pour l'instant, garder texte.
                        form_data["date"] = f"{month_text}-{year_text}" 
                    else:
                         form_data["date"] = widget.currentText() # Juste le mois si erreur
                elif object_name == "dynamic_combo_year":
                    pass # Déjà traité avec le mois
                else:
                    # Autres combos
                    field_name = object_name.replace("dynamic_combo_", "")
                    try:
                        form_data[field_name] = widget.currentText()
                    except Exception as e:
                         print(f"Erreur lecture QComboBox {field_name}: {e}")
                         form_data[field_name] = None
            # Ignorer les autres types de widgets (QLabel, QPushButton, etc.)
            
        print(f"Données dynamiques récupérées par get_dynamic_form_data: {form_data}")
        return form_data
    # ---------------------------------------------------------

    @Slot(str)
    def update_theme_icons(self, theme_name):
        """Met à jour les icônes en fonction du thème."""
        print(f"DEBUG: DocumentsTypeSelectionPage updating theme icons for theme: {theme_name}")
        # Mettre à jour l'icône de l'en-tête
        if self.header_icon_label and self._header_icon_base_name:
            try:
                new_icon_path = icon_loader.get_icon_path(self._header_icon_base_name)
                new_pixmap = QPixmap(new_icon_path)
                if not new_pixmap.isNull():
                    self.header_icon_label.setPixmap(new_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    # print(f"DEBUG: Header icon updated to {new_icon_path}") # Optionnel
                else:
                    print(f"WARN: Header icon '{self._header_icon_base_name}' not found on theme update: {new_icon_path}")
                    self.header_icon_label.setText("?") # Fallback texte si icône non trouvée
            except Exception as e:
                print(f"ERROR updating header icon in DocumentsTypeSelectionPage: {e}")
                self.header_icon_label.setText("?") # Fallback texte en cas d'erreur
        # Ajouter ici la mise à jour d'autres icônes spécifiques à cette page si nécessaire 