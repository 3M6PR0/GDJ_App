from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QDialogButtonBox, QScrollArea, QWidget, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
# S'assurer que VariableConfigDialog est accessible, ajuster le chemin si nécessaire
# Si VariableConfigDialog est dans le même dossier 'dialogs':
from .variable_config_dialog import VariableConfigDialog

class ExistingVariablesDialog(QDialog):
    # Signal émis lorsqu'une variable est cliquée pour être ajoutée à l'éditeur
    # Passe le dictionnaire de données de la variable
    variable_clicked_to_add = pyqtSignal(dict)

    def __init__(self, project_variables, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des Variables")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        self.initial_project_variables = list(project_variables) # Copie de la liste initiale
        self.newly_added_in_this_session = [] # Variables ajoutées via le bouton "Ajouter..."
        # self.selected_variable_name = None # Plus besoin de cette sélection globale

        self._init_ui()
        self._populate_variables_buttons() # Peupler avec les variables initiales

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        title_label = QLabel("Cliquez sur une variable pour l'ajouter à l'éditeur, ou ajoutez-en une nouvelle.")
        title_label.setWordWrap(True)
        main_layout.addWidget(title_label)

        # Scroll Area pour les boutons de variables
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.variables_button_layout = QVBoxLayout(scroll_widget)
        self.variables_button_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1) 

        # Bouton pour ajouter une nouvelle variable
        self.add_new_button = QPushButton("Ajouter une Nouvelle Variable...")
        self.add_new_button.clicked.connect(self._handle_add_new_variable)
        main_layout.addWidget(self.add_new_button)

        # Boutons de dialogue - On garde juste "Fermer" (ou Annuler si on veut être strict sur exec_)
        # button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # self.ok_button = button_box.button(QDialogButtonBox.Ok)
        # self.ok_button.setText("Utiliser Sélection")
        # self.ok_button.setEnabled(False) 
        # button_box.accepted.connect(self.accept)
        # button_box.rejected.connect(self.reject)

        # Un simple bouton Fermer suffit si le dialogue reste ouvert après clic sur variable.
        # Si on veut qu'il se ferme après chaque action, on pourrait ne pas avoir besoin de bouton de dialogue.
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept) # On utilise accept() pour indiquer une fermeture "normale"
        main_layout.addWidget(close_button)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout:
                    self._clear_layout(child_layout)

    def _populate_variables_buttons(self):
        self._clear_layout(self.variables_button_layout)
        current_display_list = self.initial_project_variables + self.newly_added_in_this_session
        
        print(f"[ExistingVariablesDialog] Populando botões. {len(current_display_list)} variáveis à afficher.") # Log

        if not current_display_list:
            no_var_label = QLabel("Aucune variable définie.")
            no_var_label.setAlignment(Qt.AlignCenter)
            self.variables_button_layout.addWidget(no_var_label)
            return

        for var_data in current_display_list:
            var_name = var_data.get("name", "Variable Inconnue")
            btn = QPushButton(var_name)
            # Forcer un style minimal pour le test
            btn.setStyleSheet("QPushButton { background-color: #555; color: white; border: 1px solid #777; padding: 5px; }") 
            btn.clicked.connect(lambda checked_status=None, bound_data=var_data: self._on_variable_button_clicked(bound_data))
            
            print(f"[ExistingVariablesDialog] Ajout du bouton pour : {var_name}") # Log
            self.variables_button_layout.addWidget(btn)
        self.variables_button_layout.addStretch(1)

    def _on_variable_button_clicked(self, variable_data_dict):
        """Émet un signal avec les données de la variable cliquée."""
        print(f"[ExistingVariablesDialog] Bouton cliqué pour variable: {variable_data_dict.get('name')}")
        self.variable_clicked_to_add.emit(variable_data_dict)
        # On pourrait fermer le dialogue ici si on voulait un ajout unique par ouverture :
        # self.accept()
        # Ou le laisser ouvert pour ajouter plusieurs variables.

    def _handle_add_new_variable(self):
        var_config_dialog = VariableConfigDialog(self)
        if var_config_dialog.exec_():
            new_variable_data = var_config_dialog.get_variable_data()
            if new_variable_data:
                all_names = [v.get('name') for v in self.initial_project_variables] + \
                            [v.get('name') for v in self.newly_added_in_this_session]
                if new_variable_data.get('name') in all_names:
                    print(f"AVERTISSEMENT: Le nom de variable '{new_variable_data.get('name')}' existe déjà.")
                
                self.newly_added_in_this_session.append(new_variable_data)
                self._populate_variables_buttons() # Rafraîchir la liste
                # Optionnel: émettre un signal ici aussi si on veut que la LamicoidPage soit notifiée immédiatement
                # de l'ajout, même sans que l'utilisateur reclique sur le bouton de la variable.
                # self.variable_clicked_to_add.emit(new_variable_data) # Ou alors, l'utilisateur doit cliquer dessus.

    # def get_selected_variable_data(self): # Plus directement pertinent de cette manière
    #     return self.selected_variable_data_dict if hasattr(self, 'selected_variable_data_dict') else None

    def get_newly_added_variables_this_session(self):
        """Retourne les variables qui ont été créées via le bouton 'Ajouter' dans cette session du dialogue."""
        return self.newly_added_in_this_session

# Pour tester ce dialogue isolément :
if __name__ == '__main__':
    app = QApplication(sys.argv)
    sample_vars = [
        {"name": "LargeurGlobale", "type": "Valeur personnalisable", "has_unit": True, "unit": "cm"},
        {"name": "CouleurCadre", "type": "Valeur sélectionnable", "selectable_values": ["Noir", "Blanc", "Gris"]}
    ]
    dialog = ExistingVariablesDialog(sample_vars)
    
    def test_slot(var_data):
        print(f"Signal variable_clicked_to_add reçu pour: {var_data.get('name')}")

    dialog.variable_clicked_to_add.connect(test_slot)
    
    # exec_() est bloquant, donc on ne verra le print que si le dialogue est fermé (ou après un accept/reject)
    # Si le dialogue reste ouvert, les signaux sont gérés par la boucle d'événements de l'app principale.
    dialog.exec_() 
    # Si on a cliqué sur "Fermer" (qui appelle accept), on peut récupérer les variables ajoutées:
    newly_added = dialog.get_newly_added_variables_this_session()
    print(f"Variables ajoutées dans cette session (après fermeture dialogue): {newly_added}")

    # sys.exit(app.exec_()) # On commente pour éviter une double boucle si on exécute déjà une app

    app.exec_() 