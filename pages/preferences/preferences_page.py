import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem,
    QSizePolicy, QLineEdit, QGridLayout, QFormLayout, QComboBox, QStyleOption, QGraphicsOpacityEffect # QStyleOption importé ici
)
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtProperty, QEasingCurve, QPropertyAnimation, pyqtSignal, QEvent, pyqtSlot as Slot
# QFont, QPainter, QPen, QBrush retirés (SimpleToggle gardé mais stylisé par QSS)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QPalette # Rajouter les imports nécessaires pour SimpleToggle.paintEvent
import functools # Importer functools

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path
from utils import icon_loader # <-- AJOUT DE L'IMPORT
# --- AJOUT IMPORT --- 
from utils.signals import signals 
# -------------------

# Constantes de couleur/police supprimées

# --- SimpleToggle (Nettoyé) ---
# Le style est maintenant géré par QSS global ciblant SimpleToggle
class SimpleToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 22)
        self.setCursor(Qt.PointingHandCursor)
        self.checked = False
        # Couleurs définies via QSS

    def isChecked(self):
        return self.checked

    def setChecked(self, checked):
        if self.checked == checked:
            return
        self.checked = checked
        self.toggled.emit(self.checked)
        self.update() # Déclenche paintEvent

    def toggle(self):
        self.setChecked(not self.isChecked())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        # Le dessin est toujours nécessaire, mais les couleurs viendront 
        # de la feuille de style appliquée à ce widget.
        # Nous devons récupérer les couleurs depuis la palette actuelle.
        painter = QPainter(self) # Créer QPainter ICI
        painter.setRenderHint(QPainter.Antialiasing)
        
        opt = QStyleOption()
        opt.initFrom(self)
        
        height = self.height()
        width = self.width()
        # Remis: Calcul du rayon pour le fond
        radius = height / 2 
        handle_radius = (height - 6) // 2
        handle_diameter = 2 * handle_radius
        
        painter.setPen(Qt.NoPen)
        
        # Récupérer les couleurs de la palette pour le CERCLE ET LE RAIL
        palette = self.palette()
        # Remis: bg_color pour le rail
        bg_color = palette.color(QPalette.Highlight) if self.checked else palette.color(QPalette.Dark)
        handle_color = palette.color(QPalette.BrightText)
        
        # Remis: Dessiner le rectangle de fond (le rail)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), radius, radius)
        
        # Dessiner le cercle (handle)
        painter.setBrush(QBrush(handle_color))
        padding = 3
        handle_x = padding if not self.checked else width - handle_diameter - padding
        handle_rect = QRect(handle_x, padding, handle_diameter, handle_diameter)
        painter.drawEllipse(handle_rect)

# --- Nouveau Widget Personnalisé --- 
class SignaturePreviewWidget(QWidget):
    clicked = pyqtSignal() # Signal émis au clic

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap() # Pixmap à afficher
        self.setMinimumHeight(50) # Hauteur minimale
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Cliquez pour choisir une image de signature")
        # Le fond sera hérité ou défini par QSS via son nom d'objet
        self.setObjectName("SignaturePreviewWidget") 

    def setPixmap(self, pixmap):
        if pixmap is None:
            self._pixmap = QPixmap() # Créer un QPixmap vide
        else:
            self._pixmap = pixmap
        self.update() # Demander un redessin

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # --- Dessiner le fond ARRONDI --- 
        bg_color = self.palette().color(QPalette.Base)
        radius = 4.0 # Utiliser la valeur de notre setStyleSheet (4px)
        painter.setPen(Qt.NoPen) # Pas de contour pour le fond
        painter.setBrush(QBrush(bg_color)) # Définir la couleur de remplissage
        painter.drawRoundedRect(rect, radius, radius) # Dessiner le rectangle arrondi

        if self._pixmap.isNull():
            # Dessiner "..." si pas d'image
            painter.setPen(self.palette().color(QPalette.Text))
            painter.drawText(rect, Qt.AlignCenter, "Cliquez ici...")
        else:
            # Calculer la taille et la position du pixmap redimensionné
            target_rect = rect.adjusted(2, 2, -2, -2) # Petit padding
            scaled_pixmap = self._pixmap.scaled(target_rect.size(), 
                                                Qt.KeepAspectRatio, 
                                                Qt.SmoothTransformation)
            # Centrer le pixmap dans la zone
            x = target_rect.x() + (target_rect.width() - scaled_pixmap.width()) / 2
            y = target_rect.y() + (target_rect.height() - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

# --- Classe PreferencesPage (Modifiée) --- 
class PreferencesPage(QWidget):
    """Page principale des préférences utilisateur.

    Contient les sections pour le profil utilisateur, les options Jacmar,
    les paramètres généraux et l'apparence. Gère l'affichage des champs,
    la prévisualisation de la signature, et les boutons d'action (Sauvegarder, etc.).
    Le style des composants est géré par des feuilles de style QSS externes.

    Signals:
        select_signature_requested: Demande l'ouverture du dialogue de sélection de signature.
        save_prefs_requested: Demande la sauvegarde des préférences actuelles.
        import_prefs_requested: Demande l'importation de préférences.
        export_prefs_requested: Demande l'exportation de préférences.
    """
    select_signature_requested = pyqtSignal()
    save_prefs_requested = pyqtSignal()
    import_prefs_requested = pyqtSignal()
    export_prefs_requested = pyqtSignal()
    # Signal pour indiquer qu'un champ doit être réinitialisé (optionnel, on peut tout gérer dans le contrôleur)
    # field_revert_requested = pyqtSignal(str) # Le nom du champ à réinitialiser

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreferencesPageWidget")
        self.input_widgets = {}
        self.refresh_buttons = {}
        self.refresh_effects = {}
        # --- AJOUT : Dictionnaire pour boutons thème --- 
        self._theme_aware_buttons = {}
        # ---------------------------------------------
        self.init_ui()
        # --- AJOUT : Connecter signal thème --- 
        signals.theme_changed_signal.connect(self._update_button_icons)
        # --------------------------------------

    def init_ui(self):
        prefs_main_layout = QGridLayout(self)
        prefs_main_layout.setSpacing(15)
        prefs_main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Utiliser le composant Frame importé
        try: 
            from ui.components.frame import Frame
        except ImportError:
            Frame = QFrame 
            Frame.get_content_layout = lambda s: QVBoxLayout(s)
        
        # --- Section "Mon profile" ---
        profile_box = Frame(title="Mon profile", icon_base_name="round_account_box.png")
        box_content_layout_prof = profile_box.get_content_layout()
        profile_form_layout = QFormLayout()
        profile_form_layout.setContentsMargins(15, 10, 15, 15)
        profile_form_layout.setSpacing(10)
        profile_form_layout.setVerticalSpacing(12)
        
        # Création des champs avec leurs boutons refresh
        self.le_nom = QLineEdit(placeholderText="Entrez votre nom")
        profile_form_layout.addRow(self._create_form_label("Nom:"), self._wrap_widget_with_refresh(self.le_nom, "profile.nom"))
        
        self.le_prenom = QLineEdit(placeholderText="Entrez votre prénom")
        profile_form_layout.addRow(self._create_form_label("Prénom:"), self._wrap_widget_with_refresh(self.le_prenom, "profile.prenom"))
        
        self.le_tel = QLineEdit(placeholderText="XXX-XXX-XXXX")
        profile_form_layout.addRow(self._create_form_label("Téléphone:"), self._wrap_widget_with_refresh(self.le_tel, "profile.telephone"))
        
        self.le_courriel = QLineEdit(placeholderText="nom@example.com")
        profile_form_layout.addRow(self._create_form_label("Courriel:"), self._wrap_widget_with_refresh(self.le_courriel, "profile.courriel"))
        
        # Widget Signature
        self.signature_display_widget = SignaturePreviewWidget()
        # --- REMETTRE le setStyleSheet pour le fond et radius --- 
        self.signature_display_widget.setStyleSheet("""
            QWidget#SignaturePreviewWidget {
                background-color: #555555; /* Gris moyen */
                border-radius: 4px; 
                border: 1px solid #777777; /* Optionnel */
            }
        """)
        self.signature_display_widget.clicked.connect(self.select_signature_requested.emit)
        
        # L'ajouter via la méthode wrap pour inclure le bouton refresh
        profile_form_layout.addRow(self._create_form_label("Signature:"), 
                                   self._wrap_widget_with_refresh(self.signature_display_widget, "profile.signature_path"))
        
        box_content_layout_prof.addLayout(profile_form_layout)
        box_content_layout_prof.addStretch(1)
        prefs_main_layout.addWidget(profile_box, 0, 0)

        # --- Section "Jacmar" ---
        jacmar_box = Frame(title="Jacmar", icon_base_name="round_corporate_fare.png")
        box_content_layout_jac = jacmar_box.get_content_layout()
        jacmar_form_layout = QFormLayout()
        jacmar_form_layout.setContentsMargins(15, 10, 15, 15)
        jacmar_form_layout.setSpacing(10)
        jacmar_form_layout.setVerticalSpacing(12)
        
        # Créer les ComboBox vides ici
        self.cb_emplacement = QComboBox()
        jacmar_form_layout.addRow(self._create_form_label("Emplacement:"), self._wrap_widget_with_refresh(self.cb_emplacement, "jacmar.emplacement"))
        
        self.cb_dept = QComboBox()
        jacmar_form_layout.addRow(self._create_form_label("Département:"), self._wrap_widget_with_refresh(self.cb_dept, "jacmar.departement"))
        
        self.cb_titre = QComboBox()
        jacmar_form_layout.addRow(self._create_form_label("Titre:"), self._wrap_widget_with_refresh(self.cb_titre, "jacmar.titre"))
        
        self.cb_super = QComboBox()
        jacmar_form_layout.addRow(self._create_form_label("Superviseur:"), self._wrap_widget_with_refresh(self.cb_super, "jacmar.superviseur"))
        
        self.cb_plafond = QComboBox()
        jacmar_form_layout.addRow(self._create_form_label("Plafond de déplacement:"), self._wrap_widget_with_refresh(self.cb_plafond, "jacmar.plafond"))
        
        box_content_layout_jac.addLayout(jacmar_form_layout)
        box_content_layout_jac.addStretch(1)
        prefs_main_layout.addWidget(jacmar_box, 0, 1)

        # --- Section "Application" ---
        app_box = Frame(title="Application", icon_base_name="round_category.png")
        box_content_layout_app = app_box.get_content_layout()
        app_form_layout = QFormLayout()
        app_form_layout.setContentsMargins(15, 10, 15, 15)
        app_form_layout.setSpacing(10)
        app_form_layout.setVerticalSpacing(12)
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["Clair", "Sombre"])
        app_form_layout.addRow(self._create_form_label("Thème:"), self._wrap_widget_with_refresh(self.cb_theme, "application.theme"))
        self.toggle_auto_update = SimpleToggle()
        app_form_layout.addRow(self._create_form_label("Mise à jour auto:"), self._wrap_widget_with_refresh(self.toggle_auto_update, "application.auto_update"))
        self.toggle_show_notes = SimpleToggle()
        app_form_layout.addRow(self._create_form_label("Afficher la note de version:"), self._wrap_widget_with_refresh(self.toggle_show_notes, "application.show_note"))
        box_content_layout_app.addLayout(app_form_layout)
        box_content_layout_app.addStretch(1)
        prefs_main_layout.addWidget(app_box, 1, 0)

        # --- Section "Gestion des preferences" ---
        mgmt_box = Frame(title="Gestion des preferences", icon_base_name="round_smart_button.png")
        box_content_layout_mgmt = mgmt_box.get_content_layout()
        prefs_form_layout = QFormLayout()
        prefs_form_layout.setContentsMargins(15, 10, 15, 15)
        prefs_form_layout.setSpacing(10)
        prefs_form_layout.setVerticalSpacing(12)
        
        self.btn_export = self._create_icon_button("round_file_download.png", "Exporter les préférences")
        self.btn_export.clicked.connect(self.export_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Exporter:"), self.btn_export)
        # --- AJOUT : Stocker bouton action thème --- 
        self._theme_aware_buttons[self.btn_export] = "round_file_download.png"
        # -------------------------------------------
        
        self.btn_import = self._create_icon_button("round_file_upload.png", "Importer les préférences")
        self.btn_import.clicked.connect(self.import_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Importer:"), self.btn_import)
        # --- AJOUT : Stocker bouton action thème --- 
        self._theme_aware_buttons[self.btn_import] = "round_file_upload.png"
        # -------------------------------------------
        
        self.btn_save = self._create_icon_button("round_save.png", "Sauvegarder les préférences")
        self.btn_save.clicked.connect(self.save_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Sauvegarder:"), self.btn_save)
        # --- AJOUT : Stocker bouton action thème --- 
        self._theme_aware_buttons[self.btn_save] = "round_save.png"
        # -------------------------------------------
        
        box_content_layout_mgmt.addLayout(prefs_form_layout)
        box_content_layout_mgmt.addStretch(1)
        prefs_main_layout.addWidget(mgmt_box, 1, 1)

        # --- CORRECTION : Appliquer le stretch aux bonnes lignes/colonnes --- 
        prefs_main_layout.setRowStretch(0, 1) # Ligne 0
        prefs_main_layout.setRowStretch(1, 1) # Ligne 1
        prefs_main_layout.setColumnStretch(0, 1) # Colonne 0
        prefs_main_layout.setColumnStretch(1, 1) # Colonne 1
        # -------------------------------------------------------------------
        
        # Appel à apply_styles supprimé

    def _create_form_label(self, text):
        label = QLabel(text)
        label.setObjectName("FormLabel") # ID pour style QSS
        # setStyleSheet supprimé
        return label

    def _wrap_widget_in_hbox(self, widget):
        # Ancienne méthode gardée pour compatibilité si appelée ailleurs, mais dépréciée
        # pour les champs principaux
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addStretch(1)
        return container

    def _wrap_widget_with_refresh(self, input_widget, pref_path):
        """Crée un container QHBoxLayout avec le widget d'entrée et un bouton refresh invisible via opacité.
           Fonctionne avec QLineEdit, QComboBox, SimpleToggle, et SignaturePreviewWidget.
        """
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # S'assurer que le widget principal prend de la place
        size_policy = input_widget.sizePolicy()
        size_policy.setHorizontalStretch(1)
        input_widget.setSizePolicy(size_policy)
        layout.addWidget(input_widget, 1)

        # --- Utiliser icon_loader pour le bouton refresh ---
        # Passer seulement le nom de base à _create_icon_button
        refresh_button = self._create_icon_button("round_refresh.png", 
                                                  f"Réinitialiser {pref_path.split('.')[-1]}...")
        # --------------------------------------------------
        refresh_button.setObjectName(f"refresh_{pref_path.replace('.', '_')}")
        refresh_button.setFixedSize(20, 20)
        refresh_button.setIconSize(QSize(16, 16))

        # Utiliser l'effet d'opacité
        opacity_effect = QGraphicsOpacityEffect(refresh_button)
        opacity_effect.setOpacity(0.0) # Invisible par défaut
        refresh_button.setGraphicsEffect(opacity_effect)
        layout.addWidget(refresh_button, 0)

        # Stocker les références
        self.input_widgets[pref_path] = input_widget
        self.refresh_buttons[pref_path] = refresh_button
        self.refresh_effects[pref_path] = opacity_effect
        # --- AJOUT : Stocker bouton refresh thème --- 
        self._theme_aware_buttons[refresh_button] = "round_refresh.png"
        # --------------------------------------------

        return container

    def _create_icon_button(self, icon_base_name, tooltip):
        """Crée un bouton avec une icône chargée via icon_loader.""" # Doc mise à jour
        btn = QPushButton("")
        btn.setObjectName("FormButton")
        # --- Utiliser icon_loader ici --- 
        absolute_icon_path = icon_loader.get_icon_path(icon_base_name) 
        btn.setIcon(QIcon(absolute_icon_path))
        btn.setIconSize(QSize(20, 20)) # Garder cette taille ?
        btn.setFixedSize(30, 30)      # Garder cette taille ?
        btn.setToolTip(tooltip)
        return btn
    # -----------------------------------------------------------

    def update_signature_preview(self, pixmap=None, error_text=None):
        # Met à jour le pixmap dans notre widget personnalisé
        if error_text:
             self.signature_display_widget.setPixmap(None) # Effacer l'image
        else:
            self.signature_display_widget.setPixmap(pixmap) # Mettre à jour le pixmap (None si vide)
            
    # --- Méthodes pour le contrôleur ---
    def get_input_widget(self, pref_path):
        return self.input_widgets.get(pref_path)

    def get_refresh_button(self, pref_path):
        return self.refresh_buttons.get(pref_path)

    def get_refresh_effect(self, pref_path):
        """Retourne l'effet d'opacité associé au bouton refresh."""
        return self.refresh_effects.get(pref_path)

    def get_all_pref_paths(self):
        return list(self.input_widgets.keys())

    def populate_jacmar_combos(self, emplacements, departements, titres, superviseurs, plafonds):
        """Remplit les ComboBox de la section Jacmar avec les listes fournies."""
        self.cb_emplacement.clear()
        self.cb_emplacement.addItems(emplacements if emplacements else ["N/A"])
        
        self.cb_dept.clear()
        self.cb_dept.addItems(departements if departements else ["N/A"])
        
        self.cb_titre.clear()
        self.cb_titre.addItems(titres if titres else ["N/A"])
        
        self.cb_super.clear()
        self.cb_super.addItems(superviseurs if superviseurs else ["N/A"])
        
        self.cb_plafond.clear()
        # Utiliser les clés extraites pour les plafonds
        self.cb_plafond.addItems(plafonds if plafonds else ["N/A"])

    # --- AJOUT : Slot pour maj icones boutons --- 
    @Slot(str)
    def _update_button_icons(self, theme_name):
        for button, icon_base_name in self._theme_aware_buttons.items():
            if not button: continue # Sécurité
            try:
                new_icon_path = icon_loader.get_icon_path(icon_base_name)
                new_icon = QIcon(new_icon_path)
                if not new_icon.isNull():
                    button.setIcon(new_icon)
                else:
                    # Fallback si icône non trouvée (même par défaut)
                    button.setIcon(QIcon())
                    button.setText("?") # Ou autre placeholder
            except Exception as e:
                button.setIcon(QIcon())
                button.setText("?")
    # ---------------------------------------------

print("PreferencesPage (dans pages/preferences/) defined") 