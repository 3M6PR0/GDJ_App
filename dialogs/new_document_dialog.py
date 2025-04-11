from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QStackedWidget, QWidget,
    QFormLayout, QLineEdit, QDialogButtonBox
)


class NewDocumentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau Document")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Sélection du type de document
        layout.addWidget(QLabel("Sélectionnez le type de document :"))
        self.combo = QComboBox()
        document_types = [
            "Rapport Dépense",
            "Écriture Comptable",
            "Rapport Temps Sup",
            "CSA",
            "Système Vision",
            "Robot"
        ]
        self.combo.addItems(document_types)
        layout.addWidget(self.combo)

        # Zone d'information évolutive via un QStackedWidget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Formulaire pour Rapport Dépense
        self.form_rapport = QWidget()
        form_rapport_layout = QFormLayout(self.form_rapport)
        self.input_rapport_name = QLineEdit()
        self.input_rapport_amount = QLineEdit()
        form_rapport_layout.addRow("Nom du Rapport :", self.input_rapport_name)
        form_rapport_layout.addRow("Montant :", self.input_rapport_amount)
        self.stacked_widget.addWidget(self.form_rapport)

        # Formulaire pour Écriture Comptable
        self.form_ecriture = QWidget()
        form_ecriture_layout = QFormLayout(self.form_ecriture)
        self.input_ecriture_title = QLineEdit()
        self.input_ecriture_operation = QLineEdit()
        form_ecriture_layout.addRow("Titre :", self.input_ecriture_title)
        form_ecriture_layout.addRow("Opération :", self.input_ecriture_operation)
        self.stacked_widget.addWidget(self.form_ecriture)

        # Formulaire pour Rapport Temps Sup
        self.form_temps_sup = QWidget()
        form_temps_sup_layout = QFormLayout(self.form_temps_sup)
        self.input_temps_sup_title = QLineEdit()
        self.input_temps_sup_hours = QLineEdit()
        form_temps_sup_layout.addRow("Titre :", self.input_temps_sup_title)
        form_temps_sup_layout.addRow("Heures :", self.input_temps_sup_hours)
        self.stacked_widget.addWidget(self.form_temps_sup)

        # Formulaire pour CSA
        self.form_csa = QWidget()
        form_csa_layout = QFormLayout(self.form_csa)
        self.input_csa_title = QLineEdit()
        self.input_csa_details = QLineEdit()
        form_csa_layout.addRow("Titre :", self.input_csa_title)
        form_csa_layout.addRow("Détails :", self.input_csa_details)
        self.stacked_widget.addWidget(self.form_csa)

        # Formulaire pour Système Vision
        self.form_vision = QWidget()
        form_vision_layout = QFormLayout(self.form_vision)
        self.input_vision_title = QLineEdit()
        self.input_vision_params = QLineEdit()
        form_vision_layout.addRow("Titre :", self.input_vision_title)
        form_vision_layout.addRow("Paramètres :", self.input_vision_params)
        self.stacked_widget.addWidget(self.form_vision)

        # Formulaire pour Robot
        self.form_robot = QWidget()
        form_robot_layout = QFormLayout(self.form_robot)
        self.input_robot_title = QLineEdit()
        self.input_robot_config = QLineEdit()
        form_robot_layout.addRow("Titre :", self.input_robot_title)
        form_robot_layout.addRow("Configuration :", self.input_robot_config)
        self.stacked_widget.addWidget(self.form_robot)

        # Synchronisation de la page affichée avec le choix du combobox
        self.combo.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # Boutons OK et Annuler
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        """
        Retourne le type de document sélectionné et un dictionnaire contenant
        les valeurs saisies dans le formulaire associé.
        """
        doc_type = self.combo.currentText()
        data = {}
        index = self.combo.currentIndex()

        if index == 0:  # Rapport Dépense
            data['nom'] = self.input_rapport_name.text()
            data['montant'] = self.input_rapport_amount.text()
        elif index == 1:  # Écriture Comptable
            data['titre'] = self.input_ecriture_title.text()
            data['operation'] = self.input_ecriture_operation.text()
        elif index == 2:  # Rapport Temps Sup
            data['titre'] = self.input_temps_sup_title.text()
            data['heures'] = self.input_temps_sup_hours.text()
        elif index == 3:  # CSA
            data['titre'] = self.input_csa_title.text()
            data['details'] = self.input_csa_details.text()
        elif index == 4:  # Système Vision
            data['titre'] = self.input_vision_title.text()
            data['vision_params'] = self.input_vision_params.text()
        elif index == 5:  # Robot
            data['titre'] = self.input_robot_title.text()
            data['config'] = self.input_robot_config.text()
        return doc_type, data
