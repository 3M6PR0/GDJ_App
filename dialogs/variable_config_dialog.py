from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QDialogButtonBox, QPushButton, QWidget, QCheckBox)
from PyQt5.QtCore import Qt

class VariableConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de la Variable")
        self.setMinimumWidth(400) # Augmenter un peu la largeur

        self._init_ui()
        self.selectable_value_edits = [] # Pour stocker les QLineEdit des valeurs sélectionnables
        self._on_type_changed(self.type_combo.currentText()) # Appel initial pour configurer l'UI

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    child_layout = item.layout()
                    if child_layout is not None:
                        self._clear_layout(child_layout)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10) # Ajuster l'espacement

        # --- Nom de la variable ---
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom de la variable:")
        self.name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        main_layout.addLayout(name_layout)

        # --- Type de variable ---
        type_layout = QHBoxLayout()
        type_label = QLabel("Type de variable:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("Valeur personnalisable")
        self.type_combo.addItem("Valeur sélectionnable")
        self.type_combo.currentTextChanged.connect(self._on_type_changed) # Connexion du signal
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        main_layout.addLayout(type_layout)
        
        # --- Espace pour options dynamiques ---
        self.dynamic_options_widget = QWidget()
        self.dynamic_options_layout = QVBoxLayout(self.dynamic_options_widget)
        self.dynamic_options_layout.setContentsMargins(0, 5, 0, 5) # Ajouter un peu de marge verticale
        main_layout.addWidget(self.dynamic_options_widget)

        # --- Boutons OK / Annuler ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _on_type_changed(self, selected_type):
        self._clear_layout(self.dynamic_options_layout)
        self.selectable_value_edits = [] # Réinitialiser la liste

        if selected_type == "Valeur personnalisable":
            self.dynamic_options_widget.setVisible(True)
            
            unit_checkbox = QCheckBox("Définir une unité ?")
            self.dynamic_options_layout.addWidget(unit_checkbox)

            unit_input_widget = QWidget() # Widget conteneur pour le label et le lineedit de l'unité
            unit_input_layout = QHBoxLayout(unit_input_widget)
            unit_input_layout.setContentsMargins(15,0,0,0) # Indentation pour l'option d'unité
            unit_label = QLabel("Unité:")
            self.unit_edit = QLineEdit()
            unit_input_layout.addWidget(unit_label)
            unit_input_layout.addWidget(self.unit_edit)
            self.dynamic_options_layout.addWidget(unit_input_widget)
            unit_input_widget.setVisible(False) # Initialement caché

            unit_checkbox.toggled.connect(unit_input_widget.setVisible)
            # Stocker les références si nécessaire pour get_variable_data
            self.current_unit_checkbox = unit_checkbox 
            self.current_unit_edit = self.unit_edit

        elif selected_type == "Valeur sélectionnable":
            self.dynamic_options_widget.setVisible(True)
            self._add_selectable_value_field() # Ajouter le premier champ

            add_button = QPushButton("Ajouter une valeur")
            add_button.clicked.connect(self._add_selectable_value_field)
            self.dynamic_options_layout.addWidget(add_button, 0, Qt.AlignLeft) # Aligner à gauche
            
        else:
            self.dynamic_options_widget.setVisible(False)
        
        self.adjustSize() # Ajuster la taille du dialogue au nouveau contenu

    def _add_selectable_value_field(self):
        """Ajoute un QLineEdit pour une nouvelle valeur sélectionnable."""
        new_value_edit = QLineEdit()
        new_value_edit.setPlaceholderText(f"Valeur {len(self.selectable_value_edits) + 1}")
        self.dynamic_options_layout.insertWidget(self.dynamic_options_layout.count() -1, new_value_edit) # Insérer avant le bouton "Ajouter"
        self.selectable_value_edits.append(new_value_edit)
        self.adjustSize()

    def get_variable_data(self):
        """Retourne les données configurées."""
        if self.result() != QDialog.Accepted:
            return None

        data = {
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText()
        }

        if data["type"] == "Valeur personnalisable":
            if hasattr(self, 'current_unit_checkbox') and self.current_unit_checkbox.isChecked():
                data["has_unit"] = True
                data["unit"] = self.current_unit_edit.text().strip()
            else:
                data["has_unit"] = False
                data["unit"] = None
        
        elif data["type"] == "Valeur sélectionnable":
            data["selectable_values"] = [edit.text().strip() for edit in self.selectable_value_edits if edit.text().strip()]

        return data

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = VariableConfigDialog()
    if dialog.exec_():
        data = dialog.get_variable_data()
        print("Données de la variable:", data)
    sys.exit(app.exec_()) 