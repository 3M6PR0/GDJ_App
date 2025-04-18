import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem,
    QSizePolicy, QLineEdit, QGridLayout, QFormLayout, QComboBox, QStyleOption # QStyleOption importé ici
)
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, pyqtProperty, QEasingCurve, QPropertyAnimation, pyqtSignal
# QFont, QPainter, QPen, QBrush retirés (SimpleToggle gardé mais stylisé par QSS)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QPen, QPalette # Rajouter les imports nécessaires pour SimpleToggle.paintEvent

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

# --- Classe PreferencesPage (Nettoyée) --- 
class PreferencesPage(QWidget):
    select_signature_requested = pyqtSignal()
    save_prefs_requested = pyqtSignal()
    import_prefs_requested = pyqtSignal()
    export_prefs_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreferencesPageWidget")
        self.init_ui()

    def init_ui(self):
        prefs_main_layout = QGridLayout(self)
        prefs_main_layout.setSpacing(15)
        prefs_main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Utiliser le composant Frame importé
        try: 
            from ui.components.frame import Frame
        except ImportError:
            print("ERREUR: Impossible d'importer ui.components.frame.Frame")
            Frame = QFrame 
            Frame.get_content_layout = lambda s: QVBoxLayout(s)
        
        # --- Section "Mon profile" ---
        profile_box = Frame(title="Mon profile", icon_path="resources/icons/clear/round_account_box.png")
        box_content_layout_prof = profile_box.get_content_layout()
        profile_form_layout = QFormLayout()
        profile_form_layout.setContentsMargins(15, 10, 15, 15)
        profile_form_layout.setSpacing(10)
        profile_form_layout.setVerticalSpacing(12)
        
        self.le_nom = QLineEdit(placeholderText="Entrez votre nom") # Style via QSS
        profile_form_layout.addRow(self._create_form_label("Nom:"), self.le_nom)
        self.le_prenom = QLineEdit(placeholderText="Entrez votre prénom") # Style via QSS
        profile_form_layout.addRow(self._create_form_label("Prénom:"), self.le_prenom)
        self.le_tel = QLineEdit(placeholderText="XXX-XXX-XXXX") # Style via QSS
        profile_form_layout.addRow(self._create_form_label("Numéro de téléphone:"), self.le_tel)
        self.le_courriel = QLineEdit(placeholderText="nom@example.com") # Style via QSS
        profile_form_layout.addRow(self._create_form_label("Courriel:"), self.le_courriel)
        
        # Widget Signature
        signature_widget_container = QWidget()
        # setStyleSheet supprimé
        signature_layout = QHBoxLayout(signature_widget_container)
        signature_layout.setContentsMargins(0, 0, 0, 0)
        signature_layout.setSpacing(5)
        btn_plus_signature = QPushButton("+")
        btn_plus_signature.setObjectName("PlusButton") # Style via QSS
        btn_plus_signature.setFixedSize(24, 24)
        btn_plus_signature.clicked.connect(self.select_signature_requested.emit)
        self.signature_image_label = QLabel()
        self.signature_image_label.setObjectName("SignaturePreviewLabel") # ID pour QSS
        self.signature_image_label.setMinimumHeight(24)
        # setStyleSheet supprimé
        self.signature_image_label.setAlignment(Qt.AlignCenter)
        self.signature_image_label.setText("...")
        signature_layout.addWidget(btn_plus_signature)
        signature_layout.addWidget(self.signature_image_label, 1)
        profile_form_layout.addRow(self._create_form_label("Signature Numerique:"), signature_widget_container)
        
        box_content_layout_prof.addLayout(profile_form_layout)
        box_content_layout_prof.addStretch(1)
        prefs_main_layout.addWidget(profile_box, 0, 0)

        # --- Section "Jacmar" ---
        jacmar_box = Frame(title="Jacmar", icon_path="resources/icons/clear/round_corporate_fare.png")
        box_content_layout_jac = jacmar_box.get_content_layout()
        jacmar_form_layout = QFormLayout()
        jacmar_form_layout.setContentsMargins(15, 10, 15, 15)
        jacmar_form_layout.setSpacing(10)
        jacmar_form_layout.setVerticalSpacing(12)
        self.cb_emplacement = QComboBox() # Style via QSS
        self.cb_emplacement.addItems(["Jacmar", "Autre..."])
        jacmar_form_layout.addRow(self._create_form_label("Emplacement:"), self.cb_emplacement)
        self.cb_dept = QComboBox() # Style via QSS
        self.cb_dept.addItems(["Ingénierie", "Production", "Ventes", "..."])
        jacmar_form_layout.addRow(self._create_form_label("Département:"), self.cb_dept)
        self.cb_titre = QComboBox() # Style via QSS
        self.cb_titre.addItems(["Chargé de projet", "Technicien", "Directeur", "..."])
        jacmar_form_layout.addRow(self._create_form_label("Titre:"), self.cb_titre)
        self.cb_super = QComboBox() # Style via QSS
        self.cb_super.addItems(["Personne A", "Personne B", "..."])
        jacmar_form_layout.addRow(self._create_form_label("Superviseur:"), self.cb_super)
        self.cb_plafond = QComboBox() # Style via QSS
        self.cb_plafond.addItems(["Standard", "Élevé", "Aucun", "..."])
        jacmar_form_layout.addRow(self._create_form_label("Plafond de déplacement:"), self.cb_plafond)
        box_content_layout_jac.addLayout(jacmar_form_layout)
        box_content_layout_jac.addStretch(1)
        prefs_main_layout.addWidget(jacmar_box, 0, 1)

        # --- Section "Application" ---
        app_box = Frame(title="Application", icon_path="resources/icons/clear/round_category.png")
        box_content_layout_app = app_box.get_content_layout()
        app_form_layout = QFormLayout()
        app_form_layout.setContentsMargins(15, 10, 15, 15)
        app_form_layout.setSpacing(10)
        app_form_layout.setVerticalSpacing(12)
        self.cb_theme = QComboBox() # Style via QSS
        self.cb_theme.addItems(["Sombre (Défaut)", "Clair", "Système"])
        app_form_layout.addRow(self._create_form_label("Thème:"), self.cb_theme)
        self.toggle_auto_update = SimpleToggle() # Style via QSS sur SimpleToggle
        app_form_layout.addRow(self._create_form_label("Mise a jour automatique:"), self._wrap_widget_in_hbox(self.toggle_auto_update))
        self.toggle_show_notes = SimpleToggle() # Style via QSS sur SimpleToggle
        app_form_layout.addRow(self._create_form_label("Afficher la note de version:"), self._wrap_widget_in_hbox(self.toggle_show_notes))
        box_content_layout_app.addLayout(app_form_layout)
        box_content_layout_app.addStretch(1)
        prefs_main_layout.addWidget(app_box, 1, 0)

        # --- Section "Gestion des preferences" ---
        mgmt_box = Frame(title="Gestion des preferences", icon_path="resources/icons/clear/round_smart_button.png")
        box_content_layout_mgmt = mgmt_box.get_content_layout()
        prefs_form_layout = QFormLayout()
        prefs_form_layout.setContentsMargins(15, 10, 15, 15)
        prefs_form_layout.setSpacing(10)
        prefs_form_layout.setVerticalSpacing(12)
        
        self.btn_export = self._create_icon_button("resources/icons/clear/round_file_download.png", "Exporter les préférences")
        self.btn_export.clicked.connect(self.export_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Exporter:"), self.btn_export)
        
        self.btn_import = self._create_icon_button("resources/icons/clear/round_file_upload.png", "Importer les préférences")
        self.btn_import.clicked.connect(self.import_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Importer:"), self.btn_import)
        
        self.btn_save = self._create_icon_button("resources/icons/clear/round_save.png", "Sauvegarder les préférences")
        self.btn_save.clicked.connect(self.save_prefs_requested.emit)
        prefs_form_layout.addRow(self._create_form_label("Sauvegarder:"), self.btn_save)
        
        box_content_layout_mgmt.addLayout(prefs_form_layout)
        box_content_layout_mgmt.addStretch(1)
        prefs_main_layout.addWidget(mgmt_box, 1, 1)

        prefs_main_layout.setRowStretch(2, 1)
        prefs_main_layout.setColumnStretch(2, 1)
        
        # Appel à apply_styles supprimé

    def _create_form_label(self, text):
        label = QLabel(text)
        label.setObjectName("FormLabel") # ID pour style QSS
        # setStyleSheet supprimé
        return label

    def _wrap_widget_in_hbox(self, widget):
        container = QWidget()
        # Rendre ce conteneur spécifique transparent
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addStretch(1)
        return container

    def _create_icon_button(self, icon_path, tooltip):
        btn = QPushButton("")
        btn.setObjectName("FormButton") # ID pour style QSS
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(20, 20))
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        return btn

    def update_signature_preview(self, pixmap=None, error_text=None):
        if not self.signature_image_label:
            return
        if error_text:
            self.signature_image_label.setText(error_text)
            self.signature_image_label.setVisible(True)
        elif pixmap and not pixmap.isNull():
            label_size = self.signature_image_label.size()
            if not label_size.isValid() or label_size.height() < 10:
                label_size = QSize(100, 30)
                self.signature_image_label.setMinimumSize(label_size)
            scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.signature_image_label.setPixmap(scaled_pixmap)
            self.signature_image_label.setText("")
            self.signature_image_label.setVisible(True)
        else:
            self.signature_image_label.setText("...")
            self.signature_image_label.setVisible(True)

    # Méthode _create_dashboard_box supprimée (remplacée par Frame)
    # Méthode apply_styles supprimée

print("PreferencesPage (dans pages/preferences/) defined") 