from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                           QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QHBoxLayout, QMessageBox,
                           QGridLayout, QFrame)
from PyQt5.QtCore import Qt, QDate
from ui.components.frame import Frame # Correction: Chemin d'importation correct
from models.documents.rapport_depense import RapportDepense, Deplacement, Repas, Depense # Importer les modèles

# Supposer qu'une classe RapportDepense existe dans vos modèles
# from models.documents.rapport_depense import RapportDepense

class RapportDepensePage(QWidget):
    def __init__(self, document: RapportDepense, parent=None):
        super().__init__(parent)
        self.setObjectName("RapportDepensePage")
        self.document = document # Garder une référence au modèle de données
        
        self._setup_ui()
        # self._load_data() # Pas besoin avec le QLabel simple

    def _setup_ui(self):
        # Layout vertical principal pour la page
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(15, 15, 15, 15) 
        content_layout.setSpacing(15)

        # --- Section Supérieure : Ajout ET Totaux --- 
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15) # Espacement entre les frames Ajout et Totaux

        # --- Frame Gauche: Ajouter une Entrée ---
        # 1. Créer le ComboBox D'ABORD
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.addItems(["Déplacement", "Repas", "Dépense"])
        self.entry_type_combo.currentIndexChanged.connect(self._update_entry_form)

        # 2. Créer le Frame en passant le ComboBox comme header_widget
        self.add_entry_frame = Frame(header_widget=self.entry_type_combo, parent=self) 
        add_entry_content_layout = self.add_entry_frame.get_content_layout()
        add_entry_content_layout.setSpacing(8)

        # --- Ligne pour les boutons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0,0,0,0)
        buttons_layout.setSpacing(6)
        buttons_layout.addStretch()
        self.clear_button = QPushButton("Effacer")
        self.add_button = QPushButton("Ajouter")
        self.clear_button.clicked.connect(self._clear_entry_form)
        self.add_button.clicked.connect(self._add_entry)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.add_button)
        add_entry_content_layout.addLayout(buttons_layout)

        # --- Formulaire dynamique (créé dans _update_entry_form) ---
        self.dynamic_form_widget = None
        self.dynamic_form_layout = None
        self.form_fields = {}
        # Le widget sera ajouté au `add_entry_content_layout` dans `_update_entry_form`
        
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
        """ Met à jour le formulaire en fonction du type d'entrée sélectionné, en utilisant QGridLayout. """
        # Récupérer le layout parent où ajouter le widget du formulaire
        parent_layout = self.add_entry_frame.get_content_layout()
        
        # --- Nettoyage radical : Supprimer l'ancien widget de formulaire s'il existe ---
        if self.dynamic_form_widget is not None:
            # Retirer l'ancien widget du layout parent
            parent_layout.removeWidget(self.dynamic_form_widget)
            # Supprimer le widget et ses enfants (y compris l'ancien layout)
            self.dynamic_form_widget.deleteLater()
            self.dynamic_form_widget = None
            self.dynamic_form_layout = None # Reset layout reference
            self.form_fields = {} # Reset fields reference

        # --- Créer le nouveau widget et layout --- 
        self.dynamic_form_widget = QWidget()
        # Appliquer un fond transparent au widget contenant le formulaire
        self.dynamic_form_widget.setStyleSheet("background-color: transparent;") 
        self.dynamic_form_layout = QGridLayout(self.dynamic_form_widget) # Appliquer le layout AU NOUVEAU WIDGET
        self.dynamic_form_layout.setHorizontalSpacing(15)
        self.dynamic_form_layout.setVerticalSpacing(8)
        self.dynamic_form_layout.setContentsMargins(0, 5, 0, 5) 

        # --- Ajouter le nouveau widget de formulaire au layout parent ---
        # Insérer APRÈS le layout des boutons. Le layout des boutons est à l'index 0 maintenant.
        parent_layout.insertWidget(1, self.dynamic_form_widget)
        
        entry_type = self.entry_type_combo.currentText()
        self.form_fields = {} 

        # --- Champs communs ---
        row = 0
        # Date
        date_label = QLabel("Date:")
        self.form_fields['date'] = QDateEdit(QDate.currentDate())
        self.form_fields['date'].setCalendarPopup(True)
        self.dynamic_form_layout.addWidget(date_label, row, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], row, 1)
        
        # Montant
        montant_label = QLabel("Montant:")
        self.form_fields['montant'] = QDoubleSpinBox()
        self.form_fields['montant'].setRange(0.0, 99999.99)
        self.form_fields['montant'].setSuffix(" $")
        self.form_fields['montant'].setAlignment(Qt.AlignRight) # Aligner à droite
        self.dynamic_form_layout.addWidget(montant_label, row, 2)
        self.dynamic_form_layout.addWidget(self.form_fields['montant'], row, 3)

        row += 1
        # Description (occupe toute la ligne)
        desc_label = QLabel("Description:")
        self.form_fields['description'] = QLineEdit()
        self.dynamic_form_layout.addWidget(desc_label, row, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['description'], row, 1, 1, 3) # Étend sur 3 colonnes

        # --- Champs spécifiques ---
        row += 1
        col = 0 # Reset column for specific fields
        
        specific_fields = []
        if entry_type == "Déplacement":
            specific_fields = [
                ("Client:", 'client', QLineEdit()),
                ("Ville:", 'ville', QLineEdit()),
                ("N° Commande:", 'numero_commande', QLineEdit()),
                ("Kilométrage:", 'kilometrage', QDoubleSpinBox(), {"range": (0.0, 9999.9), "suffix": " km", "alignment": Qt.AlignRight}),
            ]
        elif entry_type == "Repas":
            specific_fields = [
                ("Nombre convives:", 'nombre_convives', QDoubleSpinBox(), {"range": (1, 100), "decimals": 0, "alignment": Qt.AlignRight}),
                ("Noms convives:", 'nom_convives', QLineEdit()),
                ("Établissement:", 'etablissement', QLineEdit()),
            ]
        # elif entry_type == "Dépense": -> pas de champs spécifiques
            
        for label_text, field_key, widget_instance, *config in specific_fields:
            label = QLabel(label_text)
            widget = widget_instance
            
            # Appliquer la configuration si fournie
            if config:
                props = config[0]
                if "range" in props: widget.setRange(*props["range"])
                if "suffix" in props: widget.setSuffix(props["suffix"])
                if "decimals" in props: widget.setDecimals(props["decimals"])
                if "alignment" in props: widget.setAlignment(props["alignment"])
                
            self.form_fields[field_key] = widget
            
            self.dynamic_form_layout.addWidget(label, row, col)
            self.dynamic_form_layout.addWidget(widget, row, col + 1)
            
            col += 2 # Passer aux deux prochaines colonnes
            if col >= 4: # Si on a rempli la ligne (2 paires de champs)
                col = 0
                row += 1
                
        # Ajouter un spacer vertical à la fin pour pousser les champs vers le haut
        # Vérifier si la dernière ligne utilisée était complète ou non
        final_row = row if col == 0 else row + 1
        self.dynamic_form_layout.setRowStretch(final_row, 1)
        # Ajuster le stretch de colonne pour donner plus de place aux champs qu'aux labels
        self.dynamic_form_layout.setColumnStretch(1, 1)
        self.dynamic_form_layout.setColumnStretch(3, 1)

    def _clear_entry_form(self):
        """ Efface les champs du formulaire actuel. """
        for widget in self.form_fields.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(widget.minimum()) # Remettre à la valeur minimale (souvent 0)
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            # Ajouter d'autres types de widgets si nécessaire

    def _add_entry(self):
        """ Ajoute l'entrée (Déplacement, Repas, Dépense) au document. """
        entry_type = self.entry_type_combo.currentText()
        
        try:
            # Récupérer les valeurs communes
            date_val = self.form_fields['date'].date().toPyDate() # Convertir QDate en date
            description_val = self.form_fields['description'].text()
            montant_val = self.form_fields['montant'].value()

            if not description_val:
                QMessageBox.warning(self, "Champ manquant", "La description est requise.")
                return
            if montant_val <= 0:
                 QMessageBox.warning(self, "Montant invalide", "Le montant doit être positif.")
                 return

            new_entry = None
            if entry_type == "Déplacement":
                 # Récupérer les valeurs spécifiques CORRIGÉES
                 client_val = self.form_fields['client'].text()
                 ville_val = self.form_fields['ville'].text()
                 num_commande_val = self.form_fields['numero_commande'].text()
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 
                 new_entry = Deplacement(date_deplacement=date_val, 
                                         client=client_val,
                                         ville=ville_val,
                                         numero_commande=num_commande_val,
                                         kilometrage=kilometrage_val, 
                                         montant=montant_val)
                 self.document.add_deplacement(new_entry)

            elif entry_type == "Repas":
                 # Récupérer les valeurs spécifiques au repas
                 nb_convives_val = int(self.form_fields['nombre_convives'].value()) # Assurer entier
                 noms_convives_val = self.form_fields['nom_convives'].text()
                 etablissement_val = self.form_fields['etablissement'].text()

                 new_entry = Repas(date=date_val, description=description_val, montant=montant_val,
                                   nombre_convives=nb_convives_val, nom_convives=noms_convives_val, 
                                   nom_etablissement=etablissement_val)
                 self.document.add_repas(new_entry)
                 
            elif entry_type == "Dépense":
                 new_entry = Depense(date=date_val, description=description_val, montant=montant_val)
                 self.document.add_depense(new_entry)

            if new_entry:
                print(f"Entrée ajoutée: {new_entry}") # Pour débogage
                self._clear_entry_form()
                # Mettre à jour l'affichage des entrées (à faire)
                # self._update_entries_display() 
                QMessageBox.information(self, "Succès", f"{entry_type} ajouté avec succès.")

        except KeyError as e:
             QMessageBox.critical(self, "Erreur", f"Erreur interne: Champ de formulaire manquant {e}")
        except Exception as e:
             QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'entrée: {e}")

    # --- Méthode pour mettre à jour l'affichage des entrées (à implémenter) ---
    # def _update_entries_display(self):
    #     pass 

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