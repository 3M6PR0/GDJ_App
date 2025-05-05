from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel, 
                             QPushButton, QSizePolicy, QSpacerItem, QHBoxLayout)
# --- Retirer QProgressBar, importer CircularProgressBar --- 
# from PyQt5.QtWidgets import QProgressBar
from ui.components.progressbar import CircularProgressBar 
from PyQt5.QtCore import Qt, QSize
import logging # AJOUT

# Importer le composant Frame personnalisé
from ui.components.frame import Frame 

logger = logging.getLogger('GDJ_App') # OBTENIR LE LOGGER

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        
        self._setup_ui()
        logger.debug("SettingsPage initialisée.") # Utiliser logger

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Pas de marges externes

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("SettingsScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame) # Pas de bordure pour le scroll area

        scroll_content = QWidget()
        scroll_content.setObjectName("SettingsScrollContent")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20) # Marges internes
        content_layout.setSpacing(15)
        content_layout.setAlignment(Qt.AlignTop)

        # --- Section Mise à jour ---
        self.update_frame = Frame(title="Mise à jour", icon_base_name="round_update.png")
        frame_content_layout = self.update_frame.get_content_layout()
        frame_content_layout.setContentsMargins(15, 10, 15, 15)
        frame_content_layout.setSpacing(20)

        # --- Créer le layout horizontal principal (SANS parent ici) ---
        update_main_hbox = QHBoxLayout()
        # update_main_hbox.setContentsMargins(0, 0, 0, 0) # Pas besoin ici, géré par frame_content_layout
        # update_main_hbox.setSpacing(20) # Idem

        # --- Partie Gauche: Informations Textuelles ---
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(8)
        # --- FORCER L'ALIGNEMENT À GAUCHE --- 
        info_vbox.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # --- Widgets état "Idle" ---
        self.lbl_current_version = QLabel("Version actuelle : -")
        self.lbl_update_status = QLabel("Statut : Prêt") 
        self.btn_check_updates = QPushButton("Vérifier les mises à jour")
        # --- Utiliser l'objectName des boutons de navigation --- 
        self.btn_check_updates.setObjectName("TopNavButton")
        self.btn_check_updates.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        
        # --- Widgets état "Téléchargement" --- 
        # (Labels seulement, la barre ira à droite)
        self.lbl_speed = QLabel("Vitesse : - MB/s")
        self.lbl_speed.setObjectName("UpdateSpeedLabel")
        # self.lbl_speed.setAlignment(Qt.AlignLeft) # Aligner à gauche par défaut
        self.lbl_speed.setVisible(False)
        
        # Labels pour détails (Téléchargé / Restant)
        self.lbl_downloaded_label = QLabel("Téléchargé")
        self.lbl_downloaded_label.setObjectName("UpdateDetailLabel")
        self.lbl_downloaded_value = QLabel("- / - MB")
        self.lbl_downloaded_value.setObjectName("UpdateDetailValue")
        self.downloaded_details_widget = QWidget()
        # --- Rendre le fond transparent --- 
        self.downloaded_details_widget.setStyleSheet("background-color: transparent;")
        dl_layout = QHBoxLayout(self.downloaded_details_widget)
        dl_layout.setContentsMargins(0,0,0,0); dl_layout.setSpacing(5)
        dl_layout.addWidget(self.lbl_downloaded_label)
        dl_layout.addWidget(self.lbl_downloaded_value, 1) # Donner l'espace au label de valeur
        self.downloaded_details_widget.setVisible(False)

        self.lbl_remaining_label = QLabel("Durée restante")
        self.lbl_remaining_label.setObjectName("UpdateDetailLabel")
        self.lbl_remaining_value = QLabel("Calcul...")
        self.lbl_remaining_value.setObjectName("UpdateDetailValue")
        self.remaining_details_widget = QWidget()
        # --- Rendre le fond transparent --- 
        self.remaining_details_widget.setStyleSheet("background-color: transparent;")
        rl_layout = QHBoxLayout(self.remaining_details_widget)
        rl_layout.setContentsMargins(0,0,0,0); rl_layout.setSpacing(5)
        rl_layout.addWidget(self.lbl_remaining_label)
        rl_layout.addWidget(self.lbl_remaining_value, 1)
        self.remaining_details_widget.setVisible(False)

        # Bouton Annuler/Arrêter
        self.btn_cancel_update = QPushButton("ARRÊTER")
        # --- Utiliser le même objectName ---
        self.btn_cancel_update.setObjectName("TopNavButton")
        self.btn_cancel_update.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.btn_cancel_update.setVisible(False)

        # Assemblage partie gauche (Info VBox)
        info_vbox.addWidget(self.lbl_current_version)
        info_vbox.addWidget(self.lbl_update_status) 
        info_vbox.addSpacing(10)
        # --- Ajouter les widgets de téléchargement cachés ---
        info_vbox.addWidget(self.lbl_speed)
        info_vbox.addWidget(self.downloaded_details_widget)
        info_vbox.addWidget(self.remaining_details_widget)
        info_vbox.addSpacing(10)
        info_vbox.addStretch(1) # Pousser les boutons vers le bas
        
        # --- AJOUTER LES DEUX BOUTONS À LA FIN --- 
        info_vbox.addWidget(self.btn_check_updates) # Visible par défaut
        info_vbox.addWidget(self.btn_cancel_update) # Caché par défaut
        
        update_main_hbox.addLayout(info_vbox, 1) 

        # --- Partie Droite: Barre de Progression Circulaire ---
        self.progress_bar = CircularProgressBar()
        self.progress_bar.setObjectName("UpdateProgressBar")
        self.progress_bar.setMinimumSize(120, 120)
        self.progress_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # Taille fixe
        self.progress_bar.setVisible(False) # Caché initialement
        
        # Centrer verticalement la barre
        progress_vbox = QVBoxLayout()
        progress_vbox.addStretch()
        progress_vbox.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        progress_vbox.addStretch()
        # --- AJOUT MARGE DROITE --- 
        progress_vbox.setContentsMargins(0, 0, 50, 0) # 0 left, 0 top, 20 right, 0 bottom

        update_main_hbox.addLayout(progress_vbox, 0) 

        # --- Ajouter notre layout horizontal au layout du Frame --- 
        frame_content_layout.addLayout(update_main_hbox)

        content_layout.addWidget(self.update_frame)

        # --- Ajouter d'autres sections ici si besoin ---
        # Exemple :
        # self.other_frame = Frame(title="Autre Section")
        # other_layout = QVBoxLayout(self.other_frame.get_content_widget())
        # ... widgets ...
        # content_layout.addWidget(self.other_frame)

        # Ajouter un espace en bas pour éviter que le dernier frame colle au bord
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        logger.info("SettingsPage UI initialized with update progress elements") 