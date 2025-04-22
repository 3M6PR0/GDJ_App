# pages/documents/documents_type_selection_page.py # <- Nouveau nom
# Permet à l'utilisateur de choisir le type de nouveau document à créer.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFormLayout, 
    QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.components.frame import Frame

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
        self._setup_ui()

    def _setup_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10) 
        page_layout.setSpacing(10) 

        # --- Créer le contenu de l'en-tête --- 
        header_layout = QHBoxLayout()
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

    def update_content_area(self, fields_data: dict):
        """Nettoie l'ancien conteneur et repeuple avec un nouveau formulaire transparent."""
        # 1. Supprimer l'ancien conteneur
        if self.dynamic_content_container is not None:
            print("DEBUG: Suppression de l'ancien dynamic_content_container")
            # Retirer du layout parent
            self.main_content_layout.removeWidget(self.dynamic_content_container)
            # Marquer pour suppression
            self.dynamic_content_container.deleteLater()
            self.dynamic_content_container = None
        self._current_dynamic_widgets = []
        
        # 2. Créer le nouveau conteneur dynamique transparent
        self.dynamic_content_container = QWidget()
        self.dynamic_content_container.setStyleSheet("background-color: transparent;")
        
        # 3. Si pas de données, ajouter conteneur vide et sortir
        if not fields_data:
            print("Aucun champ à afficher. Ajout conteneur vide transparent.")
            # Insérer avant le stretch
            stretch_index = self.main_content_layout.count() - 1
            self.main_content_layout.insertWidget(stretch_index, self.dynamic_content_container)
            return

        # 4. Créer et peupler le nouveau formulaire
        print(f"Affichage des champs: {list(fields_data.keys())}")
        new_form_layout = QFormLayout()
        new_form_layout.setSpacing(10)
        new_form_layout.setVerticalSpacing(12)

        for field_name, field_info in fields_data.items():
            field_type = field_info.get("type", "combo") # Type de widget demandé
            label_text = field_name.replace('_', ' ').replace("departements", "département").capitalize() + ":"
            label = QLabel(label_text)
            label.setObjectName("FormLabel")
            
            widget = None
            default_value = field_info.get("default") # Récupérer la valeur par défaut si fournie
            
            if field_type == "label":
                value = field_info.get("value", "")
                widget = QLabel(str(value))
                widget.setObjectName(f"dynamic_label_{field_name}")
                widget.setWordWrap(True)
            elif field_type == "combo":
                options = field_info.get("options", [])
                widget = QComboBox()
                widget.setObjectName(f"dynamic_combo_{field_name}")
                widget.addItems(options if options else ["N/A"])
                # --- Préselectionner la valeur par défaut --- 
                if default_value is not None:
                    print(f"    -> Tentative sélection '{default_value}' pour {field_name}")
                    widget.setCurrentText(str(default_value)) # Utiliser setCurrentText
                    # Vérifier si la sélection a réussi (si la valeur existait dans les options)
                    if widget.currentText() != str(default_value):
                        print(f"    -> WARN: '{default_value}' non trouvé dans les options de {field_name}")
            elif field_type == "lineedit":
                # Utiliser la valeur fournie par le contrôleur (qui inclut déjà le défaut)
                initial_value = field_info.get("value", "") 
                widget = QLineEdit()
                widget.setObjectName(f"dynamic_lineedit_{field_name}")
                widget.setText(str(initial_value))
            else:
                widget = QLabel(f"Type de champ inconnu: {field_type}")

            if widget:
                new_form_layout.addRow(label, widget)
                self._current_dynamic_widgets.extend([label, widget])

        # 5. Appliquer le layout au conteneur transparent
        self.dynamic_content_container.setLayout(new_form_layout)
        
        # 6. Ajouter le conteneur au layout principal
        stretch_index = self.main_content_layout.count() - 1 
        self.main_content_layout.insertWidget(stretch_index, self.dynamic_content_container)
        print("DEBUG: Nouveau dynamic_content_container transparent ajouté.")

    # --- Récupérer les valeurs du formulaire dynamique (Maintenant important!) ---
    def get_dynamic_form_data(self):
        data = {}
        layout = self.dynamic_content_container.layout()
        if layout:
            for i in range(layout.rowCount()): # Itérer sur les lignes du QFormLayout
                label_item = layout.itemAt(i, QFormLayout.LabelRole)
                widget_item = layout.itemAt(i, QFormLayout.FieldRole)
                
                if label_item and widget_item:
                    label_widget = label_item.widget()
                    field_widget = widget_item.widget()
                    
                    if label_widget and field_widget:
                        # Récupérer le nom original du champ (moins idéal, basé sur le label)
                        field_name = label_widget.text().replace(':', '').replace(' ', '_').lower()
                        # Cas spécial pour département
                        if "département" in field_name:
                             field_name = "departements" 
                        elif "plafond_de_déplacement" in field_name:
                             field_name = "plafond_deplacement"
                        elif "nom" == field_name:
                             field_name = "nom" # garder minuscule
                        elif "prénom" == field_name:
                             field_name = "prenom"
                             
                        # Obtenir la valeur selon le type de widget
                        if isinstance(field_widget, QComboBox):
                            data[field_name] = field_widget.currentText()
                        elif isinstance(field_widget, QLineEdit):
                            data[field_name] = field_widget.text()
                        # Ajouter d'autres types si nécessaire
        print(f"Données dynamiques récupérées: {data}")
        return data 