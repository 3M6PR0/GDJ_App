from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout
)
from utils.config_loader import load_config_data
from models.profile import Profile  # Pour recharger le profil depuis le JSON

class ProfilePage(QWidget):
    def __init__(self, profile, parent=None):
        """
        :param profile: Instance de la classe Profile déjà chargée (models/profile.py)
        """
        super().__init__(parent)
        self.profile = profile
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Charger les données de configuration depuis config_data.json
        config_data = load_config_data()
        profile_config = config_data.get("profile", {})

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

        # Peupler les combobox avec les valeurs du fichier config_data.json
        self.combo_departement.addItems(profile_config.get("departements", []))
        self.combo_emplacement.addItems(profile_config.get("emplacements", []))
        self.combo_superviseur.addItems(profile_config.get("superviseurs", []))
        plafond_data = profile_config.get("plafond_deplacement", [])
        if plafond_data and isinstance(plafond_data, list) and isinstance(plafond_data[0], dict):
            plafond_list = list(plafond_data[0].keys())
            self.combo_plafond.addItems(plafond_list)
        else:
            self.combo_plafond.addItems([])

        renseignement_layout.addRow("Nom :", self.input_nom)
        renseignement_layout.addRow("Prénom :", self.input_prenom)
        renseignement_layout.addRow("Téléphone :", self.input_telephone)
        renseignement_layout.addRow("Courriel :", self.input_courriel)
        renseignement_layout.addRow("Département :", self.combo_departement)
        renseignement_layout.addRow("Emplacement :", self.combo_emplacement)
        renseignement_layout.addRow("Superviseur :", self.combo_superviseur)
        renseignement_layout.addRow("Plafond de déplacement :", self.combo_plafond)
        renseignement_group.setLayout(renseignements_layout := renseignement_layout)
        main_layout.addWidget(renseignement_group)

        # SECTION PREFERENCES
        preferences_group = QGroupBox("Section Préférences")
        preferences_layout = QFormLayout()
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(profile_config.get("themes", []))
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

        # Remplir le formulaire avec les données existantes du profil
        self.load_profile_data()

        # Connexions
        self.btn_reinitialiser.clicked.connect(self.reset_fields)
        self.btn_sauvegarder.clicked.connect(self.save_profile)

    def load_profile_data(self):
        """Charge les données du profil dans tous les champs du formulaire."""
        # Pour les QLineEdit
        self.input_nom.setText(self.profile.nom)
        self.input_prenom.setText(self.profile.prenom)
        self.input_telephone.setText(self.profile.telephone)
        self.input_courriel.setText(self.profile.courriel)

        # Pour les combobox, on tente de trouver l'index correspondant à la valeur sauvegardée ;
        # si elle n'est pas trouvée, on met l'index 0 par défaut.
        index_dep = self.combo_departement.findText(self.profile.departement)
        self.combo_departement.setCurrentIndex(index_dep if index_dep >= 0 else 0)

        index_emp = self.combo_emplacement.findText(self.profile.emplacement)
        self.combo_emplacement.setCurrentIndex(index_emp if index_emp >= 0 else 0)

        index_sup = self.combo_superviseur.findText(self.profile.superviseur)
        self.combo_superviseur.setCurrentIndex(index_sup if index_sup >= 0 else 0)

        index_plaf = self.combo_plafond.findText(self.profile.plafond)
        self.combo_plafond.setCurrentIndex(index_plaf if index_plaf >= 0 else 0)

        index_theme = self.combo_theme.findText(self.profile.theme)
        self.combo_theme.setCurrentIndex(index_theme if index_theme >= 0 else 0)

    def reset_fields(self):
        """
        Recharge le profil depuis le fichier JSON pour annuler les modifications non sauvegardées
        et met à jour le formulaire.
        """
        self.profile = Profile.load_from_file()  # Recharge l'objet Profile depuis le fichier JSON
        self.load_profile_data()

    def save_profile(self):
        """Mets à jour l'objet profil avec les données du formulaire et sauvegarde dans le JSON."""
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
