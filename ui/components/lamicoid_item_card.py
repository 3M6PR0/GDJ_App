from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QSizePolicy, QMenu, QAction, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot
from PyQt5.QtGui import QIcon

from models.documents.lamicoid.lamicoid_item import LamicoidItem
from utils.icon_loader import get_icon_path # Assurez-vous que ce chemin est correct
import logging

logger = logging.getLogger('GDJ_App')

class LamicoidItemCardWidget(QFrame):
    """Widget "carte" pour afficher un LamicoidItem et offrir des actions."""
    edit_requested = pyqtSignal(LamicoidItem)
    delete_requested = pyqtSignal(LamicoidItem)

    def __init__(self, item: LamicoidItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("LamicoidItemCardWidget")
        # Appliquer un style de base, peut être affiné avec QSS externe
        self.setStyleSheet("""
            #LamicoidItemCardWidget {
                background-color: #4a4d4e; /* Similaire à CardWidget */
                border-radius: 4px;
                border: 1px solid #5a5d5e;
                margin: 0 5px 5px 5px; /* Marge pour espacement */
            }
            QLabel {
                background-color: transparent;
                border: none;
                font-size: 9pt;
            }
            QPushButton {
                font-size: 9pt;
                padding: 3px;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(5)

        # Section Résumé (toujours visible)
        summary_widget = QWidget()
        summary_layout = QHBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0,0,0,0)
        summary_layout.setSpacing(10)

        # Colonnes pour le résumé
        date_label = QLabel(f"<b>Date:</b> {self.item.date_item or 'N/A'}")
        ref_label = QLabel(f"<b>Réf:</b> {self.item.numero_reference or 'N/A'}")
        qty_label = QLabel(f"<b>Qté:</b> {self.item.quantite or 0}")
        
        summary_layout.addWidget(date_label, 1) # Poids pour l'expansion
        summary_layout.addWidget(ref_label, 2)  # Poids plus grand pour la référence
        summary_layout.addWidget(qty_label, 0)  # Poids minimal

        # Bouton Options
        self.options_button = QPushButton()
        options_icon_path = get_icon_path("round_more_vert.png")
        if options_icon_path:
            self.options_button.setIcon(QIcon(options_icon_path))
        else:
            self.options_button.setText("...") # Fallback si icône non trouvée
        self.options_button.setFixedSize(24, 24)
        self.options_button.setToolTip("Options de l'item")
        self.options_button.clicked.connect(self._show_options_menu)
        summary_layout.addWidget(self.options_button)
        
        main_layout.addWidget(summary_widget)

        # Section Détails (pourrait être extensible si nécessaire, pour l'instant simple)
        details_layout = QVBoxLayout() # Utiliser QVBoxLayout pour empiler Description et Matériel
        details_layout.setContentsMargins(5,0,0,0) # Petite marge à gauche
        details_layout.setSpacing(3)

        desc_title_label = QLabel("<b>Description:</b>")
        self.desc_label = QLabel(self.item.description or "-")
        self.desc_label.setWordWrap(True)
        self.desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)


        material_title_label = QLabel("<b>Matériel:</b>")
        self.material_label = QLabel(self.item.materiel or "-")
        self.material_label.setWordWrap(True)
        self.material_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        details_layout.addWidget(desc_title_label)
        details_layout.addWidget(self.desc_label)
        details_layout.addWidget(material_title_label)
        details_layout.addWidget(self.material_label)
        
        main_layout.addLayout(details_layout)
        self.setLayout(main_layout)
    
    def update_data(self, new_item_data: LamicoidItem):
        """Met à jour l'affichage de la carte avec de nouvelles données d'item."""
        self.item = new_item_data # Mettre à jour l'item interne
        
        # Mettre à jour les labels (exemple simple, à étendre si la structure des labels change)
        # Pour un rafraîchissement complet, on pourrait reconstruire l'UI ou des parties.
        # Ici, on met juste à jour les textes des labels existants.
        
        # Il faudrait s'assurer que les labels du résumé sont aussi mis à jour
        # Pour l'instant, on se concentre sur les détails qui sont des QLabel distincts.
        self.desc_label.setText(self.item.description or "-")
        self.material_label.setText(self.item.materiel or "-")
        
        # Si les labels du résumé (date, réf, qté) sont aussi des attributs de la classe,
        # on pourrait les mettre à jour ici de la même manière.
        # Par exemple, si date_label était self.date_display_label:
        # self.date_display_label.setText(f"<b>Date:</b> {self.item.date_item or 'N/A'}")
        # etc.

        # Une solution plus robuste pour le résumé serait de le reconstruire ou d'avoir des
        # références directes aux QLabel qui affichent date, réf, qté.
        # Pour l'instant, cette méthode est basique.
        logger.debug(f"LamicoidItemCardWidget {self.item.id_item} mis à jour.")


    @pyqtSlot()
    def _show_options_menu(self):
        menu = QMenu(self)
        
        edit_action = QAction(QIcon(get_icon_path("round_edit.png") or ""), "Modifier cet item", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.item))
        menu.addAction(edit_action)

        delete_action = QAction(QIcon(get_icon_path("round_delete.png") or ""), "Supprimer cet item", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.item))
        menu.addAction(delete_action)
        
        menu.exec_(self.options_button.mapToGlobal(self.options_button.rect().bottomLeft()))

    def get_item(self) -> LamicoidItem:
        return self.item

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    from datetime import date

    app = QApplication(sys.argv)

    # Créer un LamicoidItem de test
    test_item1 = LamicoidItem(
        date_item=date(2023, 10, 1), 
        numero_reference="REF001-XYZ", 
        description="Plaque de Lamicoid pour panneau électrique principal avec gravure spéciale et logo couleur. Ceci est une description assez longue pour tester le word wrap et voir comment ça se comporte sur plusieurs lignes.", 
        quantite=2, 
        materiel="Lamicoid Rouge/Blanc 3mm")
    
    test_item2 = LamicoidItem(
        date_item=date(2023, 10, 5), 
        numero_reference="REF002-ABC", 
        description="Petites étiquettes pour boutons", 
        quantite=50, 
        materiel="Lamicoid Noir/Blanc 1.5mm")

    main_widget = QWidget()
    test_layout = QVBoxLayout(main_widget)
    
    card1 = LamicoidItemCardWidget(test_item1)
    card2 = LamicoidItemCardWidget(test_item2)

    test_layout.addWidget(card1)
    test_layout.addWidget(card2)
    test_layout.addStretch()

    main_widget.setWindowTitle("Test LamicoidItemCardWidget")
    main_widget.resize(400, 300)
    main_widget.show()

    sys.exit(app.exec_()) 