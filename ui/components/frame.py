# ui/components/frame.py
import os
import logging
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot as Slot
from utils import icon_loader
from utils.signals import signals

logger = logging.getLogger(__name__)

class Frame(QFrame):
    def __init__(self, title=None, icon_base_name=None, header_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomFrame") 
        self.setFrameShape(QFrame.StyledPanel)
        
        # Layout principal qui contiendra l'en-tête, le séparateur ET le layout de contenu
        self.internal_layout = QVBoxLayout(self) 
        self.internal_layout.setContentsMargins(1, 1, 1, 1) # Garder petite marge pour radius
        self.internal_layout.setSpacing(0) 

        self.title_label = None 
        self.separator_line = None

        # --- AJOUT : Stocker infos icône --- 
        self._icon_base_name = icon_base_name 
        self.icon_label = None
        # ----------------------------------

        # --- En-tête (si nécessaire) --- 
        has_header_content = title or self._icon_base_name or header_widget
        
        if has_header_content:
            title_hbox = QHBoxLayout()
            # Appliquer les marges et l'espacement standard de l'en-tête DANS TOUS LES CAS
            title_hbox.setContentsMargins(15, 8, 15, 8) 
            title_hbox.setSpacing(8)
            
            if header_widget:
                # Ajouter le widget personnalisé
                title_hbox.addWidget(header_widget, 1) 
            else:
                if self._icon_base_name: # Utiliser variable stockée
                    absolute_icon_path = icon_loader.get_icon_path(self._icon_base_name) 
                    if os.path.exists(absolute_icon_path):
                        # --- Stocker la référence au QLabel --- 
                        self.icon_label = QLabel()
                        # -------------------------------------
                        pixmap = QPixmap(absolute_icon_path)
                        self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        self.icon_label.setFixedSize(20, 20)
                        title_hbox.addWidget(self.icon_label)
                    else: 
                        logger.warning(f"Icône de Frame '{self._icon_base_name}' non trouvée à {absolute_icon_path}")
                if title:
                    self.title_label = QLabel(title)
                    self.title_label.setObjectName("CustomFrameTitle") 
                    title_hbox.addWidget(self.title_label)
                    
                title_hbox.addStretch()
            self.internal_layout.addLayout(title_hbox) 
            
            # Ajouter le séparateur seulement si un en-tête a été ajouté
            self.separator_line = QFrame()
            self.separator_line.setFrameShape(QFrame.HLine)
            self.separator_line.setObjectName("CustomFrameSeparator")
            self.internal_layout.addWidget(self.separator_line)

        # --- Zone de contenu (toujours créée) --- 
        self.content_layout = QVBoxLayout() 
        # Ajouter des marges/padding PAR DEFAUT pour le contenu?
        # Ces valeurs pourront être modifiées par l'utilisateur du Frame si besoin.
        self.content_layout.setContentsMargins(15, 10, 15, 15) 
        self.content_layout.setSpacing(12) 
        # Ajouter le layout de contenu au layout principal, avec stretch
        self.internal_layout.addLayout(self.content_layout, 1) 

        # --- AJOUT : Connecter le signal de thème --- 
        signals.theme_changed_signal.connect(self.update_theme_icons)
        # -------------------------------------------

    def get_content_layout(self):
        """Retourne le QVBoxLayout destiné au contenu SOUS l'en-tête."""
        return self.content_layout

    # --- AJOUT : Slot pour mettre à jour l'icône --- 
    @Slot(str)
    def update_theme_icons(self, theme_name):
        # Mettre à jour l'icône principale du Frame (si elle existe)
        if self.icon_label and self._icon_base_name:
            try:
                absolute_icon_path = icon_loader.get_icon_path(self._icon_base_name)
                if os.path.exists(absolute_icon_path):
                    pixmap = QPixmap(absolute_icon_path)
                    pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.icon_label.setPixmap(pixmap)
                else:
                    # logger.warning(f"Icon '{self._icon_base_name}' not found during theme update. Path: {absolute_icon_path}")
                    self.icon_label.setPixmap(QPixmap()) # Effacer pixmap si non trouvé
            except Exception as e:
                logger.error(f"Error updating Frame icon '{self._icon_base_name}': {e}")
                self.icon_label.setPixmap(QPixmap())
        
        # Mettre à jour l'icône du bouton d'aide (si ajouté plus tard)
        # ... (code commenté inchangé)
    # ------------------------------------------------------

print("ui/components/frame.py defined with theme update logic.") 