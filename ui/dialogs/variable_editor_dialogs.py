from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, 
    QDialogButtonBox, QLabel, QLineEdit, QComboBox, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from dataclasses import dataclass, field
from typing import List, Union, Any

# --- Modèles de données pour les définitions de Variables ---
@dataclass
class VariableOption:
    value: Any # La valeur peut être de différent type, souvent str

    def __str__(self):
        return str(self.value)

@dataclass
class BaseVariable:
    name: str
    # prompt_text: str = "" # SUPPRIMÉ
    # type_name est géré par les sous-classes

@dataclass
class VariableLibre(BaseVariable):
    type_name: str = field(default='Libre', init=False)

    def __str__(self):
        return f"{self.name} (Libre)"

@dataclass
class VariableAvecChoix(BaseVariable):
    options: List[VariableOption] = field(default_factory=list)
    type_name: str = field(default='Choix', init=False)

    def __str__(self):
        return f"{self.name} (Choix: {len(self.options)} options)"

@dataclass
class VariableDate(BaseVariable):
    type_name: str = field(default='Date', init=False)
    # default_to_today: bool = True # Exemple d'option spécifique

    def __str__(self):
        return f"{self.name} (Date)"

# Union type pour les définitions de variables
VariableDefinitionType = Union[VariableLibre, VariableAvecChoix, VariableDate]


# --- Dialogue pour créer/éditer une variable spécifique ---
class VariableCreateEditDialog(QDialog):
    def __init__(self, parent=None, variable_to_edit: VariableDefinitionType = None, existing_names: List[str] = None):
        super().__init__(parent)
        self.existing_names = existing_names if existing_names else []
        self.variable = variable_to_edit
        self.is_editing = variable_to_edit is not None

        if self.is_editing:
            self.setWindowTitle(f"Modifier la Variable '{self.variable.name}'")
        else:
            self.setWindowTitle("Créer une Nouvelle Variable")
        
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)

        self.name_label = QLabel("Nom de la variable (unique):")
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)

        self.type_label = QLabel("Type de variable:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Libre", "Choix Multiples", "Date"])
        layout.addWidget(self.type_label)
        layout.addWidget(self.type_combo)

        # Section pour les options (si type "Choix Multiples")
        self.options_label = QLabel("Options (pour type Choix Multiples):")
        self.options_list_widget = QListWidget()
        self.options_list_widget.setFixedHeight(100)
        self.add_option_button = QPushButton("Ajouter Option")
        self.remove_option_button = QPushButton("Supprimer Option")
        options_buttons_layout = QHBoxLayout()
        options_buttons_layout.addWidget(self.add_option_button)
        options_buttons_layout.addWidget(self.remove_option_button)

        layout.addWidget(self.options_label)
        layout.addWidget(self.options_list_widget)
        layout.addLayout(options_buttons_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)

        # Visibilité initiale des options
        self._toggle_options_widgets(self.type_combo.currentText() == "Choix Multiples")

        # Connexions
        self.type_combo.currentTextChanged.connect(lambda text: self._toggle_options_widgets(text == "Choix Multiples"))
        self.add_option_button.clicked.connect(self._add_option)
        self.remove_option_button.clicked.connect(self._remove_option)
        self.button_box.accepted.connect(self.accept_dialog)
        self.button_box.rejected.connect(self.reject)

        if self.is_editing:
            self._load_variable_data()

    def _load_variable_data(self):
        if not self.variable: return
        self.name_edit.setText(self.variable.name)
        if isinstance(self.variable, VariableLibre):
            self.type_combo.setCurrentText("Libre")
        elif isinstance(self.variable, VariableDate):
            self.type_combo.setCurrentText("Date")
        elif isinstance(self.variable, VariableAvecChoix):
            self.type_combo.setCurrentText("Choix Multiples")
            for opt in self.variable.options:
                self.options_list_widget.addItem(QListWidgetItem(str(opt.value)))
        self.name_edit.setDisabled(True) # Ne pas permettre de changer le nom en mode édition pour l'instant

    def _toggle_options_widgets(self, show: bool):
        self.options_label.setVisible(show)
        self.options_list_widget.setVisible(show)
        self.add_option_button.setVisible(show)
        self.remove_option_button.setVisible(show)

    def _add_option(self):
        value, ok = QInputDialog.getText(self, "Ajouter Option", "Valeur de l'option:")
        if ok and value:
            # Vérifier si une option avec la même valeur existe déjà ?
            # Pour l'instant, on permet les doublons, mais on pourrait vérifier :
            # all_values = [self.options_list_widget.item(i).text() for i in range(self.options_list_widget.count())]
            # if value in all_values:
            #     QMessageBox.warning(self, "Option existante", "Cette valeur d'option existe déjà.")
            #     return
            self.options_list_widget.addItem(QListWidgetItem(value))
    
    def _remove_option(self):
        selected_items = self.options_list_widget.selectedItems()
        if not selected_items: return
        for item in selected_items:
            self.options_list_widget.takeItem(self.options_list_widget.row(item))

    def accept_dialog(self):
        var_name = self.name_edit.text().strip()
        var_type_str = self.type_combo.currentText()

        if not var_name:
            QMessageBox.warning(self, "Nom manquant", "Le nom de la variable est requis.")
            return

        if not self.is_editing and var_name in self.existing_names:
            QMessageBox.warning(self, "Nom existant", f"Une variable nommée '{var_name}' existe déjà.")
            return

        if var_type_str == "Libre":
            self.variable = VariableLibre(name=var_name)
        elif var_type_str == "Date":
            self.variable = VariableDate(name=var_name)
        elif var_type_str == "Choix Multiples":
            options_list = []
            for i in range(self.options_list_widget.count()):
                item_text = self.options_list_widget.item(i).text()
                # item_text est maintenant directement la valeur de l'option
                options_list.append(VariableOption(value=item_text))
            if not options_list:
                QMessageBox.warning(self, "Options manquantes", "Une variable de type 'Choix Multiples' doit avoir au moins une option.")
                return
            self.variable = VariableAvecChoix(name=var_name, options=options_list)
        else:
            QMessageBox.critical(self, "Erreur", "Type de variable inconnu.")
            return
        
        super().accept() # Accepter le dialogue

    def get_variable_definition(self) -> VariableDefinitionType | None:
        if self.result() == QDialog.Accepted:
            return self.variable
        return None

# --- Dialogue principal pour gérer et sélectionner les variables ---
class VariableManagerDialog(QDialog):
    def __init__(self, parent=None, current_variables: List[VariableDefinitionType] = None):
        super().__init__(parent)
        self.setWindowTitle("Gestionnaire de Variables")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Simule une base de données de variables. À remplacer par un vrai chargement/sauvegarde.
        self.variables: List[VariableDefinitionType] = list(current_variables) if current_variables else []
        self.selected_variable_object: VariableDefinitionType | None = None

        layout = QVBoxLayout(self)

        info_label = QLabel("Sélectionnez une variable existante ou créez-en une nouvelle.")
        layout.addWidget(info_label)

        self.variables_list_widget = QListWidget()
        self._populate_variables_list()
        layout.addWidget(self.variables_list_widget)

        actions_layout = QHBoxLayout()
        self.create_variable_button = QPushButton("Créer Variable")
        self.edit_variable_button = QPushButton("Modifier Variable") # TODO
        self.delete_variable_button = QPushButton("Supprimer Variable") # TODO
        actions_layout.addWidget(self.create_variable_button)
        actions_layout.addWidget(self.edit_variable_button)
        actions_layout.addWidget(self.delete_variable_button)
        self.edit_variable_button.setDisabled(True) # Activer si sélection
        self.delete_variable_button.setDisabled(True) # Activer si sélection
        layout.addLayout(actions_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Sélectionner Variable")
        self.button_box.button(QDialogButtonBox.Ok).setDisabled(True) # Activer si sélection
        layout.addWidget(self.button_box)

        # Connexions
        self.create_variable_button.clicked.connect(self._create_new_variable)
        self.variables_list_widget.itemSelectionChanged.connect(self._on_variable_selection_changed)
        self.variables_list_widget.itemDoubleClicked.connect(lambda item: self.accept() if item else None) # Accepter au double clic
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _populate_variables_list(self):
        self.variables_list_widget.clear()
        for var_def in self.variables:
            item = QListWidgetItem(str(var_def))
            item.setData(Qt.UserRole, var_def) # Stocker l'objet variable
            self.variables_list_widget.addItem(item)
    
    def _get_existing_variable_names(self) -> List[str]:
        return [v.name for v in self.variables]

    def _create_new_variable(self):
        create_dialog = VariableCreateEditDialog(self, existing_names=self._get_existing_variable_names())
        if create_dialog.exec_() == QDialog.Accepted:
            new_var = create_dialog.get_variable_definition()
            if new_var:
                self.variables.append(new_var)
                self._populate_variables_list()
                # Optionnel: sélectionner la nouvelle variable
                for i in range(self.variables_list_widget.count()):
                    if self.variables_list_widget.item(i).data(Qt.UserRole).name == new_var.name:
                        self.variables_list_widget.setCurrentRow(i)
                        break
                # TODO: Logique de sauvegarde globale des variables ici

    def _on_variable_selection_changed(self):
        selected_items = self.variables_list_widget.selectedItems()
        if selected_items:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
            self.edit_variable_button.setEnabled(True)
            self.delete_variable_button.setEnabled(True)
            var_obj = selected_items[0].data(Qt.UserRole)
            self.selected_variable_object = var_obj
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.edit_variable_button.setEnabled(False)
            self.delete_variable_button.setEnabled(False)
            self.selected_variable_object = None

    def get_selected_variable_definition(self) -> VariableDefinitionType | None:
        if self.result() == QDialog.Accepted and self.selected_variable_object:
            return self.selected_variable_object
        return None

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Exemple de variables initiales pour test
    initial_vars = [
        VariableLibre(name="NomClient"),
        VariableAvecChoix(name="TypeService", options=[
            VariableOption("Standard"), VariableOption("Express")
        ]),
        VariableDate(name="DateIntervention")
    ]

    manager_dialog = VariableManagerDialog(current_variables=initial_vars)
    if manager_dialog.exec_() == QDialog.Accepted:
        selected_var_obj = manager_dialog.get_selected_variable_definition()
        if selected_var_obj:
            print(f"Variable sélectionnée: {selected_var_obj.name}")
            print(f"  Définition: {selected_var_obj}")
        else:
            print("Aucune variable sélectionnée mais dialogue accepté (devrait être désactivé).")
    else:
        print("Gestionnaire de variables annulé.")

    sys.exit(app.exec_()) 