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
        
        self.internal_layout = QVBoxLayout(self) 
        self.internal_layout.setContentsMargins(10, 1, 10, 1)
        self.internal_layout.setSpacing(0) 

        self.title_label = None 
        self.separator_line = None

        if title or (icon_path and os.path.exists(icon_path)) or header_widget:
            title_hbox = QHBoxLayout()
            # Ne pas définir les marges/spacing ici par défaut
            # title_hbox.setContentsMargins(15, 8, 15, 8) 
            # title_hbox.setSpacing(8)

            if header_widget:
                # Ajouter le widget personnalisé SANS marges/spacing supplémentaires du HBox
                title_hbox.setContentsMargins(0, 0, 0, 0) # Forcer 0 marge pour ce HBox
                title_hbox.setSpacing(0) # Forcer 0 spacing pour ce HBox
                title_hbox.addWidget(header_widget, 1) 
            else:
                # Appliquer les marges/spacing UNIQUEMENT pour l'en-tête titre/icône
                title_hbox.setContentsMargins(15, 8, 15, 8) 
                title_hbox.setSpacing(8)
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

    def get_content_layout(self):
        return self.internal_layout

print("ui/components/frame.py défini") # Debug 