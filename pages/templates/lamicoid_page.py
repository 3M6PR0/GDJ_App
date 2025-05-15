from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QFormLayout, QDateEdit, 
                             QLineEdit, QSpinBox, QComboBox, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
import logging
from datetime import datetime

from models.documents.lamicoid.lamicoid import LamicoidDocument
from models.documents.lamicoid.lamicoid_item import LamicoidItem
from ui.components.lamicoid_item_card import LamicoidItemCardWidget
from utils.signals import signals

logger = logging.getLogger('GDJ_App')

class LamicoidPage(QWidget):
    document_saved_signal = pyqtSignal(str)
    # Pour gérer l'édition d'un item spécifique
    editing_item_id: str | None = None 

    def __init__(self, document: LamicoidDocument, parent=None):
        super().__init__(parent)
        self.setObjectName("LamicoidPage")
        self.document = document
        self.editing_item_id = None # Aucun item en édition au départ
        
        self._init_ui()
        self._load_and_display_items()
        logger.debug(f"LamicoidPage initialisée pour document: {document.file_name or 'Nouveau Lamicoid'}")

    def _init_ui(self):
        # Layout principal de la page (horizontal pour les deux panneaux)
        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        # --- Panneau Gauche (Formulaire d'édition/ajout) ---
        left_panel = QFrame()
        left_panel.setObjectName("LamicoidFormPanel")
        left_panel.setFixedWidth(350) # Largeur fixe pour le formulaire
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(5,5,5,5)
        left_panel_layout.setSpacing(8)

        # Titre du panneau gauche (change si ajout ou édition)
        self.form_title_label = QLabel("Ajouter un nouvel item Lamicoid")
        self.form_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        left_panel_layout.addWidget(self.form_title_label)

        # ComboBox pour type de Lamicoid (placeholder pour l'instant)
        type_lamicoid_label = QLabel("Type de Lamicoid (Placeholder):")
        self.type_lamicoid_combo = QComboBox()
        self.type_lamicoid_combo.addItem("Standard Lamicoid Item") # Option par défaut
        # self.type_lamicoid_combo.currentIndexChanged.connect(self._on_lamicoid_type_changed)
        # Pour l'instant, ce combo ne fait rien
        form_combo_layout = QHBoxLayout()
        form_combo_layout.addWidget(type_lamicoid_label)
        form_combo_layout.addWidget(self.type_lamicoid_combo)
        left_panel_layout.addLayout(form_combo_layout)
        
        # Formulaire pour les champs de LamicoidItem
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.form_layout.addRow("Date:", self.date_edit)
        
        self.ref_edit = QLineEdit()
        self.form_layout.addRow("Numéro Réf.:", self.ref_edit)
        
        self.desc_edit = QLineEdit() # Pourrait être QTextEdit pour plus d'espace
        self.form_layout.addRow("Description:", self.desc_edit)
        
        self.qty_edit = QSpinBox()
        self.qty_edit.setRange(0, 9999)
        self.qty_edit.setValue(1) # Valeur par défaut
        self.form_layout.addRow("Quantité:", self.qty_edit)
        
        self.material_edit = QLineEdit()
        self.form_layout.addRow("Matériel:", self.material_edit)
        
        left_panel_layout.addLayout(self.form_layout)
        left_panel_layout.addStretch(1) # Pousse les boutons vers le bas

        # Boutons pour le formulaire
        form_buttons_layout = QHBoxLayout()
        self.form_action_button = QPushButton("Ajouter Item") # Texte change en "Sauvegarder Item"
        self.form_action_button.clicked.connect(self._handle_form_action_button)
        self.form_cancel_button = QPushButton("Annuler")
        self.form_cancel_button.clicked.connect(self._cancel_edit_mode)
        self.form_cancel_button.setVisible(False) # Caché par défaut

        form_buttons_layout.addStretch()
        form_buttons_layout.addWidget(self.form_cancel_button)
        form_buttons_layout.addWidget(self.form_action_button)
        left_panel_layout.addLayout(form_buttons_layout)
        
        page_layout.addWidget(left_panel)

        # --- Panneau Droit (Liste des items sous forme de cartes) ---
        right_panel = QFrame()
        right_panel.setObjectName("LamicoidListPanel")
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0,0,0,0)

        list_title_label = QLabel("Liste des Items Lamicoid")
        list_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        right_panel_layout.addWidget(list_title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("LamicoidListScrollArea")

        self.cards_container_widget = QWidget() # Widget qui contiendra le layout des cartes
        self.cards_container_widget.setObjectName("CardsContainer")
        self.cards_container_layout = QVBoxLayout(self.cards_container_widget)
        self.cards_container_layout.setAlignment(Qt.AlignTop) # Les cartes s'empilent en haut
        self.cards_container_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.cards_container_widget)
        right_panel_layout.addWidget(self.scroll_area)
        page_layout.addWidget(right_panel, 1) # Le panneau droit prend l'espace restant

        # Bouton de sauvegarde global du document (en bas du panneau de droite ou ailleurs)
        # Pour l'instant, plaçons-le sous la liste des cartes.
        self.save_document_button = QPushButton("Sauvegarder Document Lamicoid")
        self.save_document_button.clicked.connect(self._save_document_clicked)
        right_panel_layout.addWidget(self.save_document_button)
        
        self.setLayout(page_layout)

    def _clear_form_fields(self):
        self.date_edit.setDate(QDate.currentDate())
        self.ref_edit.clear()
        self.desc_edit.clear()
        self.qty_edit.setValue(1)
        self.material_edit.clear()
        self.type_lamicoid_combo.setCurrentIndex(0) # Réinitialiser au type par défaut

    def _populate_form_fields(self, item: LamicoidItem):
        self.date_edit.setDate(QDate.fromString(item.date_item, "yyyy-MM-dd"))
        self.ref_edit.setText(item.numero_reference or "")
        self.desc_edit.setText(item.description or "")
        self.qty_edit.setValue(item.quantite or 0)
        self.material_edit.setText(item.materiel or "")
        # La sélection du type de Lamicoid pourrait être mise à jour ici si elle était dynamique

    def _load_and_display_items(self):
        # Vider les cartes existantes
        while self.cards_container_layout.count():
            child = self.cards_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Créer et ajouter les nouvelles cartes
        if self.document and self.document.items:
            for item in self.document.items:
                card = LamicoidItemCardWidget(item, self.cards_container_widget)
                card.edit_requested.connect(self._handle_edit_item_request)
                card.delete_requested.connect(self._handle_delete_item_request)
                self.cards_container_layout.addWidget(card)
        # Ajouter un spacer pour pousser les cartes vers le haut si peu nombreuses
        # self.cards_container_layout.addStretch(1) 
        # Attention: un stretch permanent peut être problématique si on ajoute/supprime beaucoup.
        # Il est souvent mieux de juste laisser les widgets s'empiler naturellement avec AlignTop.

    def _enter_edit_mode(self, item: LamicoidItem):
        self.editing_item_id = item.id_item
        self._populate_form_fields(item)
        self.form_title_label.setText("Modifier l'item Lamicoid")
        self.form_action_button.setText("Sauvegarder Item")
        self.form_cancel_button.setVisible(True)
        logger.debug(f"Entrée en mode édition pour item ID: {item.id_item}")

    def _exit_edit_mode(self):
        self.editing_item_id = None
        self._clear_form_fields()
        self.form_title_label.setText("Ajouter un nouvel item Lamicoid")
        self.form_action_button.setText("Ajouter Item")
        self.form_cancel_button.setVisible(False)
        logger.debug("Sortie du mode édition.")

    def _cancel_edit_mode(self):
        self._exit_edit_mode()

    def _handle_form_action_button(self):
        # Récupérer les données du formulaire
        date_val = self.date_edit.date().toString("yyyy-MM-dd")
        ref_val = self.ref_edit.text().strip()
        desc_val = self.desc_edit.text().strip()
        qty_val = self.qty_edit.value()
        material_val = self.material_edit.text().strip()

        # Validation simple (à améliorer)
        if not ref_val:
            QMessageBox.warning(self, "Champ manquant", "Le numéro de référence est requis.")
            self.ref_edit.setFocus()
            return
        if qty_val <= 0:
            QMessageBox.warning(self, "Valeur invalide", "La quantité doit être supérieure à zéro.")
            self.qty_edit.setFocus()
            return

        try:
            if self.editing_item_id:
                # Mode Édition
                item_to_update = self.document.get_item_by_id(self.editing_item_id)
                if item_to_update:
                    item_to_update.date_item = date_val
                    item_to_update.numero_reference = ref_val
                    item_to_update.description = desc_val
                    item_to_update.quantite = qty_val
                    item_to_update.materiel = material_val
                    # Notifier la carte correspondante de mettre à jour son affichage
                    for i in range(self.cards_container_layout.count()):
                        widget = self.cards_container_layout.itemAt(i).widget()
                        if isinstance(widget, LamicoidItemCardWidget) and widget.get_item().id_item == self.editing_item_id:
                            widget.update_data(item_to_update) # Mettre à jour les données de la carte
                            break
                    logger.info(f"Item Lamicoid ID '{self.editing_item_id}' mis à jour.")
                else:
                    logger.error(f"Impossible de trouver l'item ID '{self.editing_item_id}' pour la mise à jour.")
                self._exit_edit_mode()
            else:
                # Mode Ajout
                new_item = LamicoidItem(
                    date_item=date_val,
                    numero_reference=ref_val,
                    description=desc_val,
                    quantite=qty_val,
                    materiel=material_val
                )
                self.document.add_item(new_item)
                # Ajouter une nouvelle carte (au lieu de tout recharger pour l'instant)
                card = LamicoidItemCardWidget(new_item, self.cards_container_widget)
                card.edit_requested.connect(self._handle_edit_item_request)
                card.delete_requested.connect(self._handle_delete_item_request)
                self.cards_container_layout.addWidget(card)
                logger.info(f"Nouvel item Lamicoid ajouté: {new_item.id_item}")
                self._clear_form_fields()
            
            # Optionnel: Défiler vers le bas si une nouvelle carte est ajoutée
            # self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout/modification de l'item Lamicoid: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def _handle_edit_item_request(self, item: LamicoidItem):
        self._enter_edit_mode(item)

    def _handle_delete_item_request(self, item_to_delete: LamicoidItem):
        reply = QMessageBox.question(self, "Confirmation de suppression", 
                                     f"Êtes-vous sûr de vouloir supprimer l'item '{item_to_delete.numero_reference or item_to_delete.id_item}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.document.remove_item(item_to_delete.id_item):
                logger.info(f"Item Lamicoid ID '{item_to_delete.id_item}' supprimé du document.")
                # Retrouver et supprimer la carte de l'UI
                for i in range(self.cards_container_layout.count()):
                    widget = self.cards_container_layout.itemAt(i).widget()
                    if isinstance(widget, LamicoidItemCardWidget) and widget.get_item().id_item == item_to_delete.id_item:
                        widget.deleteLater()
                        self.cards_container_layout.takeAt(i) # Retirer du layout
                        logger.debug(f"Carte pour item ID '{item_to_delete.id_item}' supprimée de l'UI.")
                        break
                if self.editing_item_id == item_to_delete.id_item: # Si on supprime l'item en cours d'édition
                    self._exit_edit_mode()
            else:
                logger.warning(f"Impossible de supprimer l'item ID '{item_to_delete.id_item}' du document.")
                QMessageBox.warning(self, "Erreur", "L'item n'a pas pu être supprimé du document.")

    def _save_document_clicked(self):
        try:
            # La méthode get_document s'assure que self.document.items est à jour
            # Mais ici, les modifications sont déjà faites directement sur self.document.items
            # lors de l'ajout/modification/suppression.
            
            # Il n'est plus nécessaire de faire self.document.items = list(self.items_model._items)
            # car nous n'utilisons plus self.items_model.

            file_path_tuple = self.document.save() # save() retourne (document_data, [])
            if file_path_tuple and isinstance(file_path_tuple, tuple) and len(file_path_tuple) > 0:
                # La vraie sauvegarde du fichier est gérée par MainController ou DocumentWindow
                # Ici, on prépare juste les données et on émet un signal.
                # Le retour de self.document.save() est (dict_data, list_factures_a_copier)
                # Le signal document_saved attend (doc_type, file_path_str, doc_title_str)
                # Le file_path effectif sera déterminé par le gestionnaire de sauvegarde.
                # Pour l'instant, nous n'avons pas le chemin final ici.
                # Nous allons émettre le signal avec le file_name actuel du document.
                
                logger.info(f"Document Lamicoid '{self.document.title}' (fichier: {self.document.file_name}) prêt pour sauvegarde.")
                signals.document_saved.emit(self.document.type_document, self.document.file_name, self.document.title)
                self.document_saved_signal.emit(self.document.file_name) 
                QMessageBox.information(self, "Sauvegarde", f"Les données du document Lamicoid '{self.document.title}' sont prêtes à être sauvegardées.")
            else:
                logger.error("Échec de la préparation à la sauvegarde du document Lamicoid.")
                QMessageBox.critical(self, "Erreur Sauvegarde", "Les données du document n'ont pas pu être préparées pour la sauvegarde.")
        except Exception as e:
            logger.exception(f"Erreur lors de la préparation à la sauvegarde du document Lamicoid: {e}")
            QMessageBox.critical(self, "Erreur Sauvegarde", f"Une erreur critique est survenue: {e}")

    def get_document(self) -> LamicoidDocument:
        # Les modifications sont faites directement sur self.document.items,
        # donc il devrait être à jour.
        return self.document

    def can_close(self) -> bool:
        # TODO: Vérifier modifications non sauvegardées
        return True

# Retrait de l'ancien main de test qui utilisait QTableView

# Exemple d'utilisation (pour test si exécuté directement, ce qui n'est pas le cas dans l'app)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Créer un LamicoidDocument de test
    test_doc = LamicoidDocument(file_name="TestLamicoid.json", profile_name="TestProfile")
    test_doc.add_item(LamicoidItem(date_item="2023-10-01", numero_reference="REF001", description="Item 1", quantite=2, materiel="Bois"))
    test_doc.add_item(LamicoidItem(date_item="2023-10-02", numero_reference="REF002", description="Item 2", quantite=5, materiel="Metal"))

    main_window = QWidget() # Simuler une fenêtre principale
    layout = QVBoxLayout(main_window)
    
    lamicoid_page = LamicoidPage(document=test_doc)
    layout.addWidget(lamicoid_page)
    
    main_window.setWindowTitle("Test LamicoidPage")
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec_()) 