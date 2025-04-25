from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                           QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, 
                           QPushButton, QHBoxLayout, QMessageBox)
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Section En-tête (Infos du Rapport) ---
        # Pourrait être enrichi plus tard pour afficher nom, date, etc.
        header_label = QLabel(f"Rapport: {self.document.title}")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_layout.addWidget(header_label)

        # --- Section Ajouter une Entrée ---

        # 1. Créer le ComboBox D'ABORD
        self.entry_type_combo = QComboBox()
        self.entry_type_combo.addItems(["Déplacement", "Repas", "Dépense"])
        self.entry_type_combo.currentIndexChanged.connect(self._update_entry_form)

        # 2. Créer le Frame en passant le ComboBox comme header_widget
        add_entry_frame = Frame(header_widget=self.entry_type_combo, parent=self)
        add_entry_content_layout = add_entry_frame.get_content_layout() 
        add_entry_content_layout.setSpacing(8) # Réduire l'espacement vertical

        # --- Ligne pour les boutons (sous l'en-tête/ComboBox) ---
        buttons_layout = QHBoxLayout() # Renommé pour clarté
        buttons_layout.setContentsMargins(0,0,0,0)
        buttons_layout.setSpacing(6)
        
        # 3. Ne plus ajouter le ComboBox ici
        # top_controls_layout.addWidget(self.entry_type_combo)

        buttons_layout.addStretch() # Pousser les boutons vers la droite

        # Boutons "Effacer" et "Ajouter"
        self.clear_button = QPushButton("Effacer")
        self.add_button = QPushButton("Ajouter")
        self.clear_button.clicked.connect(self._clear_entry_form)
        self.add_button.clicked.connect(self._add_entry)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.add_button)
        
        # Ajouter la ligne des boutons au layout du contenu
        add_entry_content_layout.addLayout(buttons_layout)

        # --- Formulaire dynamique (en dessous des boutons) ---
        self.dynamic_form_widget = QWidget()
        self.dynamic_form_layout = QFormLayout(self.dynamic_form_widget)
        self.dynamic_form_layout.setContentsMargins(0, 0, 0, 0) 
        add_entry_content_layout.addWidget(self.dynamic_form_widget)

        # --- Ajouter le Frame au layout principal ---
        main_layout.addWidget(add_entry_frame)

        # --- Section Affichage des Entrées (à ajouter plus tard) ---
        # Placeholder pour une table ou liste
        entries_label = QLabel("Entrées existantes (à implémenter)")
        main_layout.addWidget(entries_label)

        main_layout.addStretch() # Pour pousser les éléments vers le haut

        # Initialiser le formulaire pour le premier type
        self._update_entry_form()

    def _update_entry_form(self):
        """ Met à jour le formulaire en fonction du type d'entrée sélectionné. """
        # Supprimer les anciens widgets du layout dynamique
        while self.dynamic_form_layout.count():
            item = self.dynamic_form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        entry_type = self.entry_type_combo.currentText()
        self.form_fields = {} # Dictionnaire pour stocker les widgets du formulaire

        # Champs communs
        self.form_fields['date'] = QDateEdit(QDate.currentDate())
        self.form_fields['date'].setCalendarPopup(True)
        self.dynamic_form_layout.addRow("Date:", self.form_fields['date'])
        
        self.form_fields['description'] = QLineEdit()
        self.dynamic_form_layout.addRow("Description:", self.form_fields['description'])

        self.form_fields['montant'] = QDoubleSpinBox()
        self.form_fields['montant'].setRange(0.0, 99999.99)
        self.form_fields['montant'].setSuffix(" $")
        self.dynamic_form_layout.addRow("Montant:", self.form_fields['montant'])

        # Champs spécifiques
        if entry_type == "Déplacement":
            self.form_fields['kilometrage'] = QDoubleSpinBox()
            self.form_fields['kilometrage'].setRange(0.0, 9999.9)
            self.form_fields['kilometrage'].setSuffix(" km")
            self.dynamic_form_layout.addRow("Kilométrage:", self.form_fields['kilometrage'])
            
            self.form_fields['vehicule'] = QLineEdit()
            self.dynamic_form_layout.addRow("Véhicule:", self.form_fields['vehicule'])

            self.form_fields['depart'] = QLineEdit()
            self.dynamic_form_layout.addRow("Lieu Départ:", self.form_fields['depart'])
            
            self.form_fields['arrivee'] = QLineEdit()
            self.dynamic_form_layout.addRow("Lieu Arrivée:", self.form_fields['arrivee'])

        elif entry_type == "Repas":
            self.form_fields['nombre_convives'] = QDoubleSpinBox() # Utiliser QSpinBox si entier est suffisant
            self.form_fields['nombre_convives'].setRange(1, 100)
            self.form_fields['nombre_convives'].setDecimals(0) # Pour un entier
            self.dynamic_form_layout.addRow("Nombre convives:", self.form_fields['nombre_convives'])

            self.form_fields['nom_convives'] = QLineEdit()
            self.dynamic_form_layout.addRow("Noms convives:", self.form_fields['nom_convives'])
            
            self.form_fields['etablissement'] = QLineEdit()
            self.dynamic_form_layout.addRow("Établissement:", self.form_fields['etablissement'])

        elif entry_type == "Dépense":
            # Pas de champs spécifiques pour le modèle Depense de base pour l'instant
            # On pourrait ajouter 'categorie' ou autre plus tard
            pass

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
                 # Récupérer les valeurs spécifiques au déplacement
                 kilometrage_val = self.form_fields['kilometrage'].value()
                 vehicule_val = self.form_fields['vehicule'].text()
                 depart_val = self.form_fields['depart'].text()
                 arrivee_val = self.form_fields['arrivee'].text()
                 
                 new_entry = Deplacement(date=date_val, description=description_val, montant=montant_val,
                                         kilometrage=kilometrage_val, vehicule=vehicule_val, 
                                         lieu_depart=depart_val, lieu_arrivee=arrivee_val)
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