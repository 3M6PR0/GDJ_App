from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout
)

class ProfilePage(QWidget):
    def __init__(self, profile, parent=None):
        """
        :param profile: Instance de Profile (déjà chargée depuis le fichier JSON)
        """
        super().__init__(parent)
        self.profile = profile
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # SECTION RENSEIGNEMENT
        renseignement_group = QGroupBox("Section Renseignement")
        renseignement_layout = QFormLayout()

        self.input_nom = QLineEdit()
        self.input_prenom = QLineEdit()
        self.input_telephone = QLineEdit()
        self.input_courriel = QLineEdit()
        self.combo_departement = QComboBox()
        self.combo_emplacement = QComboBox()
        self.combo_superviseur = QComboBox()
        self.combo_plafond = QComboBox()

        # Remplissage d'exemple des combobox
        self.combo_departement.addItems(["Finance", "Informatique", "Marketing"])
        self.combo_emplacement.addItems(["Paris", "Lyon", "Marseille"])
        self.combo_superviseur.addItems(["Dupont", "Durand", "Martin"])
        self.combo_plafond.addItems(["100€", "200€", "500€"])

        renseignement_layout.addRow("Nom :", self.input_nom)
        renseignement_layout.addRow("Prénom :", self.input_prenom)
        renseignement_layout.addRow("Téléphone :", self.input_telephone)
        renseignement_layout.addRow("Courriel :", self.input_courriel)
        renseignement_layout.addRow("Département :", self.combo_departement)
        renseignement_layout.addRow("Emplacement :", self.combo_emplacement)
        renseignement_layout.addRow("Superviseur :", self.combo_superviseur)
        renseignement_layout.addRow("Plafond de déplacement :", self.combo_plafond)

        renseignement_group.setLayout(renseignement_layout)
        main_layout.addWidget(renseignement_group)

        # SECTION PREFERENCES
        preferences_group = QGroupBox("Section Préférences")
        preferences_layout = QFormLayout()
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Clair", "Sombre"])
        preferences_layout.addRow("Theme :", self.combo_theme)
        preferences_group.setLayout(preferences_layout)
        main_layout.addWidget(preferences_group)

        # Boutons en bas
        button_layout = QHBoxLayout()
        self.btn_reinitialiser = QPushButton("Réinitialiser")
        self.btn_sauvegarder = QPushButton("Sauvegarder")
        button_layout.addWidget(self.btn_reinitialiser)
        button_layout.addWidget(self.btn_sauvegarder)
        main_layout.addLayout(button_layout)

        # Remplir le formulaire avec les données existantes
        self.load_profile_data()

        # Connexions
        self.btn_reinitialiser.clicked.connect(self.reset_fields)
        self.btn_sauvegarder.clicked.connect(self.save_profile)

    def load_profile_data(self):
        """Remplit le formulaire avec les informations de l'objet profil."""
        self.input_nom.setText(self.profile.nom)
        self.input_prenom.setText(self.profile.prenom)
        self.input_telephone.setText(self.profile.telephone)
        self.input_courriel.setText(self.profile.courriel)
        # Pour les combobox, on essaie de sélectionner l'élément correspondant
        index_dep = self.combo_departement.findText(self.profile.departement)
        if index_dep >= 0:
            self.combo_departement.setCurrentIndex(index_dep)
        index_emp = self.combo_emplacement.findText(self.profile.emplacement)
        if index_emp >= 0:
            self.combo_emplacement.setCurrentIndex(index_emp)
        index_sup = self.combo_superviseur.findText(self.profile.superviseur)
        if index_sup >= 0:
            self.combo_superviseur.setCurrentIndex(index_sup)
        index_plaf = self.combo_plafond.findText(self.profile.plafond)
        if index_plaf >= 0:
            self.combo_plafond.setCurrentIndex(index_plaf)
        index_theme = self.combo_theme.findText(self.profile.theme)
        if index_theme >= 0:
            self.combo_theme.setCurrentIndex(index_theme)

    def reset_fields(self):
        """Réinitialise tous les champs aux valeurs par défaut."""
        self.input_nom.clear()
        self.input_prenom.clear()
        self.input_telephone.clear()
        self.input_courriel.clear()
        self.combo_departement.setCurrentIndex(0)
        self.combo_emplacement.setCurrentIndex(0)
        self.combo_superviseur.setCurrentIndex(0)
        self.combo_plafond.setCurrentIndex(0)
        self.combo_theme.setCurrentIndex(0)

    def save_profile(self):
        """
        Met à jour l'objet profil avec les données du formulaire
        et sauvegarde dans le fichier JSON.
        """
        self.profile.nom = self.input_nom.text()
        self.profile.prenom = self.input_prenom.text()
        self.profile.telephone = self.input_telephone.text()
        self.profile.courriel = self.input_courriel.text()
        self.profile.departement = self.combo_departement.currentText()
        self.profile.emplacement = self.combo_emplacement.currentText()
        self.profile.superviseur = self.combo_superviseur.currentText()
        self.profile.plafond = self.combo_plafond.currentText()
        self.profile.theme = self.combo_theme.currentText()
        self.profile.save_to_file()
        print("Profil sauvegardé :", self.profile.to_dict())
