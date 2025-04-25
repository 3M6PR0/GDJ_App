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
        self.form_fields['date'].setCalendarPopup(True)
        self.dynamic_form_layout.addWidget(date_label, 0, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], 0, 1)
        max_grid_row_used = max(max_grid_row_used, 0)
        
        # Description (col 0)
        desc_label = QLabel("Description:")
        self.form_fields['description'] = QLineEdit()
        self.dynamic_form_layout.addWidget(desc_label, 1, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['description'], 1, 1)
        max_grid_row_used = max(max_grid_row_used, 1)

        # --- Champs spécifiques par type --- 
        if entry_type == "Déplacement":
            # Colonne 1 (suite)
            client_label = QLabel("Client:")
            self.form_fields['client'] = QLineEdit()
            self.dynamic_form_layout.addWidget(client_label, 2, 0)
            self.dynamic_form_layout.addWidget(self.form_fields['client'], 2, 1)
            max_grid_row_used = max(max_grid_row_used, 2)

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
            
            # Stretch colonnes pour Déplacement
            self.dynamic_form_layout.setColumnStretch(1, 1) # Widget Col 1
            self.dynamic_form_layout.setColumnStretch(3, 1) # Widget Col 2
            self.dynamic_form_layout.setColumnStretch(0, 0) # Label Col 1
            self.dynamic_form_layout.setColumnStretch(2, 0) # Label Col 2

        elif entry_type == "Repas":
            # Garder la logique dynamique pour Repas (ou autre type si nécessaire)
            specific_fields = [
                ("Nombre convives:", 'nombre_convives', QDoubleSpinBox(), {"range": (1, 100), "decimals": 0, "alignment": Qt.AlignRight}),
                ("Noms convives:", 'nom_convives', QLineEdit()), 
                ("Établissement:", 'etablissement', QLineEdit())
            ]
            fields_per_col = 3 # Ou ajustez si vous voulez changer pour repas
            start_row_specifics = max_grid_row_used + 1 # Commence après Description
            num_cols_used = 0
            current_max_row_specifics = start_row_specifics - 1

            for i, (label_text, field_key, widget_instance, *config) in enumerate(specific_fields):
                col_idx = i // fields_per_col
                row_in_col = i % fields_per_col
                num_cols_used = max(num_cols_used, col_idx + 1)
                grid_row = start_row_specifics + row_in_col
                grid_col_label = col_idx * 2
                grid_col_widget = grid_col_label + 1
                current_max_row_specifics = max(current_max_row_specifics, grid_row)

                label = QLabel(label_text)
                widget = widget_instance
                if config:
                    props = config[0]
                    if "range" in props: widget.setRange(*props["range"])
                    if "suffix" in props: widget.setSuffix(props["suffix"])
                    if "decimals" in props: widget.setDecimals(props["decimals"])
                    if "alignment" in props: widget.setAlignment(props["alignment"])
                self.form_fields[field_key] = widget
                self.dynamic_form_layout.addWidget(label, grid_row, grid_col_label)
                self.dynamic_form_layout.addWidget(widget, grid_row, grid_col_widget)
            
            max_grid_row_used = max(max_grid_row_used, current_max_row_specifics)
            # Ajuster le stretch des colonnes utilisées pour Repas
            grid_cols_total = num_cols_used * 2
            for c in range(grid_cols_total):
                 if c % 2 == 1: self.dynamic_form_layout.setColumnStretch(c, 1)
                 else: self.dynamic_form_layout.setColumnStretch(c, 0)
        
        # Pour 'Dépense', rien de plus à ajouter
        # ...
                
        # Ajuster le stretch de la ligne APRÈS la dernière ligne utilisée
        self.dynamic_form_layout.setRowStretch(max_grid_row_used + 1, 1)

    def _clear_entry_form(self):
        """ Efface les champs du formulaire actuel (gauche ET reset le label montant). """
        # Effacer les champs du formulaire dynamique (gauche)
        for field_key, widget in self.form_fields.items():
            # Exclure 'montant' car il n'est plus ici
            if field_key == 'montant': continue 
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(widget.minimum()) 
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
        # Réinitialiser le label montant dédié (droite)
        if hasattr(self, 'montant_display_label') and self.montant_display_label:
             self.montant_display_label.setText("0.00 $")

    def _add_entry(self):
        """ Ajoute l'entrée en lisant les champs de gauche ET en calculant/récupérant le montant. """
        entry_type = self.entry_type_combo.currentText()
        
        try:
            # Récupérer les valeurs communes (Description et Date depuis self.form_fields)
            date_val = self.form_fields['date'].date().toPyDate() 
            description_val = self.form_fields['description'].text()
            
            # --- !!! Logique de calcul du montant à définir ici !!! ---
            montant_val = 0.0 # VALEUR TEMPORAIRE
            # Exemple possible pour déplacement (nécessite un taux défini):
            # if entry_type == "Déplacement":
            #     TAUX_KM = 0.50 # Exemple de taux
            #     kilometrage_val = self.form_fields.get('kilometrage', QDoubleSpinBox()).value() # Lire le kilométrage
            #     montant_val = kilometrage_val * TAUX_KM
            #     # Mettre à jour le label affiché?
            #     self.montant_display_label.setText(f"{montant_val:.2f} $")
            # Pour Repas/Depense, comment calculer montant_val ?
            # ----------------------------------------------------------
            
            if not description_val:
                QMessageBox.warning(self, "Champ manquant", "La description est requise.")
                return
            # La validation montant_val <= 0 est toujours pertinente si le calcul peut donner 0 ou négatif
            # if montant_val <= 0: 
            #      QMessageBox.warning(self, "Montant calculé invalide", "Le montant calculé doit être positif.")
            #      return

            new_entry = None
            if entry_type == "Déplacement":
                 # Récupérer les valeurs spécifiques depuis self.form_fields
                 client_val = self.form_fields['client'].text()
                 ville_val = self.form_fields['ville'].text()
                 num_commande_val = self.form_fields['numero_commande'].text()
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 # Créer l'objet avec date_val, montant_val (calculé) et les spécifiques
                 new_entry = Deplacement(date_deplacement=date_val, 
                                         client=client_val, ville=ville_val, 
                                         numero_commande=num_commande_val,
                                         kilometrage=kilometrage_val, montant=montant_val)
                 self.document.add_deplacement(new_entry)

            elif entry_type == "Repas":
                 # Récupérer les valeurs spécifiques depuis self.form_fields
                 nb_convives_val = int(self.form_fields['nombre_convives'].value())
                 noms_convives_val = self.form_fields['nom_convives'].text()
                 etablissement_val = self.form_fields['etablissement'].text()
                 # Créer l'objet avec date_val, description_val, montant_val (calculé) et les spécifiques
                 new_entry = Repas(date=date_val, description=description_val, montant=montant_val,
                                   nombre_convives=nb_convives_val, nom_convives=noms_convives_val, 
                                   nom_etablissement=etablissement_val)
                 self.document.add_repas(new_entry)
                 
            elif entry_type == "Dépense":
                 # Créer l'objet avec date_val, description_val, montant_val (calculé)
                 new_entry = Depense(date=date_val, description=description_val, montant=montant_val)
                 self.document.add_depense(new_entry)

            if new_entry:
                print(f"Entrée ajoutée: {new_entry}")
                self._clear_entry_form() # Doit maintenant effacer aussi le montant à droite
                # self._update_entries_display() 
                QMessageBox.information(self, "Succès", f"{entry_type} ajouté avec succès.")

        except KeyError as e:
             # Gérer le cas où le champ montant dédié n'existerait pas (ne devrait pas arriver)
             if 'montant' not in str(e) and hasattr(self, 'montant_display_label') and self.montant_display_label is None:
                  QMessageBox.critical(self, "Erreur", "Erreur interne: Champ montant non initialisé.")
             else:
                  QMessageBox.critical(self, "Erreur", f"Erreur interne: Champ manquant {e}")
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