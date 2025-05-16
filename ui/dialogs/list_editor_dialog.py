from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QDialogButtonBox, QLabel, 
                             QInputDialog, QLineEdit, QFrame, QMessageBox)
from PyQt5.QtCore import Qt
from dataclasses import dataclass, field
from typing import List, Union, Any

# --- Modèles de données pour les items de la liste ---
@dataclass
class ListItemText:
    text: str
    type: str = field(default='Text', init=False)

    def __str__(self):
        return f"{self.text}"

@dataclass
class ListItemTextVariable:
    label: str
    variable_name: str
    type: str = field(default='TextVariable', init=False)

    def __str__(self):
        return f"{self.label}: {self.variable_name}"

@dataclass
class ListItemSeparator:
    type: str = field(default='Separator', init=False)

    def __str__(self):
        return "---"

# Type hint pour les items de la liste
ListItemType = Union[ListItemText, ListItemTextVariable, ListItemSeparator]

# --- Dialogue d'édition de la liste ---
class ListEditorDialog(QDialog):
    def __init__(self, parent=None, current_items: List[ListItemType] = None):
        super().__init__(parent)
        self.setWindowTitle("Éditeur de Liste d'Items")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self.items: List[ListItemType] = list(current_items) if current_items else []

        main_layout = QVBoxLayout(self)

        # Zone d'affichage de la liste
        self.items_list_widget = QListWidget()
        self._populate_list_widget()
        main_layout.addWidget(self.items_list_widget)

        # Boutons d'action pour ajouter des items
        actions_layout = QHBoxLayout()
        self.add_text_button = QPushButton("Ajouter Texte")
        self.add_text_variable_button = QPushButton("Ajouter Texte+Variable")
        self.add_separator_button = QPushButton("Ajouter Séparateur")
        
        actions_layout.addWidget(self.add_text_button)
        actions_layout.addWidget(self.add_text_variable_button)
        actions_layout.addWidget(self.add_separator_button)
        main_layout.addLayout(actions_layout)
        
        # TODO: Ajouter boutons pour Modifier, Supprimer, Monter, Descendre item sélectionné

        # Boutons OK / Annuler
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(button_box)

        # Connexions
        self.add_text_button.clicked.connect(self._add_text_item)
        self.add_text_variable_button.clicked.connect(self._add_text_variable_item)
        self.add_separator_button.clicked.connect(self._add_separator_item)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def _populate_list_widget(self):
        self.items_list_widget.clear()
        for item_obj in self.items:
            q_list_item = QListWidgetItem(str(item_obj))
            # On pourrait stocker l'objet lui-même dans l'item pour le récupérer plus tard
            q_list_item.setData(Qt.UserRole, item_obj) 
            self.items_list_widget.addItem(q_list_item)

    def _add_text_item(self):
        text, ok = QInputDialog.getText(self, "Ajouter Texte", "Texte de l'item:")
        if ok and text:
            self.items.append(ListItemText(text=text))
            self._populate_list_widget()

    def _add_text_variable_item(self):
        # Pourrait utiliser un dialogue plus complexe avec deux champs
        label, ok_label = QInputDialog.getText(self, "Ajouter Texte+Variable", "Label:")
        if ok_label and label:
            variable_name, ok_var = QInputDialog.getText(self, "Ajouter Texte+Variable", "Nom de la Variable:")
            if ok_var and variable_name:
                self.items.append(ListItemTextVariable(label=label, variable_name=variable_name))
                self._populate_list_widget()
            elif ok_var and not variable_name: # Variable name est vide mais OK cliqué
                 QMessageBox.warning(self, "Nom de variable manquant", "Le nom de la variable ne peut pas être vide.")
        elif ok_label and not label: # Label est vide mais OK cliqué
            QMessageBox.warning(self, "Label manquant", "Le label ne peut pas être vide.")


    def _add_separator_item(self):
        self.items.append(ListItemSeparator())
        self._populate_list_widget()

    def get_items(self) -> List[ListItemType]:
        """Retourne la liste des objets items si le dialogue est accepté."""
        if self.result() == QDialog.Accepted:
            return self.items
        return [] # Retourne une liste vide si annulé ou pas d'items

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    # Exemple d'items initiaux
    initial_items = [
        ListItemText("Première ligne de texte"),
        ListItemTextVariable("Utilisateur", "user_name"),
        ListItemSeparator(),
        ListItemText("Autre texte après séparateur")
    ]

    dialog = ListEditorDialog(current_items=initial_items)
    if dialog.exec_() == QDialog.Accepted:
        final_items = dialog.get_items()
        print("Dialogue accepté. Items:")
        for item in final_items:
            print(f"  - {item} (type: {item.type})")
    else:
        print("Dialogue annulé.")

    sys.exit(app.exec_()) 