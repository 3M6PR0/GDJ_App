# ui/components/frame.py
import os
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt # Ajout pour Qt.KeepAspectRatio etc.

class Frame(QFrame):
    def __init__(self, title=None, icon_path=None, header_widget: QWidget = None, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomFrame") 
        self.setFrameShape(QFrame.StyledPanel)
        
        # Layout principal qui contiendra l'en-tête, le séparateur ET le layout de contenu
        self.internal_layout = QVBoxLayout(self) 
        self.internal_layout.setContentsMargins(1, 1, 1, 1) # Garder petite marge pour radius
        self.internal_layout.setSpacing(0) 

        self.title_label = None 
        self.separator_line = None

        # --- En-tête (si nécessaire) --- 
        if title or (icon_path and os.path.exists(icon_path)) or header_widget:
            title_hbox = QHBoxLayout()
            # Appliquer les marges et l'espacement standard de l'en-tête DANS TOUS LES CAS
            title_hbox.setContentsMargins(15, 8, 15, 8) 
            title_hbox.setSpacing(8)
            
            if header_widget:
                # Ajouter le widget personnalisé
                title_hbox.addWidget(header_widget, 1) 
            else:
                # Ajouter titre/icône par défaut
                if icon_path and os.path.exists(icon_path):
                    icon_label = QLabel()
                    pixmap = QPixmap(icon_path)
                    icon_label.setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    icon_label.setFixedSize(20, 20)
                    title_hbox.addWidget(icon_label)
                elif icon_path: 
                     print(f"Avertissement: Icône non trouvée à {icon_path}")

                if title:
                    self.title_label = QLabel(title)
                    self.title_label.setObjectName("CustomFrameTitle") 
                    title_hbox.addWidget(self.title_label)
                    
                title_hbox.addStretch()
            self.internal_layout.addLayout(title_hbox) 
            
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

    def get_content_layout(self):
        """Retourne le QVBoxLayout destiné au contenu SOUS l'en-tête."""
        return self.content_layout

print("ui/components/frame.py défini") # Debug 