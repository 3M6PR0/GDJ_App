from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QScrollArea, QFormLayout, QDateEdit, 
                             QLineEdit, QSpinBox, QComboBox, QSizePolicy, QMessageBox,
                             QStackedWidget, QDialog)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
import logging
from datetime import datetime

from models.documents.lamicoid.lamicoid import LamicoidDocument
from models.documents.lamicoid.lamicoid_item import LamicoidItem
from ui.components.lamicoid_display_widget import LamicoidDisplayWidget
from ui.editors.disposition_editor_widget import DispositionEditorWidget
from ui.editors.model_editor_widget import ModelEditorWidget
from ui.components.frame import Frame
from utils.signals import signals
from ui.dialogs.text_input_dialog import TextInputDialog

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
        self._connect_signals()
        self.lamicoid_display.update_display() # Appel initial pour afficher le placeholder
        logger.debug(f"LamicoidPage initialisée pour document: {document.file_name or 'Nouveau Lamicoid'}")

    def _init_ui(self):
        # Layout principal de la page (horizontal pour les deux panneaux)
        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(10)

        # --- Panneau Gauche (Formulaire d'édition/ajout) ---
        # Création de l'en-tête pour le panneau gauche
        left_header_widget = QWidget()
        left_header_widget.setObjectName("FrameHeaderContainer")
        left_header_layout = QVBoxLayout(left_header_widget) # QVBoxLayout pour empiler titre et combo
        left_header_layout.setContentsMargins(0,0,0,0)
        left_header_layout.setSpacing(5)

        self.form_title_label = QLabel("Ajouter un nouvel item Lamicoid")
        self.form_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.form_title_label.setObjectName("CustomFrameTitle")
        left_header_layout.addWidget(self.form_title_label)

        type_lamicoid_combo_container = QWidget()
        type_lamicoid_combo_layout = QHBoxLayout(type_lamicoid_combo_container)
        type_lamicoid_combo_layout.setContentsMargins(0,0,0,0)
        type_lamicoid_label = QLabel("Mode:")
        self.mode_selection_combo = QComboBox()
        self.mode_selection_combo.addItem("--- Sélectionner Mode ---")
        self.mode_selection_combo.addItem("Disposition")
        self.mode_selection_combo.addItem("Modèle")
        self.mode_selection_combo.addItem("Lamicoid")
        self.mode_selection_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        type_lamicoid_combo_layout.addWidget(type_lamicoid_label)
        type_lamicoid_combo_layout.addWidget(self.mode_selection_combo, 1)
        left_header_layout.addWidget(type_lamicoid_combo_container)
        
        left_panel = Frame(header_widget=left_header_widget, parent=self)
        # left_panel.setObjectName("LamicoidFormPanel") # RETIRÉ - Utilise "CustomFrame" de la classe Frame
        left_panel.setFixedWidth(350) 
        
        # Obtenir le layout de contenu du Frame pour y ajouter nos éléments
        left_panel_content_layout = left_panel.get_content_layout()
        # Retirer les marges par défaut du content_layout si elles ne conviennent pas.
        # Frame met déjà des marges (15,10,15,15). Ajuster si besoin.
        # left_panel_content_layout.setContentsMargins(5,5,5,5) # Exemple d'ajustement
        # left_panel_content_layout.setSpacing(8)

        # --- Widget conteneur pour le formulaire d'ITEM Lamicoid ---
        self.item_form_widget = QWidget(self) # Le parent est la LamicoidPage
        item_form_widget_layout = QVBoxLayout(self.item_form_widget)
        item_form_widget_layout.setContentsMargins(0,0,0,0) # Pas de marges pour ce conteneur interne
        item_form_widget_layout.setSpacing(8)

        # Formulaire pour les champs de LamicoidItem (déplacé dans item_form_widget_layout)
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(8)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.form_layout.addRow("Date:", self.date_edit)
        
        self.ref_edit = QLineEdit()
        self.form_layout.addRow("Numéro Réf.:", self.ref_edit)
        
        self.desc_edit = QLineEdit() 
        self.form_layout.addRow("Description:", self.desc_edit)
        
        self.qty_edit = QSpinBox()
        self.qty_edit.setRange(0, 9999)
        self.qty_edit.setValue(1) 
        self.form_layout.addRow("Quantité:", self.qty_edit)
        
        self.material_edit = QLineEdit()
        self.form_layout.addRow("Matériel:", self.material_edit)
        
        item_form_widget_layout.addLayout(self.form_layout) # Ajout du form_layout au layout du widget d'item
        item_form_widget_layout.addStretch(1) 

        # Boutons pour le formulaire d'item (déplacés dans item_form_widget_layout)
        form_buttons_layout = QHBoxLayout()
        self.form_action_button = QPushButton("Ajouter Item") 
        # self.form_action_button.clicked.connect(self._handle_form_action_button) # Connexion dans _connect_signals
        self.form_cancel_button = QPushButton("Annuler")
        # self.form_cancel_button.clicked.connect(self._cancel_edit_mode) # Connexion dans _connect_signals
        self.form_cancel_button.setVisible(False) 

        form_buttons_layout.addStretch()
        form_buttons_layout.addWidget(self.form_cancel_button)
        form_buttons_layout.addWidget(self.form_action_button)
        item_form_widget_layout.addLayout(form_buttons_layout)
        # --- Fin du widget conteneur pour le formulaire d'ITEM Lamicoid ---


        # --- Widget conteneur pour le formulaire de DÉFINITION DE DISPOSITION ---
        self.disposition_definition_widget = QWidget(self) # RENOMMÉ de template_definition_widget
        disposition_definition_layout = QVBoxLayout(self.disposition_definition_widget)
        disposition_definition_layout.setContentsMargins(0,0,0,0)
        disposition_definition_layout.setSpacing(8)

        self.disposition_form_layout = QFormLayout() # RENOMMÉ de template_form_layout
        self.disposition_form_layout.setSpacing(8)
        self.disposition_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.disposition_name_edit = QLineEdit() # RENOMMÉ de template_name_edit
        self.disposition_form_layout.addRow("Nom de la Disposition:", self.disposition_name_edit) 
        
        disposition_definition_layout.addLayout(self.disposition_form_layout)

        # --- Cadre pour la gestion de la grille ---
        self.grid_management_frame = QFrame(self)
        self.grid_management_frame.setObjectName("GridManagementFrame")
        grid_management_layout = QVBoxLayout(self.grid_management_frame)
        grid_management_layout.setContentsMargins(0, 5, 0, 5)
        grid_management_layout.setSpacing(10)

        self.add_row_button = QPushButton("Ajouter Rangée")
        self.add_column_button = QPushButton("Ajouter Colonne")
        self.merge_cells_button = QPushButton("Fusionner Cellules Sélectionnées")
        self.split_cells_button = QPushButton("Défusionner Cellules Sélectionnées")
        self.delete_rows_button = QPushButton("Supprimer Rangée(s) Sélectionnée(s)")
        self.delete_columns_button = QPushButton("Supprimer Colonne(s) Sélectionnée(s)")
        
        grid_management_layout.addWidget(self.add_row_button)
        grid_management_layout.addWidget(self.add_column_button)
        grid_management_layout.addWidget(self.merge_cells_button)
        grid_management_layout.addWidget(self.split_cells_button)
        grid_management_layout.addWidget(self.delete_rows_button)
        grid_management_layout.addWidget(self.delete_columns_button)
        grid_management_layout.addStretch()

        grid_management_layout.addStretch() # Pour pousser les boutons vers le haut s'ils ne remplissent pas tout l'espace

        disposition_definition_layout.addWidget(self.grid_management_frame)
        # --- Fin du cadre pour la gestion de la grille ---

        # --- Cadre pour la Palette de Contenu --- 
        self.content_palette_frame = QFrame(self)
        self.content_palette_frame.setObjectName("ContentPaletteFrame")
        content_palette_layout = QVBoxLayout(self.content_palette_frame)
        content_palette_layout.setContentsMargins(0, 5, 0, 5)
        content_palette_layout.setSpacing(10)

        content_palette_title = QLabel("Contenu Disponible:")
        content_palette_title.setFont(QFont("Arial", 9, QFont.Bold))
        content_palette_layout.addWidget(content_palette_title)

        self.add_text_content_button = QPushButton("Texte")
        self.add_image_content_button = QPushButton("Image")
        self.add_table_content_button = QPushButton("Tableau")

        content_palette_layout.addWidget(self.add_text_content_button)
        content_palette_layout.addWidget(self.add_image_content_button)
        content_palette_layout.addWidget(self.add_table_content_button)
        content_palette_layout.addStretch()

        disposition_definition_layout.addWidget(self.content_palette_frame)
        # --- Fin du cadre pour la Palette de Contenu ---

        # Le Frame pour "Ajouter Zone" est supprimé ici.
        disposition_definition_layout.addStretch(1) # Maintenir un stretch pour pousser les boutons vers le bas

        disposition_buttons_layout = QHBoxLayout() 
        self.save_disposition_button = QPushButton("Sauvegarder Disposition") 
        self.cancel_disposition_button = QPushButton("Annuler Définition") 
        
        disposition_buttons_layout.addStretch()
        disposition_buttons_layout.addWidget(self.cancel_disposition_button)
        disposition_buttons_layout.addWidget(self.save_disposition_button)
        disposition_definition_layout.addLayout(disposition_buttons_layout)
        # --- Fin du widget conteneur pour la DÉFINITION DE DISPOSITION ---

        # --- Widget conteneur pour le formulaire de DÉFINITION DE MODÈLE (Placeholder) ---
        self.model_definition_widget = QWidget(self)
        model_definition_layout = QVBoxLayout(self.model_definition_widget)
        model_definition_layout.setContentsMargins(0,0,0,0)
        model_definition_layout.setSpacing(8)

        self.model_form_layout = QFormLayout()
        self.model_form_layout.setSpacing(8)
        self.model_form_layout.setLabelAlignment(Qt.AlignLeft)

        self.model_name_edit = QLineEdit()
        self.model_form_layout.addRow("Nom du Modèle:", self.model_name_edit)
        self.base_disposition_combo = QComboBox() # Pour choisir la disposition de base
        self.model_form_layout.addRow("Disposition de base:", self.base_disposition_combo)
        
        model_definition_layout.addLayout(self.model_form_layout)
        model_definition_layout.addStretch(1)

        model_buttons_layout = QHBoxLayout()
        self.save_model_button = QPushButton("Sauvegarder Modèle")
        self.cancel_model_button = QPushButton("Annuler Définition")
        model_buttons_layout.addStretch()
        model_buttons_layout.addWidget(self.cancel_model_button)
        model_buttons_layout.addWidget(self.save_model_button)
        model_definition_layout.addLayout(model_buttons_layout)
        # --- Fin du widget conteneur pour la DÉFINITION DE MODÈLE ---

        # Ajout des trois widgets conteneurs de formulaire au layout du panneau de gauche.
        left_panel_content_layout.addWidget(self.item_form_widget)
        left_panel_content_layout.addWidget(self.disposition_definition_widget)
        left_panel_content_layout.addWidget(self.model_definition_widget)

        self.disposition_definition_widget.hide()
        self.model_definition_widget.hide()
        # self.item_form_widget reste visible par défaut
        
        page_layout.addWidget(left_panel)

        # --- Panneau Droit (Liste des items sous forme de cartes) ---
        # Création de l'en-tête pour le panneau droit
        right_header_widget = QWidget()
        right_header_widget.setObjectName("FrameHeaderContainer")
        right_header_layout = QHBoxLayout(right_header_widget)
        right_header_layout.setContentsMargins(0,0,0,0) # Pas de marges pour le widget d'en-tête lui-même
        
        list_title_label = QLabel("Liste des Items Lamicoid")
        list_title_label.setFont(QFont("Arial", 11, QFont.Bold))
        list_title_label.setObjectName("CustomFrameTitle")
        right_header_layout.addWidget(list_title_label)
        right_header_layout.addStretch()
        # On pourrait ajouter un compteur d'items ici, comme dans RapportDepensePage

        right_panel = Frame(header_widget=right_header_widget, parent=self)
        # right_panel.setObjectName("LamicoidListPanel") # RETIRÉ - Utilise "CustomFrame" de la classe Frame
        
        right_panel_content_layout = right_panel.get_content_layout()
        # right_panel_content_layout.setContentsMargins(0,0,0,0) # Ajuster si les marges par défaut de Frame ne vont pas

        # Création du QStackedWidget pour le panneau de droite
        self.right_display_stack = QStackedWidget(self)

        # Page 1: Affichage des items Lamicoid (existant)
        self.lamicoid_display = LamicoidDisplayWidget(self.document, self)
        self.right_display_stack.addWidget(self.lamicoid_display)

        # Page 2: Éditeur de Disposition (pour mode Disposition)
        self.disposition_editor_widget = DispositionEditorWidget(self)
        self.right_display_stack.addWidget(self.disposition_editor_widget)

        # Page 3: Éditeur de Modèle (pour mode Modèle)
        self.model_editor_widget = ModelEditorWidget(self)
        self.right_display_stack.addWidget(self.model_editor_widget)
        
        right_panel_content_layout.addWidget(self.right_display_stack)
        
        self.right_display_stack.setCurrentWidget(self.lamicoid_display)

        page_layout.addWidget(right_panel, 1) 

        # Bouton de sauvegarde global du document
        # Je le déplace hors du panneau droit pour qu'il soit en bas de la page_layout.
        # Ou alors, on le met dans le content_layout du right_panel, mais APRES la scrollArea.
        
        self.save_document_button = QPushButton("Sauvegarder Document Lamicoid")
        self.save_document_button.clicked.connect(self._save_document_clicked)
        # Pour le mettre en bas du panneau de droite, APRES la scroll area :
        right_panel_content_layout.addWidget(self.save_document_button, 0, Qt.AlignBottom)

        # Si on le veut en bas de TOUTE la page (sous les deux panneaux):
        # On créerait un QVBoxLayout global pour page_layout, puis ajouter le bouton après.
        # Pour l'instant, laissons le en bas du panneau droit.
        
        self.setLayout(page_layout)

    def _connect_signals(self):
        self.form_action_button.clicked.connect(self._handle_form_action_button)
        self.form_cancel_button.clicked.connect(self._cancel_edit_mode)
        self.save_document_button.clicked.connect(self._save_document_clicked)
        self.mode_selection_combo.currentTextChanged.connect(self._on_mode_selected)
        self.save_disposition_button.clicked.connect(self._handle_save_disposition_action)
        self.cancel_disposition_button.clicked.connect(self._handle_cancel_disposition_action)
        self.save_model_button.clicked.connect(self._handle_save_model_action)
        self.cancel_model_button.clicked.connect(self._handle_cancel_model_action)

        # Connexions pour les nouveaux boutons de grille
        self.add_row_button.clicked.connect(self._handle_add_row_to_disposition)
        self.add_column_button.clicked.connect(self._handle_add_column_to_disposition)
        self.merge_cells_button.clicked.connect(self._handle_merge_cells_action)
        self.split_cells_button.clicked.connect(self._handle_split_cells_action)
        self.delete_rows_button.clicked.connect(self._handle_delete_selected_rows_action)
        self.delete_columns_button.clicked.connect(self._handle_delete_selected_columns_action)

        # Connexions pour les boutons de la palette de contenu
        self.add_text_content_button.clicked.connect(self._handle_add_text_content_action)
        self.add_image_content_button.clicked.connect(self._handle_add_image_content_action)
        self.add_table_content_button.clicked.connect(lambda: self._handle_add_content_to_cell("tableau"))

    def _clear_form_fields(self):
        self.date_edit.setDate(QDate.currentDate())
        self.ref_edit.clear()
        self.desc_edit.clear()
        self.qty_edit.setValue(1)
        self.material_edit.clear()
        # self.type_lamicoid_combo.setCurrentIndex(0) # On ne réinitialise plus systématiquement le combo ici
                                                    # car l'action peut venir du combo lui-même.

    def _populate_form_fields(self, item: LamicoidItem):
        self.date_edit.setDate(QDate.fromString(item.date_item, "yyyy-MM-dd"))
        self.ref_edit.setText(item.numero_reference or "")
        self.desc_edit.setText(item.description or "")
        self.qty_edit.setValue(item.quantite or 0)
        self.material_edit.setText(item.materiel or "")
        # La sélection du type de Lamicoid pourrait être mise à jour ici si elle était dynamique

    def _enter_edit_mode(self, item: LamicoidItem):
        self.editing_item_id = item.id_item
        self._populate_form_fields(item)
        self.form_title_label.setText("Modifier l'item Lamicoid")
        self.form_action_button.setText("Sauvegarder Item")
        self.form_cancel_button.setVisible(True)
        logger.debug(f"Entrée en mode édition pour item ID: {item.id_item}")
        # Lorsqu'on édite un item, on pourrait essayer de sélectionner son type si cette info était stockée.
        # Pour l'instant, on laisse le combobox de type tel quel.

    def _exit_edit_mode(self):
        self.editing_item_id = None
        self._clear_form_fields()
        self.form_title_label.setText("Ajouter un nouvel item Lamicoid")
        self.form_action_button.setText("Ajouter Item")
        self.form_cancel_button.setVisible(False)
        logger.debug("Sortie du mode édition.")
        # self.type_lamicoid_combo.setCurrentIndex(0) # Pas de réinitialisation ici non plus

    def _cancel_edit_mode(self):
        self._exit_edit_mode()
        self.mode_selection_combo.setCurrentIndex(0) 
        # S'assurer que le formulaire d'item est visible et celui de template caché
        self.disposition_definition_widget.hide()
        self.model_definition_widget.hide()
        self.item_form_widget.show()
        self.form_title_label.setText("Ajouter un nouvel item Lamicoid") # Titre par défaut

    def _on_mode_selected(self, selected_mode: str):
        logger.debug(f"Mode sélectionné: {selected_mode}")
        self._ensure_correct_view_for_mode(selected_mode)
        
        # Logique additionnelle si nécessaire à la sélection d'un mode
        if selected_mode == "Disposition":
            self.disposition_name_edit.clear() # Toujours commencer avec un nom vide pour une nouvelle disposition ? Ou charger ?
        elif selected_mode == "Modèle":
            self.model_name_edit.clear()
            # TODO: Charger la liste des dispositions disponibles dans self.base_disposition_combo
            # Exemple : self.base_disposition_combo.clear(); self.base_disposition_combo.addItems(["Disp1", "Disp2"])
            pass
        elif selected_mode == "Lamicoid":
            # TODO: Peut-être charger une liste de modèles disponibles dans un autre ComboBox (non existant)
            # Pour l'instant, le formulaire d'item est générique.
            pass

    def _handle_form_action_button(self):
        if not self.item_form_widget.isVisible():
            logger.warning("Action de formulaire d'item appelée alors qu'il n'est pas visible.")
            return
        # Logique existante pour ajouter/mettre à jour un LamicoidItem (déjà présente et correcte)
        date_val = self.date_edit.date().toString("yyyy-MM-dd")
        ref_val = self.ref_edit.text().strip()
        desc_val = self.desc_edit.text().strip()
        qty_val = self.qty_edit.value()
        material_val = self.material_edit.text().strip()

        if not ref_val:
            QMessageBox.warning(self, "Champ manquant", "Le numéro de référence est requis pour un Lamicoid.")
            self.ref_edit.setFocus()
            return
        if qty_val <= 0:
            QMessageBox.warning(self, "Valeur invalide", "La quantité doit être supérieure à zéro.")
            self.qty_edit.setFocus()
            return

        try:
            if self.editing_item_id:
                item_to_update = self.document.get_item_by_id(self.editing_item_id)
                if item_to_update:
                    item_to_update.date_item = date_val
                    item_to_update.numero_reference = ref_val
                    item_to_update.description = desc_val
                    item_to_update.quantite = qty_val
                    item_to_update.materiel = material_val
                    self.lamicoid_display.update_display()
                    logger.info(f"Item Lamicoid ID '{self.editing_item_id}' mis à jour.")
                else:
                    logger.error(f"Impossible de trouver l'item ID '{self.editing_item_id}' pour la mise à jour.")
                self._exit_edit_mode()
            else:
                new_item = LamicoidItem(
                    date_item=date_val,
                    numero_reference=ref_val,
                    description=desc_val,
                    quantite=qty_val,
                    materiel=material_val
                )
                self.document.add_item(new_item)
                self.lamicoid_display.update_display()
                logger.info(f"Nouvel item Lamicoid ajouté: {new_item.id_item}")
                self._clear_form_fields()
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout/modification de l'item Lamicoid: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def _handle_delete_item_request(self, item_to_delete: LamicoidItem):
        reply = QMessageBox.question(self, "Confirmation de suppression", 
                                     f"Êtes-vous sûr de vouloir supprimer l'item '{item_to_delete.numero_reference or item_to_delete.id_item}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.document.remove_item(item_to_delete.id_item):
                logger.info(f"Item Lamicoid ID '{item_to_delete.id_item}' supprimé du document.")
                # Retrouver et supprimer la carte de l'UI
                self.lamicoid_display.update_display()
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

    def _handle_global_save_request(self, doc_type: str, file_path: str):
        if self.document and file_path == self.document.file_name:
            logger.info(f"Requête de sauvegarde globale interceptée pour {file_path}, type {doc_type}")
            self._try_save_document(auto=True, show_success_message=False) # Sauvegarde silencieuse

    def _try_save_document(self, auto=False, show_success_message=True):
        if self.document:
            try:
                self.document.save() # Le chemin est déjà dans l'objet document
                logger.info(f"Document Lamicoid '{self.document.file_name}' sauvegardé.")
                if not auto and show_success_message:
                    QMessageBox.information(self, "Sauvegarde", "Document Lamicoid sauvegardé avec succès.")
                self.document_saved_signal.emit(self.document.file_name) # Émettre le signal de sauvegarde
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du document Lamicoid '{self.document.file_name}': {e}")
                if not auto:
                    QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder le document: {e}")
        else:
            logger.warning("Tentative de sauvegarde, mais aucun document Lamicoid n'est chargé.")
            if not auto:
                QMessageBox.warning(self, "Sauvegarde impossible", "Aucun document à sauvegarder.")

    def _handle_save_disposition_action(self):
        disposition_name = self.disposition_name_edit.text().strip()
        if not disposition_name:
            QMessageBox.warning(self, "Nom manquant", "Veuillez donner un nom à la disposition.")
            self.disposition_name_edit.setFocus()
            return
        logger.info(f"Action: Sauvegarder Disposition - Nom: {disposition_name}")
        # disposition_data = self.disposition_editor_widget.get_disposition_data()
        # ... logique de sauvegarde ...
        QMessageBox.information(self, "Disposition", f"Sauvegarde de la disposition '{disposition_name}' (et de ses zones) à implémenter.")
        # Après sauvegarde, on pourrait revenir au mode Lamicoid ou Modèle par défaut
        self.mode_selection_combo.setCurrentIndex(0) # Retour à "--- Sélectionner Mode ---"
        self._ensure_correct_view_for_mode("--- Sélectionner Mode ---")

    def _handle_cancel_disposition_action(self):
        logger.info("Action: Annuler Définition de Disposition")
        self.mode_selection_combo.setCurrentIndex(0) # Retour à "--- Sélectionner Mode ---"
        self._ensure_correct_view_for_mode("--- Sélectionner Mode ---")

    def _handle_save_model_action(self):
        model_name = self.model_name_edit.text().strip()
        base_disposition = self.base_disposition_combo.currentText() # À peupler et valider
        if not model_name:
            QMessageBox.warning(self, "Nom manquant", "Veuillez donner un nom au modèle.")
            self.model_name_edit.setFocus()
            return
        if self.base_disposition_combo.currentIndex() == 0: # Supposant que l'index 0 est un placeholder
            QMessageBox.warning(self, "Disposition manquante", "Veuillez sélectionner une disposition de base pour le modèle.")
            self.base_disposition_combo.setFocus()
            return
        logger.info(f"Action: Sauvegarder Modèle - Nom: {model_name}, Base: {base_disposition}")
        # model_data = self.model_editor_widget.get_model_data()
        # ... logique de sauvegarde ...
        QMessageBox.information(self, "Modèle", f"Sauvegarde du modèle '{model_name}' (basé sur {base_disposition}) à implémenter.")
        self.mode_selection_combo.setCurrentIndex(0) # Retour à "--- Sélectionner Mode ---"
        self._ensure_correct_view_for_mode("--- Sélectionner Mode ---")

    def _handle_cancel_model_action(self):
        logger.info("Action: Annuler Définition de Modèle")
        self.mode_selection_combo.setCurrentIndex(0) # Retour à "--- Sélectionner Mode ---"
        self._ensure_correct_view_for_mode("--- Sélectionner Mode ---")

    def _handle_add_row_to_disposition(self):
        logger.info("Action: Ajouter Rangée à la Disposition")
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            self.disposition_editor_widget.add_row() # Méthode à créer dans DispositionEditorWidget
        else:
            logger.warning("Tentative d'ajouter une rangée alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _handle_add_column_to_disposition(self):
        logger.info("Action: Ajouter Colonne à la Disposition")
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            self.disposition_editor_widget.add_column() # Méthode à créer dans DispositionEditorWidget
        else:
            logger.warning("Tentative d'ajouter une colonne alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _handle_merge_cells_action(self):
        if self.disposition_editor_widget:
            logger.info("Action: Fusionner Cellules")
            self.disposition_editor_widget.merge_selected_cells()
        else:
            logger.warning("Tentative de fusion de cellules sans éditeur de disposition actif.")

    def _handle_split_cells_action(self):
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            logger.info("Action: Défusionner Cellules Sélectionnées")
            self.disposition_editor_widget.split_selected_cells() # Méthode à créer dans DispositionEditorWidget
        else:
            logger.warning("Tentative de défusionner des cellules alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _handle_delete_selected_rows_action(self):
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            selected_cells = self.disposition_editor_widget.selected_cells
            if not selected_cells:
                QMessageBox.information(self, "Suppression Rangées", "Veuillez sélectionner au moins une cellule dans les rangées à supprimer.")
                return
            
            row_indices_to_delete = sorted(list(set(cell.row for cell in selected_cells)), reverse=True)
            logger.info(f"Action: Supprimer Rangées Sélectionnées - Indices: {row_indices_to_delete}")
            self.disposition_editor_widget.delete_rows(row_indices_to_delete)
        else:
            logger.warning("Tentative de supprimer des rangées alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _handle_delete_selected_columns_action(self):
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            selected_cells = self.disposition_editor_widget.selected_cells
            if not selected_cells:
                QMessageBox.information(self, "Suppression Colonnes", "Veuillez sélectionner au moins une cellule dans les colonnes à supprimer.")
                return

            col_indices_to_delete = sorted(list(set(cell.col for cell in selected_cells)), reverse=True)
            logger.info(f"Action: Supprimer Colonnes Sélectionnées - Indices: {col_indices_to_delete}")
            self.disposition_editor_widget.delete_columns(col_indices_to_delete)
        else:
            logger.warning("Tentative de supprimer des colonnes alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _handle_add_text_content_action(self):
        if self.disposition_editor_widget and self.disposition_editor_widget.get_selected_cells_coords():
            selected_coords = self.disposition_editor_widget.get_selected_cells_coords()
            if len(selected_coords) == 1:
                r, c = selected_coords[0]
                
                # Récupérer le texte actuel de la cellule, s'il existe et est de type texte
                current_cell_text = ""
                cell_to_edit = self.disposition_editor_widget.cell_items[r][c]
                if cell_to_edit and cell_to_edit.content_type == "Texte" and cell_to_edit.content_placeholder_item:
                    current_cell_text = cell_to_edit.content_placeholder_item.text()
                    # Si le placeholder actuel est juste "Texte", ne pas le pré-remplir
                    if current_cell_text.lower() == "texte": 
                        current_cell_text = ""

                dialog = TextInputDialog(self, current_text=current_cell_text)
                if dialog.exec_() == QDialog.Accepted:
                    text_to_add = dialog.get_text()
                    if text_to_add is not None: # Peut être une chaîne vide, c'est ok
                        logger.info(f"Action: Ajouter Contenu Texte '{text_to_add}' à la cellule ({r},{c})")
                        # Nous passons maintenant le texte réel à set_cell_content
                        self.disposition_editor_widget.set_cell_content(r, c, "Texte", actual_text=text_to_add)
                    else:
                        # Cas où get_text retourne None (ne devrait pas arriver si Accepted, mais par sécurité)
                        logger.info(f"Action: Ajouter Contenu Texte annulée (pas de texte) pour la cellule ({r},{c})")
                else:
                    logger.info(f"Action: Dialogue d'ajout de texte annulé pour la cellule ({r},{c})")
            else:
                QMessageBox.information(self, "Sélection Multiple", "Veuillez sélectionner une seule cellule pour ajouter du texte.")
        else:
            logger.warning("Tentative d'ajout de contenu de type Texte sans éditeur de disposition actif ou sans sélection.")
            QMessageBox.warning(self, "Action impossible", "Veuillez sélectionner une cellule dans l'éditeur de disposition avant d'ajouter du texte.")

    def _handle_add_image_content_action(self):
        if self.disposition_editor_widget and self.disposition_editor_widget.get_selected_cells_coords():
            selected_coords = self.disposition_editor_widget.get_selected_cells_coords()
            if len(selected_coords) == 1:
                r, c = selected_coords[0]
                logger.info(f"Action: Ajouter Contenu Image à la cellule ({r},{c})")
                # Pour l'instant, utilise "Image" comme placeholder. Une sélection de fichier sera nécessaire.
                self.disposition_editor_widget.set_cell_content(r, c, "Image") 
            else:
                QMessageBox.information(self, "Sélection Multiple", "Veuillez sélectionner une seule cellule pour ajouter une image.")
        else:
            logger.warning("Tentative d'ajout de contenu de type Image sans éditeur de disposition actif ou sans sélection.")
            QMessageBox.warning(self, "Action impossible", "Veuillez sélectionner une cellule dans l'éditeur de disposition avant d'ajouter une image.")

    def _handle_add_content_to_cell(self, content_type: str):
        if self.disposition_editor_widget and self.right_display_stack.currentWidget() == self.disposition_editor_widget:
            selected_cell_items = self.disposition_editor_widget.selected_cells
            if not selected_cell_items:
                QMessageBox.information(self, "Ajout de Contenu", f"Veuillez sélectionner une cellule pour y ajouter du contenu '{content_type}'.")
                return
            if len(selected_cell_items) > 1:
                QMessageBox.information(self, "Ajout de Contenu", "Veuillez sélectionner une seule cellule pour y ajouter du contenu.")
                return
            
            target_cell = list(selected_cell_items)[0]
            # Si la cellule sélectionnée est une esclave d'une fusion, trouver sa maître.
            # Pour l'instant, on assume que la sélection est toujours une cellule maître ou une cellule simple.
            # La logique de _get_cell_merged_state pourrait être utile ici pour trouver la vraie cellule cible.

            logger.info(f"Action: Ajouter contenu '{content_type}' à la cellule ({target_cell.row}, {target_cell.col})")
            self.disposition_editor_widget.set_cell_content(target_cell.row, target_cell.col, content_type)
        else:
            logger.warning(f"Tentative d'ajouter du contenu '{content_type}' alors que l'éditeur de disposition n'est pas actif.")
            QMessageBox.warning(self, "Mode incorrect", "Veuillez être en mode 'Disposition' pour cette action.")

    def _ensure_correct_view_for_mode(self, mode: str):
        self.item_form_widget.hide()
        self.disposition_definition_widget.hide()
        self.model_definition_widget.hide()

        # La gestion de la visibilité de add_zone_frame est supprimée.
        self.grid_management_frame.setVisible(mode == "Disposition") # Afficher/cacher aussi ce cadre
        self.content_palette_frame.setVisible(mode == "Disposition") # Afficher/cacher aussi ce cadre

        if mode == "Disposition":
            self.disposition_definition_widget.show()
            self.disposition_name_edit.setFocus()
            self.form_title_label.setText("Nouvelle/Édition Disposition")
            self.right_display_stack.setCurrentWidget(self.disposition_editor_widget)
            self.disposition_editor_widget.load_disposition() # TODO: Charger la disposition sélectionnée ou une nouvelle
        elif mode == "Modèle":
            self.model_definition_widget.show()
            self.model_name_edit.setFocus()
            self.form_title_label.setText("Nouveau/Édition Modèle")
            self.right_display_stack.setCurrentWidget(self.model_editor_widget)
            # TODO: Charger les dispositions dans self.base_disposition_combo
            # self.model_editor_widget.load_model() # TODO: Charger le modèle sélectionné ou un nouveau
        elif mode == "Lamicoid":
            self.item_form_widget.show()
            # Si on n'est pas en mode édition d'item, clearer le formulaire
            if not self.editing_item_id:
                self._clear_form_fields()
            self.form_title_label.setText("Nouvel Item Lamicoid" if not self.editing_item_id else "Modifier Item Lamicoid")
            self.right_display_stack.setCurrentWidget(self.lamicoid_display)
            self.lamicoid_display.update_display() # S'assurer que l'affichage est à jour
        else: # "--- Sélectionner Mode ---" ou état inconnu
            self.item_form_widget.show() # Par défaut, montrer le formulaire d'item (peut-être vide/désactivé)
            self.form_title_label.setText("Prêt - Sélectionnez un mode")
            self.right_display_stack.setCurrentWidget(self.lamicoid_display)
            self._clear_form_fields()

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