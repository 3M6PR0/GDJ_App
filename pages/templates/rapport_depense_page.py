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
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0,0,0,0)
        right_column_layout.setSpacing(8)

        # Montant (Label affichage seulement)
        montant_label = QLabel("Montant:")
        # Remplacer QDoubleSpinBox par QLabel
        self.montant_display_label = QLabel("0.00 $") 
        self.montant_display_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter) # Aligner comme un champ
        self.montant_display_label.setStyleSheet("font-weight: bold;") # Le distinguer un peu
        # Optionnel: Donner un nom d'objet 
        # self.montant_display_label.setObjectName("MontantDisplayLabel")
        right_column_layout.addWidget(montant_label)
        right_column_layout.addWidget(self.montant_display_label) # Ajouter le QLabel

        right_column_layout.addStretch() # Pousse les boutons vers le bas

        # Boutons (créés et ajoutés en bas de la colonne droite)
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
        right_column_layout.addLayout(buttons_layout) # Ajouter les boutons au layout vertical droit
        
        form_details_layout.addWidget(right_column_widget) # Ajouter la colonne droite au HBox principal
        
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
        """ Met à jour le formulaire dynamique (partie gauche). """
        # Récupérer le conteneur du formulaire dynamique (partie gauche)
        parent_container = self.dynamic_form_container 
        
        # --- Nettoyage --- Supprimer l'ancien widget de formulaire dynamique s'il existe
        if self.dynamic_form_widget is not None:
            # Le widget est enfant de parent_container, pas besoin de removeWidget explicite?
            # Essayons sans removeWidget d'abord
            self.dynamic_form_widget.deleteLater()
            self.dynamic_form_widget = None
            self.dynamic_form_layout = None 
            self.form_fields = {} 

        # --- Créer le nouveau widget et layout (qui iront dans le conteneur gauche) --- 
        self.dynamic_form_widget = QWidget(parent_container) # Parent = conteneur gauche
        self.dynamic_form_widget.setStyleSheet("background-color: transparent;") 
        self.dynamic_form_layout = QGridLayout(self.dynamic_form_widget) 
        self.dynamic_form_layout.setHorizontalSpacing(15)
        self.dynamic_form_layout.setVerticalSpacing(8)
        self.dynamic_form_layout.setContentsMargins(0, 0, 0, 0) # Pas de marges internes ici

        # --- Ajouter le nouveau widget au layout du conteneur gauche ---
        # S'assurer que le conteneur gauche a un layout
        if parent_container.layout() is None:
            container_layout = QVBoxLayout(parent_container)
            container_layout.setContentsMargins(0,0,0,0)
            parent_container.setLayout(container_layout)
        parent_container.layout().addWidget(self.dynamic_form_widget)
        
        entry_type = self.entry_type_combo.currentText()
        self.form_fields = {} # Reset pour les nouveaux champs (hors montant)

        # --- Champs communs (SAUF Montant) ---
        row = 0
        # Date
        date_label = QLabel("Date:")
        self.form_fields['date'] = QDateEdit(QDate.currentDate())
        self.form_fields['date'].setCalendarPopup(True)
        self.dynamic_form_layout.addWidget(date_label, row, 0)
        self.dynamic_form_layout.addWidget(self.form_fields['date'], row, 1)
        
        # Montant - NE PAS AJOUTER ICI
        # montant_label = QLabel("Montant:")
        # ...
        # self.dynamic_form_layout.addWidget(montant_label, row, 2)
        # self.dynamic_form_layout.addWidget(self.form_fields['montant'], row, 3)

        row += 1
        # Description (occupe toute la ligne disponible à gauche)
        desc_label = QLabel("Description:")
        self.form_fields['description'] = QLineEdit()
        self.dynamic_form_layout.addWidget(desc_label, row, 0)
        # Étend seulement sur la colonne 1 (qui a un stretch factor)
        self.dynamic_form_layout.addWidget(self.form_fields['description'], row, 1, 1, 1)

        # --- Champs spécifiques --- (Logique de création inchangée, mais ajoutés au grid gauche)
        row += 1
        col = 0 
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
            
        for label_text, field_key, widget_instance, *config in specific_fields:
            label = QLabel(label_text)
            widget = widget_instance
            if config:
                props = config[0]
                if "range" in props: widget.setRange(*props["range"])
                if "suffix" in props: widget.setSuffix(props["suffix"])
                if "decimals" in props: widget.setDecimals(props["decimals"])
                if "alignment" in props: widget.setAlignment(props["alignment"])
            self.form_fields[field_key] = widget
            self.dynamic_form_layout.addWidget(label, row, col * 2) # Mettre dans colonne 0 ou 2
            self.dynamic_form_layout.addWidget(widget, row, col * 2 + 1) # Mettre dans colonne 1 ou 3
            col += 1
            if col >= 2: # Si on a mis deux paires
                col = 0
                row += 1
                
        # Stretch et spacers (appliqués au grid layout gauche)
        final_row = row if col == 0 else row + 1
        self.dynamic_form_layout.setRowStretch(final_row, 1)
        self.dynamic_form_layout.setColumnStretch(1, 1) # Donne plus de place à la colonne des champs
        # self.dynamic_form_layout.setColumnStretch(3, 1) # Plus nécessaire?
        # S'assurer qu'il n'y a que 2 colonnes utilisées pour les champs spécifiques
        # -> la logique précédente avec col*2 semble ok, mais on ajuste le stretch

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