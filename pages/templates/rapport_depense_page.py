from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                           QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QHBoxLayout, QMessageBox,
                           QGridLayout, QFrame, QCheckBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from ui.components.frame import Frame # Correction: Chemin d'importation correct
from models.documents.rapport_depense import RapportDepense, Deplacement, Repas, Depense # Importer les modèles

# Supposer qu'une classe RapportDepense existe dans vos modèles
# from models.documents.rapport_depense import RapportDepense

class RapportDepensePage(QWidget):
    def __init__(self, document: RapportDepense, parent=None):
        super().__init__(parent)
        self.setObjectName("RapportDepensePage")
        self.document = document # Garder une référence au modèle de données
        self.num_commande_repas_label = None
        self.num_commande_repas_field = None
        self.num_commande_container = None
        self.payeur_group = None # Pour groupe Payeur
        self.refacturer_group = None # Pour groupe Refacturer
        
        # --- Style pour les boutons radio spécifiques au formulaire --- 
        self.setStyleSheet("""
            QRadioButton#FormRadioButton {
                spacing: 5px; /* Espace entre indicateur et texte */
                color: #D0D0D0; /* Couleur du texte (exemple gris clair) - À AJUSTER */
            }
            QRadioButton#FormRadioButton::indicator {
                width: 16px; /* Taille légèrement plus grande */
                height: 16px;
            }
            QRadioButton#FormRadioButton::indicator::unchecked {
                /* Apparence quand non coché */
                border: 1px solid #555; /* Bordure grise foncée - À AJUSTER */
                background-color: #333; /* Fond gris très foncé - À AJUSTER */
                border-radius: 4px; /* Coins arrondis (carré) - Ajustez si besoin */
            }
            QRadioButton#FormRadioButton::indicator::checked {
                /* Apparence quand coché */
                border: 1px solid #1E88E5; /* Bordure bleue (exemple) - À AJUSTER */
                background-color: #1E88E5; /* Fond bleu - À AJUSTER */
                border-radius: 4px; /* Coins arrondis */
                /* Optionnel: petit point intérieur ou icône */
                /* image: url(:/icons/radio_checked.png); */ 
            }
            QRadioButton#FormRadioButton::indicator::checked::hover {
                border: 1px solid #42A5F5; /* Bleu plus clair au survol si coché - À AJUSTER */
                background-color: #42A5F5; /* À AJUSTER */
            }
            QRadioButton#FormRadioButton::indicator::unchecked::hover {
                border: 1px solid #777; /* Gris plus clair au survol si non coché - À AJUSTER */
            }
        """)
        # -------------------------------------------------------------

        self._setup_ui()
        # self._load_data() # Pas besoin avec le QLabel simple

    def _setup_ui(self):
        # Layout vertical principal pour la page
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(15, 15, 15, 15) 
        content_layout.setSpacing(15)

        # --- Section Supérieure : Ajout ET Totaux --- 
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15) 

        # --- Frame Gauche: Ajouter une Entrée ---
        # 1. Créer le contenu de l'en-tête (Label + ComboBox)
        header_layout = QHBoxLayout()
        header_label = QLabel("Ajouter un(e) :") 
        header_label.setObjectName("FormLabel") 
        header_layout.addWidget(header_label)
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.setObjectName("HeaderComboBox") 
        self.entry_type_combo.addItems(["Déplacement", "Repas", "Dépense"])
        self.entry_type_combo.currentIndexChanged.connect(self._update_entry_form)
        header_layout.addWidget(self.entry_type_combo, 1)
        header_container = QWidget()
        header_container.setObjectName("FrameHeaderContainer")
        header_container.setLayout(header_layout)

        # 2. Créer le Frame principal d'ajout
        self.add_entry_frame = Frame(header_widget=header_container, parent=self) 
        add_entry_content_layout = self.add_entry_frame.get_content_layout()
        add_entry_content_layout.setSpacing(8)
        # --- Retrait de l'ancienne structure directe --- 
        # add_entry_content_layout.addLayout(buttons_layout) <-- Fait plus bas
        # add_entry_content_layout.addWidget(self.dynamic_form_widget) <-- Fait via _update_entry_form

        # 3. Nouveau Layout principal pour le contenu du Frame d'ajout (Gauche: Form / Droite: Montant+Boutons)
        form_details_layout = QHBoxLayout()
        form_details_layout.setContentsMargins(0,0,0,0)
        form_details_layout.setSpacing(15) # Espacement entre formulaire et colonne droite
        add_entry_content_layout.addLayout(form_details_layout) # Ajouter ce HBox au layout du Frame

        # 3a. Placeholder Gauche pour le formulaire dynamique (le widget sera créé/ajouté dans _update_entry_form)
        # Note: On a besoin d'un layout parent pour ce widget
        self.dynamic_form_container = QWidget() # Widget qui contiendra le formulaire dynamique
        # Appliquer un fond transparent à ce conteneur aussi pour être sûr
        self.dynamic_form_container.setStyleSheet("background-color: transparent;")
        form_details_layout.addWidget(self.dynamic_form_container, 1) # Stretch factor 1 pour prendre plus de place
        self.dynamic_form_widget = None # Sera le QWidget AVEC le QGridLayout dedans
        self.dynamic_form_layout = None
        self.form_fields = {}
        # --- AJOUT --- 
        self.total_apres_taxes_field = None # Pour lier à montant_display_label

        # 3b. Colonne Droite (Label Montant + Boutons)
        right_column_widget = QWidget()
        # Rendre le fond de la colonne droite transparent
        right_column_widget.setStyleSheet("background-color: transparent;")
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0,0,0,0)
        right_column_layout.setSpacing(8)
        # Donner une largeur fixe à cette colonne
        right_column_widget.setFixedWidth(150) # Ajustez cette valeur si nécessaire

        # --- Retirer le stretch avant le label Montant ---
        # right_column_layout.addStretch(1) 
        
        # Montant (Label affichage seulement)
        montant_label = QLabel("Montant:")
        # Centrer le label horizontalement
        montant_label.setAlignment(Qt.AlignHCenter)
        right_column_layout.addWidget(montant_label)
        
        # --- Ajouter un stretch ENTRE le label et la valeur du montant ---
        right_column_layout.addStretch(1)
        
        # Remplacer QDoubleSpinBox par QLabel
        self.montant_display_label = QLabel("0.00 $") 
        # Centrer la valeur horizontalement et verticalement si possible
        self.montant_display_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter) 
        self.montant_display_label.setStyleSheet("font-weight: bold;") # Le distinguer un peu
        # Optionnel: Donner un nom d'objet 
        # self.montant_display_label.setObjectName("MontantDisplayLabel")
        right_column_layout.addWidget(self.montant_display_label) # Ajouter le QLabel

        # --- Conserver le stretch ENTRE le montant et les boutons pour pousser les boutons vers le bas --- 
        right_column_layout.addStretch(1)
        
        # Boutons (créés et ajoutés en bas de la colonne droite)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0,0,0,0)
        buttons_layout.setSpacing(6)
        self.clear_button = QPushButton("Effacer")
        self.add_button = QPushButton("Ajouter")
        # Appliquer le style via le nom d'objet correct
        self.clear_button.setObjectName("TopNavButton")
        self.add_button.setObjectName("TopNavButton")
        self.clear_button.clicked.connect(self._clear_entry_form)
        self.add_button.clicked.connect(self._add_entry)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.add_button)
        right_column_layout.addLayout(buttons_layout) # Ajouter les boutons au layout vertical droit
        
        # --- Retirer le stretch après les boutons --- 
        # right_column_layout.addStretch(1)

        # Ajuster les stretchs du HBox principal (formulaire vs colonne droite)
        form_details_layout.addWidget(self.dynamic_form_container, 1) # Formulaire dynamique, prend l'espace restant
        form_details_layout.addWidget(right_column_widget, 0) # Colonne droite, largeur fixe
        
        top_section_layout.addWidget(self.add_entry_frame, 1) # Ajouter le frame d'ajout (stretch = 1)

        # --- Frame Droite: Totaux ---
        self.totals_frame = Frame("Totaux", self)
        totals_content_layout = self.totals_frame.get_content_layout()
        
        # Utiliser un QFormLayout pour les totaux
        totals_form_layout = QFormLayout()
        totals_form_layout.setSpacing(8)
        totals_form_layout.setLabelAlignment(Qt.AlignRight)
        totals_content_layout.addLayout(totals_form_layout)

        # Labels Placeholder pour les totaux
        self.total_deplacements_label = QLabel("0.00 $")
        self.total_repas_label = QLabel("0.00 $")
        self.total_depenses_label = QLabel("0.00 $")
        self.total_general_label = QLabel("0.00 $")
        self.total_general_label.setStyleSheet("font-weight: bold;") # Mettre le total général en gras
        
        totals_form_layout.addRow("Déplacements:", self.total_deplacements_label)
        totals_form_layout.addRow("Repas:", self.total_repas_label)
        totals_form_layout.addRow("Dépenses diverses:", self.total_depenses_label)
        # Ajouter un séparateur avant le total général
        separator = QFrame() # Utiliser QFrame standard ici
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        totals_form_layout.addRow(separator)
        totals_form_layout.addRow("Total Général:", self.total_general_label)
        
        totals_content_layout.addStretch() # Pousser les totaux vers le haut

        # Ajuster la largeur du frame des totaux (optionnel)
        self.totals_frame.setFixedWidth(250) # Ou utiliser setMinimumWidth

        top_section_layout.addWidget(self.totals_frame) # Ajouter le frame des totaux
        
        # Ajouter la section supérieure (Ajout + Totaux) au layout principal
        content_layout.addLayout(top_section_layout)

        # --- Section Inférieure: Affichage des Entrées --- 
        self.entries_display_frame = Frame("Entrées existantes", self) 
        self.entries_display_layout = self.entries_display_frame.get_content_layout()
        placeholder_label = QLabel("Affichage des entrées à implémenter ici (ex: QTableWidget).")
        self.entries_display_layout.addWidget(placeholder_label)
        content_layout.addWidget(self.entries_display_frame)
        # Donner plus de poids vertical au frame des entrées
        content_layout.setStretchFactor(self.entries_display_frame, 1) 

        # Initialiser le formulaire pour le premier type
        self._update_entry_form()

    def _update_entry_form(self):
        """ Met à jour le formulaire dynamique (partie gauche) selon le type d'entrée. """
        # --- Réinitialiser la référence --- 
        self.total_apres_taxes_field = None
        self.num_commande_repas_label = None
        self.num_commande_repas_field = None
        self.num_commande_container = None
        self.payeur_group = None # Réinitialiser
        self.refacturer_group = None # Réinitialiser
        parent_container = self.dynamic_form_container
        if self.dynamic_form_widget is not None:
            self.dynamic_form_widget.deleteLater()
            self.dynamic_form_widget = None
            self.dynamic_form_layout = None 
            self.form_fields = {} 
        self.dynamic_form_widget = QWidget(parent_container)
        self.dynamic_form_widget.setStyleSheet("background-color: transparent;") 
        self.dynamic_form_layout = QGridLayout(self.dynamic_form_widget) 
        self.dynamic_form_layout.setHorizontalSpacing(15)
        self.dynamic_form_layout.setVerticalSpacing(8)
        self.dynamic_form_layout.setContentsMargins(0, 0, 0, 0) 
        if parent_container.layout() is None:
            container_layout = QVBoxLayout(parent_container)
            container_layout.setContentsMargins(0,0,0,0)
            parent_container.setLayout(container_layout)
        old_layout = parent_container.layout()
        if old_layout.count() > 0:
             old_widget = old_layout.takeAt(0).widget()
             if old_widget and old_widget != self.dynamic_form_widget: 
                 old_widget.deleteLater()
        parent_container.layout().addWidget(self.dynamic_form_widget)
        entry_type = self.entry_type_combo.currentText()
        self.form_fields = {} 
        max_grid_row_used = -1 # Pour suivre la dernière ligne utilisée

        # --- Champs communs (toujours présents) --- 
        # Date (col 0)
        date_label = QLabel("Date:")
        self.form_fields['date'] = QDateEdit(QDate.currentDate())
        # --- Appliquer un style pour ressembler à QLineEdit --- 
        self.form_fields['date'].setStyleSheet("""
            QDateEdit {
                border: 1px solid #555; /* Correspondance avec RadioButton unchecked */
                padding: 2px 5px; /* Ajuster le padding comme un QLineEdit */
                background-color: #333; /* Fond comme RadioButton unchecked */
                /* border-radius: 4px; */ /* Optionnel: coins arrondis */
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #555;
                border-left-style: solid; 
                /* border-top-right-radius: 3px; */ /* Optionnel */
                /* border-bottom-right-radius: 3px; */ /* Optionnel */
            }
            QDateEdit::down-arrow {
                /* Vous pouvez utiliser une image ou un caractère unicode ici */
                /* image: url(path/to/your/arrow.png); */
                /* Ou laisser le défaut */
            }
        """)
        # ------------------------------------------------------
        self.form_fields['date'].setCalendarPopup(True)
        self.dynamic_form_layout.addWidget(date_label, 0, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], 0, 1)
        max_grid_row_used = max(max_grid_row_used, 0)
        
        # --- Champs spécifiques par type --- 
        if entry_type == "Déplacement":
            # Colonne 1 (suite)
            client_label = QLabel("Client:")
            self.form_fields['client'] = QLineEdit()
            self.dynamic_form_layout.addWidget(client_label, 1, 0) # Décalé à la ligne 1
            self.dynamic_form_layout.addWidget(self.form_fields['client'], 1, 1) # Décalé à la ligne 1
            # max_grid_row_used est à 0 (Date), devient 1 ici
            max_grid_row_used = max(max_grid_row_used, 1) 

            # Colonne 2 (Indices 2, 3)
            ville_label = QLabel("Ville:")
            self.form_fields['ville'] = QLineEdit()
            self.dynamic_form_layout.addWidget(ville_label, 0, 2)
            self.dynamic_form_layout.addWidget(self.form_fields['ville'], 0, 3)
            
            num_commande_label = QLabel("N° Commande:")
            self.form_fields['numero_commande'] = QLineEdit()
            self.dynamic_form_layout.addWidget(num_commande_label, 1, 2)
            self.dynamic_form_layout.addWidget(self.form_fields['numero_commande'], 1, 3)

            kilometrage_label = QLabel("Kilométrage:")
            self.form_fields['kilometrage'] = QDoubleSpinBox()
            self.form_fields['kilometrage'].setRange(0.0, 9999.9)
            self.form_fields['kilometrage'].setSuffix(" km")
            self.form_fields['kilometrage'].setAlignment(Qt.AlignRight)
            self.dynamic_form_layout.addWidget(kilometrage_label, 2, 2)
            self.dynamic_form_layout.addWidget(self.form_fields['kilometrage'], 2, 3)
            # max_grid_row_used est déjà à 2
            max_grid_row_used = max(max_grid_row_used, 2) # Assurer que max_grid_row_used prend en compte la colonne 2
            
            # Stretch colonnes pour Déplacement
            self.dynamic_form_layout.setColumnStretch(1, 1) # Widget Col 1
            self.dynamic_form_layout.setColumnStretch(3, 1) # Widget Col 2
            self.dynamic_form_layout.setColumnStretch(0, 0) # Label Col 1
            self.dynamic_form_layout.setColumnStretch(2, 0) # Label Col 2

        elif entry_type == "Repas":
            # --- Colonne 1 (Indices 0, 1) --- 
            # Date et Description sont déjà là (lignes 0, 1)
            
            # --- Restaurant et Client sur la Ligne 1 ---
            restaurant_label = QLabel("Restaurant:") 
            self.dynamic_form_layout.addWidget(restaurant_label, 1, 0) # Label en (1, 0)
            
            resto_client_hbox = QHBoxLayout()
            resto_client_hbox.setContentsMargins(0,0,0,0)
            resto_client_hbox.setSpacing(5)
            
            self.form_fields['restaurant'] = QLineEdit()
            resto_client_hbox.addWidget(self.form_fields['restaurant'], 1) # Stretch 1
            
            resto_client_hbox.addSpacing(10)
            
            client_repas_label_inline = QLabel("Client:")
            self.form_fields['client_repas'] = QLineEdit()
            resto_client_hbox.addWidget(client_repas_label_inline)
            resto_client_hbox.addWidget(self.form_fields['client_repas'], 1) # Stretch 1
            
            self.dynamic_form_layout.addLayout(resto_client_hbox, 1, 1) # HBox en (1, 1)
            # ----------------------------------------------
            
            # --- Remplacement CheckBox par RadioButton pour Payeur --- 
            payeur_label = QLabel("Payeur:")
            payeur_grid_layout = QGridLayout() # UTILISER UN GRID ICI
            self.payeur_group = QButtonGroup(self) # Créer le groupe
            payeur_grid_layout.setContentsMargins(0,0,0,0)
            payeur_grid_layout.setSpacing(10) # Espacement comme Refacturer
            self.form_fields['payeur_employe'] = QRadioButton("Employé")
            self.form_fields['payeur_employe'].setObjectName("FormRadioButton")
            self.form_fields['payeur_jacmar'] = QRadioButton("Jacmar")
            self.form_fields['payeur_jacmar'].setObjectName("FormRadioButton")
            self.form_fields['payeur_employe'].setChecked(True) # Défaut Employé
            self.payeur_group.addButton(self.form_fields['payeur_employe']) # Ajouter au groupe
            self.payeur_group.addButton(self.form_fields['payeur_jacmar']) # Ajouter au groupe
            # Placer les boutons dans le grid
            payeur_grid_layout.addWidget(self.form_fields['payeur_employe'], 0, 0) # Ligne 0, Col 0
            payeur_grid_layout.addWidget(self.form_fields['payeur_jacmar'], 0, 1)  # Ligne 0, Col 1

            # Définir les stretchs des colonnes (1:1:2)
            payeur_grid_layout.setColumnStretch(0, 1)
            payeur_grid_layout.setColumnStretch(1, 1)
            payeur_grid_layout.setColumnStretch(2, 2) # Laisser la colonne 2 vide mais stretchée

            self.dynamic_form_layout.addWidget(payeur_label, 2, 0)
            self.dynamic_form_layout.addLayout(payeur_grid_layout, 2, 1) # Ajouter le GRID
            # ---------------------------------------------------------
            
            # --- Remplacement CheckBox par RadioButton pour Refacturer ---
            refacturer_label = QLabel("Refacturer:")
            refacturer_grid_layout = QGridLayout() # UTILISER UN GRID ICI
            refacturer_grid_layout.setContentsMargins(0, 0, 0, 0)
            refacturer_grid_layout.setSpacing(10) # Espacement entre colonnes

            self.refacturer_group = QButtonGroup(self) # Le groupe est toujours utile

            self.form_fields['refacturer_non'] = QRadioButton("Non")
            self.form_fields['refacturer_non'].setObjectName("FormRadioButton")
            self.form_fields['refacturer_oui'] = QRadioButton("Oui")
            self.form_fields['refacturer_oui'].setObjectName("FormRadioButton")
            self.refacturer_group.addButton(self.form_fields['refacturer_non']) # Ajouter au groupe
            self.refacturer_group.addButton(self.form_fields['refacturer_oui']) # Ajouter au groupe
            self.form_fields['refacturer_non'].setChecked(True) # Défaut Non

            # --- Connecter le signal du bouton 'Oui' --- 
            self.form_fields['refacturer_oui'].toggled.connect(self._toggle_num_commande_visibility)
            # -------------------------------------------

            # Placer les widgets dans le grid
            refacturer_grid_layout.addWidget(self.form_fields['refacturer_non'], 0, 0) # Ligne 0, Col 0
            refacturer_grid_layout.addWidget(self.form_fields['refacturer_oui'], 0, 1) # Ligne 0, Col 1

            # --- Créer le CONTENEUR et son layout INTERNE (QVBox) pour la colonne 2 ---
            self.num_commande_container = QWidget() 
            num_commande_cell_layout = QHBoxLayout()
            num_commande_cell_layout.setContentsMargins(0, 0, 0, 0)
            num_commande_cell_layout.setSpacing(2) # Petit espace entre label et field

            self.num_commande_repas_label = QLabel("N° Commande:")
            self.num_commande_repas_field = QLineEdit()
            self.form_fields['numero_commande_repas'] = self.num_commande_repas_field
            num_commande_cell_layout.addWidget(self.num_commande_repas_label)
            num_commande_cell_layout.addWidget(self.num_commande_repas_field)
            num_commande_cell_layout.addStretch(1) # Retirer le stretch vertical
            self.num_commande_container.setLayout(num_commande_cell_layout) # Appliquer le layout au conteneur

            # Ajouter le CONTENEUR à la grille
            refacturer_grid_layout.addWidget(self.num_commande_container, 0, 2) # Ligne 0, Col 2

            # Définir les stretchs des colonnes du grid pour largeur égale
            refacturer_grid_layout.setColumnStretch(0, 1)
            refacturer_grid_layout.setColumnStretch(1, 1)
            refacturer_grid_layout.setColumnStretch(2, 2) # Donner un poids de 2 à la 3ème colonne
            
            # --- Définir la visibilité initiale de N° Commande --- 
            self._toggle_num_commande_visibility(self.form_fields['refacturer_oui'].isChecked())
            # -----------------------------------------------------

            self.dynamic_form_layout.addWidget(refacturer_label, 3, 0)
            self.dynamic_form_layout.addLayout(refacturer_grid_layout, 3, 1) # Ajouter le GRID au layout principal
            # ----------------------------------------------------------

            # La ligne max utilisée pour la colonne de gauche est maintenant 3
            max_grid_row_used = max(max_grid_row_used, 3)
            
            # --- Colonne 2 (Indices 2, 3) --- 
            # Fonction utilitaire pour les champs montant simples
            def add_montant_field(label_text, field_key, row):
                label = QLabel(label_text)
                widget = QLineEdit("0.00") # Valeur initiale
                # Appliquer un validateur pour nombres décimaux
                validator = QDoubleValidator(0.0, 99999.99, 2) # Min, Max, Décimales
                validator.setNotation(QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
                # ----------------------------------------------
                widget.setAlignment(Qt.AlignRight)
                # widget.setButtonSymbols(QDoubleSpinBox.NoButtons) # N'est plus pertinent
                self.form_fields[field_key] = widget
                self.dynamic_form_layout.addWidget(label, row, 2) # Label en col 2
                self.dynamic_form_layout.addWidget(widget, row, 3) # Widget en col 3
                return widget # Retourne le widget créé
            
            # --- Total avant Tx et Pourboire sur la même ligne (Ligne 0, Cols 2 et 3) --- 
            total_avtx_label = QLabel("Total avant Tx:")
            self.dynamic_form_layout.addWidget(total_avtx_label, 0, 2) # Label en (0, 2)

            montants_hbox = QHBoxLayout()
            montants_hbox.setContentsMargins(0,0,0,0)
            montants_hbox.setSpacing(5)

            # Champ Total avant Tx
            total_avtx_widget = QLineEdit("0.00")
            validator_avtx = QDoubleValidator(0.0, 99999.99, 2)
            validator_avtx.setNotation(QDoubleValidator.StandardNotation)
            total_avtx_widget.setValidator(validator_avtx)
            total_avtx_widget.setAlignment(Qt.AlignRight)
            self.form_fields['total_avant_taxes'] = total_avtx_widget
            montants_hbox.addWidget(total_avtx_widget, 1) # Stretch 1

            montants_hbox.addSpacing(10) # Espace entre les deux champs

            # Label et Champ Pourboire
            pourboire_label = QLabel("Pourboire:")
            pourboire_widget = QLineEdit("0.00")
            validator_pb = QDoubleValidator(0.0, 99999.99, 2)
            validator_pb.setNotation(QDoubleValidator.StandardNotation)
            pourboire_widget.setValidator(validator_pb)
            pourboire_widget.setAlignment(Qt.AlignRight)
            self.form_fields['pourboire'] = pourboire_widget
            montants_hbox.addWidget(pourboire_label) # Pas de stretch pour le label
            montants_hbox.addWidget(pourboire_widget, 1) # Stretch 1 pour le champ

            # Ajouter le HBox à la grille
            self.dynamic_form_layout.addLayout(montants_hbox, 0, 3) # HBox en (0, 3)
            # -------------------------------------------------------------------------
            
            # --- Taxes: Label principal + Labels/Champs groupés horizontalement --- 
            tax_start_row = 1 # Taxes à la ligne 1
            tax_labels = ["TPS:", "TVQ:", "TVH:"]
            tax_field_keys = ['tps', 'tvq', 'tvh']
            
            # Ajouter le label principal "Taxe:" dans la colonne des labels
            main_tax_label = QLabel("Taxe:")
            self.dynamic_form_layout.addWidget(main_tax_label, tax_start_row, 2) # Ligne 1, Col 2 (Label)
            
            # Layout horizontal pour les labels et champs de taxe QLineEdit
            taxes_layout = QHBoxLayout()
            taxes_layout.setContentsMargins(0,0,0,0)
            taxes_layout.setSpacing(5) # Espacement entre les éléments
            
            for i, key in enumerate(tax_field_keys):
                # Ajouter le petit label (sans ':') DANS le layout horizontal
                small_label = QLabel(tax_labels[i].replace(':',''))
                taxes_layout.addWidget(small_label)
                
                # Créer le QLineEdit et l'ajouter au layout horizontal APRÈS son petit label
                widget = QLineEdit("0.00")
                validator = QDoubleValidator(0.0, 99999.99, 2)
                validator.setNotation(QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
                widget.setAlignment(Qt.AlignRight)
                # widget.setPlaceholderText(tax_labels[i].replace(':','')) # Placeholder moins utile maintenant
                self.form_fields[key] = widget
                # Ajouter le widget avec un facteur d'étirement pour qu'il prenne l'espace
                taxes_layout.addWidget(widget, 1) 
                
                # Ajouter un petit espace si ce n'est pas le dernier
                if i < len(tax_field_keys) - 1:
                    taxes_layout.addSpacing(10)
                
            # Ajouter le layout horizontal des champs à la grille, en l'étendant sur 3 lignes
            # Ajouter le layout horizontal (labels+champs) à la grille sur UNE seule ligne
            self.dynamic_form_layout.addLayout(taxes_layout, tax_start_row, 3) # Ligne 1, Col 3 
            # ---------------------------
            
            # --- Ajuster la ligne pour Total après Tx --- 
            # Le total est maintenant sur la ligne suivant la ligne des taxes
            total_ap_tx_row = tax_start_row + 1 
            self.total_apres_taxes_field = add_montant_field("Total après Tx:", 'total_apres_taxes', total_ap_tx_row) # add_montant_field gère label col 2, widget col 3
            # Lier la valeur de ce champ au label de la colonne droite (Montant)
            self.total_apres_taxes_field.textChanged.connect(self._update_montant_display)
            max_grid_row_used = max(max_grid_row_used, total_ap_tx_row) # Mettre à jour la ligne max utilisée
            
            # Stretch colonnes pour Repas
            self.dynamic_form_layout.setColumnStretch(0, 0) # Label Col 1
            self.dynamic_form_layout.setColumnStretch(2, 0) # Label Col 2
            self.dynamic_form_layout.setColumnStretch(1, 1) # Widget Col 1
            self.dynamic_form_layout.setColumnStretch(3, 1) # Widget Col 2
            
        elif entry_type == "Dépense":
             # Pour Dépense, on n'ajoute que le champ Montant (remplacé par le label à droite)
             # Donc, seuls Date et Description sont affichés dans la grille.
             self.dynamic_form_layout.setColumnStretch(1, 1) # Widget Col 1
             self.dynamic_form_layout.setColumnStretch(0, 0) # Label Col 1
             # S'assurer que les autres colonnes n'ont pas de stretch
             self.dynamic_form_layout.setColumnStretch(2, 0)
             self.dynamic_form_layout.setColumnStretch(3, 0)
             pass # Rien de plus à ajouter spécifiquement pour Dépense simple ici
                
        # Ajuster le stretch de la ligne APRÈS la dernière ligne utilisée
        self.dynamic_form_layout.setRowStretch(max_grid_row_used + 1, 1)

    def _update_montant_display(self, value):
        """ Met à jour le label montant dans la colonne de droite. """
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
            # --- Lire depuis le QLineEdit et convertir --- 
            try:
                # Remplacer la virgule par un point si nécessaire pour float()
                numeric_value = float(str(value).replace(',', '.'))
                self.montant_display_label.setText(f"{numeric_value:.2f} $")
            except ValueError:
                # Si la valeur n'est pas un nombre valide (ex: vide ou '-'), afficher 0.00
                self.montant_display_label.setText("0.00 $")
            # -------------------------------------------

    def _clear_entry_form(self):
        """ Efface les champs du formulaire actuel (gauche ET reset le label montant). """
        # Effacer les champs du formulaire dynamique (gauche)
        for field_key, widget in self.form_fields.items():
            if isinstance(widget, QLineEdit):
                # --- Pour les champs monétaires, mettre "0.00" --- 
                if widget.validator() and isinstance(widget.validator(), QDoubleValidator):
                    widget.setText("0.00")
                else:
                    widget.clear() # Pour les autres QLineEdit
                # ----------------------------------------------
            elif isinstance(widget, QDoubleSpinBox):
                # Si c'est le champ total_apres_taxes, sa valeur sera reset par valueChanged(0) - Obsolète
                # Les autres spinbox prennent leur minimum (souvent 0)
                widget.setValue(widget.minimum()) 
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            # --- AJOUT POUR CHECKBOX --- 
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            # --- AJOUT POUR RADIOBUTTON --- 
            # Vérifier les clés spécifiques pour remettre les défauts
            elif field_key == 'payeur_employe':
                widget.setChecked(True)
            elif field_key == 'payeur_jacmar':
                widget.setChecked(False)
            elif field_key == 'refacturer_non':
                widget.setChecked(True)
            elif field_key == 'refacturer_oui':
                widget.setChecked(False)
            # ------------------------------

        # Réinitialiser le label montant dédié (droite)
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
             self.montant_display_label.setText("0.00 $")

    def _add_entry(self):
        """ Ajoute l'entrée en lisant les champs du formulaire. """
        entry_type = self.entry_type_combo.currentText()
        
        try:
            # Récupérer les valeurs communes (Date et Description)
            date_val = self.form_fields['date'].date().toPyDate()

            new_entry = None
            if entry_type == "Déplacement":
                 client_val = self.form_fields['client'].text()
                 ville_val = self.form_fields['ville'].text()
                 num_commande_val = self.form_fields['numero_commande'].text()
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 # --- Calcul du montant pour Déplacement --- 
                 TAUX_KM = 0.50 # Exemple de taux - À METTRE DANS CONFIG
                 montant_deplacement = kilometrage_val * TAUX_KM
                 self._update_montant_display(montant_deplacement) # Met à jour l'affichage
                 # -----------------------------------------
                 new_entry = Deplacement(date_deplacement=date_val, 
                                         client=client_val, ville=ville_val, 
                                         numero_commande=num_commande_val,
                                         kilometrage=kilometrage_val, 
                                         montant=montant_deplacement)
                 # self.document n'a plus add_deplacement, etc. Il faut une méthode générique?
                 # Supposons qu'il y a une liste entries: self.document.entries.append(new_entry)
                 print(f"Ajout Déplacement: {new_entry}") # Placeholder

            elif entry_type == "Repas":
                 # Récupérer les valeurs spécifiques depuis self.form_fields
                 restaurant_val = self.form_fields['restaurant'].text()
                 client_repas_val = self.form_fields['client_repas'].text()
                 # --- Lire l'état des RadioButtons --- 
                 payeur_val = self.form_fields['payeur_employe'].isChecked()
                 refacturer_val = self.form_fields['refacturer_oui'].isChecked()
                 # ------------------------------------
                 num_commande_repas_val = self.form_fields['numero_commande_repas'].text()
                 # --- Lire et convertir les QLineEdit monétaires --- 
                 def get_float_from_field(key):
                     try:
                         # Remplacer la virgule par un point si nécessaire
                         return float(self.form_fields[key].text().replace(',', '.'))
                     except (KeyError, ValueError):
                         # Si clé non trouvée ou conversion impossible, retourner 0.0
                         return 0.0
                 
                 total_avant_taxes_val = get_float_from_field('total_avant_taxes')
                 pourboire_val = get_float_from_field('pourboire')
                 tps_val = get_float_from_field('tps')
                 tvq_val = get_float_from_field('tvq')
                 tvh_val = get_float_from_field('tvh')
                 total_apres_taxes_val = get_float_from_field('total_apres_taxes')
                 # ---------------------------------------------------
                 # --- Ajout: Lire employe/jacmar s'ils existent, sinon 0 --- 
                 employe_val = get_float_from_field('employe') # TODO: Ajouter champ si nécessaire
                 jacmar_val = get_float_from_field('jacmar') # TODO: Ajouter champ si nécessaire

                 # Validation spécifique Repas
                 if not restaurant_val:
                     QMessageBox.warning(self, "Champ manquant", "Le nom du restaurant est requis.")
                     return
                 if total_apres_taxes_val <= 0:
                      QMessageBox.warning(self, "Montant invalide", "Le total après taxes doit être positif.")
                      return
                 
                 new_entry = Repas(date_repas=date_val, description="", # Passer une description vide
                                    restaurant=restaurant_val, client=client_repas_val,
                                    payeur=payeur_val, refacturer=refacturer_val,
                                    numero_commande=num_commande_repas_val,
                                    totale_avant_taxes=total_avant_taxes_val, 
                                    pourboire=pourboire_val, tps=tps_val, tvq=tvq_val, tvh=tvh_val,
                                    totale_apres_taxes=total_apres_taxes_val,
                                    employe=employe_val, jacmar=jacmar_val, 
                                    facture=None) # Facture non gérée ici
                 # self.document.entries.append(new_entry)
                 print(f"Ajout Repas: {new_entry}") # Placeholder
                 
            elif entry_type == "Dépense":
                 # --- Dépense simple : On lit le montant depuis le display label? --- 
                 # C'est problématique, il faudrait un champ dédié si on veut une dépense simple
                 # Pour l'instant, on ne peut pas l'ajouter car il n'y a pas de champ montant
                 QMessageBox.warning(self, "Type non géré", "L\'ajout de 'Dépense simple' nécessite un champ Montant.")
                 return
                 # montant_val = float(self.montant_display_label.text().replace(' $','')) # Risqué
                 # new_entry = Depense(date=date_val, description=description_val, montant=montant_val)
                 # self.document.entries.append(new_entry)
                 # print(f"Ajout Dépense: {new_entry}") # Placeholder

            if new_entry: # Si une entrée a été créée
                print(f"Entrée ajoutée: {new_entry}") # Répétitif
                self._clear_entry_form() 
                # self._update_entries_display() # TODO: Mettre à jour la liste/tableau
                self._update_totals_display() # TODO: Mettre à jour les totaux
                QMessageBox.information(self, "Succès", f"{entry_type} ajouté avec succès.")

        except KeyError as e:
             # Gérer le cas où un champ attendu n'existe pas dans self.form_fields
             QMessageBox.critical(self, "Erreur Interne", f"Erreur de clé de formulaire: {e}. Le formulaire pour '{entry_type}' est peut-être incomplet.")
        except Exception as e:
             QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'entrée: {e}")
             traceback.print_exc() # Pour débogage

    # --- Méthode pour mettre à jour l'affichage des totaux (à implémenter) ---
    def _update_totals_display(self):
         # TODO: Lire self.document.get_totals() ou équivalent et mettre à jour les labels
         pass 

    # --- Méthode pour mettre à jour l'affichage des entrées (à implémenter) ---
    # def _update_entries_display(self):
    #     pass 

    # --- AJOUT: Méthode pour gérer la visibilité de N° Commande --- 
    def _toggle_num_commande_visibility(self, checked):
        """ Affiche ou cache le label et le champ N° Commande selon l'état du bouton 'Oui'. """
        print(f"_toggle_num_commande_visibility appelé avec checked={checked}") # DEBUG
        # Agir sur le conteneur
        if hasattr(self, 'num_commande_container') and self.num_commande_container:
            self.num_commande_container.setVisible(checked)
            print(f"  num_commande_container.setVisible({checked}) effectué. visible={self.num_commande_container.isVisible()}") # DEBUG
            # Retrait de adjustSize()
        else:
            print("  Erreur: self.num_commande_container non trouvé ou None.") # DEBUG
    # -------------------------------------------------------------

# Bloc de test simple
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Simuler un objet document
    class MockRapportDepense:
        def __init__(self):
            self.nom_rapport = "Rapport Test"
            self.titre = "Déjeuner Client X"
            self.montant_total = 123.45
            
    app = QApplication(sys.argv)
    doc = MockRapportDepense()
    page = RapportDepensePage(document=doc)
    page.setWindowTitle("Test RapportDepensePage (Simplifié)")
    page.resize(400, 300)
    page.show()
    sys.exit(app.exec_()) 