import sys
import os
import shutil

# --- Ajout pour résoudre les imports lors de l'exécution directe --- 
# Calculer le chemin racine du projet (un niveau au-dessus de windows/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajouter la racine au sys.path SI elle n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --------------------------------------------------------------------

# --- Les imports relatifs devraient maintenant fonctionner ---
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, 
    QMessageBox, QApplication, QWidget, QHBoxLayout, QFrame, QSizePolicy,
    QFileDialog, QLineEdit, QGridLayout
)
# ------------------------------------
# --- PyMuPDF Import ---
try:
    import fitz # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None
# ---------------------

# --- QPixmap est à nouveau nécessaire --- 
from PyQt5.QtGui import QPixmap, QImage, QIcon, QIntValidator
# ---------------------------------------
# --- Ajout QEvent et curseurs --- 
from PyQt5.QtCore import Qt, QUrl, QTimer, QBuffer, QByteArray, QIODevice, QSize, QPoint, QRect, QEvent 
# --------------------------------

# --- Icon Loader --- 
from utils.icon_loader import get_icon_path
# -----------------

# --- AJOUT: Theme Loader --- 
from utils.theme import get_theme_vars
# --------------------------

# --- NOUVEAUX Imports --- 
from typing import List, Union
from models.documents.rapport_depense.facture import Facture
# -------------------------

class MediaViewer(QWidget):
    """
    Fenêtre modale pour afficher des fichiers image ou PDF.
    Utilise PyMuPDF pour rendre les pages PDF en haute résolution une fois.
    Le zoom est géré par mise à l'échelle Qt des QLabels.
    Inclut une barre d'outils personnalisée avec navigation de page interactive.
    """
    PDF_RENDER_ZOOM = 1.5 # Facteur de zoom pour le rendu initial des PDF (150%)
    SCROLL_UPDATE_DELAY = 150 # ms délai pour mise à jour page après scroll

    def __init__(self, media_source: Union[str, Facture, List[str]], 
                 initial_index: int = 0, parent=None):
        super().__init__(parent)
        
        self.resize(900, 700)

        # --- TRAITEMENT media_source pour initialiser file_list et current_file_index --- 
        self.file_list = []
        self.current_file_index = 0
        if isinstance(media_source, str):
            if os.path.exists(media_source):
                self.file_list = [media_source]
                self.current_file_index = 0
            else:
                raise FileNotFoundError(f"Le fichier spécifié n'existe pas: {media_source}")
        elif isinstance(media_source, Facture):
            self.file_list = media_source.get_full_paths()
            # Vérifier que l'index initial est valide pour la liste obtenue
            if 0 <= initial_index < len(self.file_list):
                self.current_file_index = initial_index
            elif self.file_list: # Si liste non vide mais index invalide, prendre 0
                print(f"WARN: Index initial {initial_index} invalide pour l'objet Facture, utilisation de l'index 0.")
                self.current_file_index = 0
            # Si la liste est vide, file_list reste [] et current_index 0
        elif isinstance(media_source, list):
            self.file_list = media_source
            if 0 <= initial_index < len(self.file_list):
                self.current_file_index = initial_index
            elif self.file_list:
                print(f"WARN: Index initial {initial_index} invalide pour la liste fournie, utilisation de l'index 0.")
                self.current_file_index = 0
        else:
            raise TypeError("media_source doit être un str (chemin), un objet Facture, ou une List[str].")

        # Validation finale: S'assurer qu'on a au moins un fichier
        if not self.file_list:
            raise ValueError("Aucun fichier valide trouvé dans la source fournie.")
        # -------------------------------------------------------------------------
        
        self.pdf_doc = None
        self.total_pages = 0 
        self.current_zoom = 1.0
        self.zoom_step = 0.1
        
        # --- Nouveaux attributs pour cette approche --- 
        self.page_labels = [] # Liste des QLabel contenant les pages PDF rendues
        self.original_pdf_pixmaps = [] # Liste des QPixmap originaux haute résolution
        self.image_display_label = None 
        self.original_image_pixmap = None 
        
        # --- Attributs pour le Drag-to-Scroll --- 
        self.is_dragging = False
        self.last_drag_pos = QPoint()
        # ----------------------------------------

        # --- Timer pour mise à jour page au scroll --- 
        self._scroll_update_timer = QTimer(self)
        self._scroll_update_timer.setSingleShot(True)
        self._scroll_update_timer.setInterval(self.SCROLL_UPDATE_DELAY)
        self._scroll_update_timer.timeout.connect(self._update_current_page_input)
        # --------------------------------------------

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # --- Barre d'outils --- 
        theme_colors = get_theme_vars() # Récupérer les couleurs du thème
        toolbar_bg_color = theme_colors.get("COLOR_PRIMARY_MEDIUM", "#3a3d40") # Choisir la couleur et fallback
        toolbar_container = QWidget() # Créer un widget conteneur
        toolbar_container.setObjectName("ToolbarContainer") # Donner un nom pour le style

        # --- Définir le style du conteneur ET la transparence des enfants ICI --- 
        # Définir comme chaîne standard, puis formater
        toolbar_style_template = "" # Assignation initiale
        toolbar_style_template = """
            # Conteneur principal avec fond et coins arrondis
            QWidget#ToolbarContainer {{ 
                background-color: {{toolbar_bg_color}};
                border-radius: 4px; /* Remettre le radius ici */
            }}

            /* Widgets internes rendus transparents */
            QWidget#LeftToolbarWidget, 
            QWidget#CentralToolbarWidget, 
            QWidget#RightToolbarWidget {{ 
                background: transparent;
            }}
        """
        toolbar_style = toolbar_style_template.format(toolbar_bg_color=toolbar_bg_color)
        toolbar_container.setStyleSheet(toolbar_style)
        # --- Forcer le clipping par l'arrière-plan stylé --- 
        toolbar_container.setAttribute(Qt.WA_StyledBackground, True)
        # ---------------------------------------------------------------------
        
        # --- UTILISER QGridLayout --- 
        toolbar_layout = QGridLayout(toolbar_container) # <--- CHANGEMENT ICI
        toolbar_layout.setContentsMargins(5, 3, 5, 3) # Ajuster marges internes du conteneur
        toolbar_layout.setSpacing(8)
        
        # --- Layout Gauche --- 
        # --- Widget Gauche --- 
        left_widget = QWidget() 
        left_widget.setObjectName("LeftToolbarWidget")
        left_layout = QHBoxLayout(left_widget) # Ajouter le layout au widget
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(8)
        
        self.prev_file_button = QPushButton()
        self.prev_file_button.setIcon(QIcon(get_icon_path("round_chevron_left.png")))
        self.prev_file_button.setToolTip("Fichier précédent")
        self.prev_file_button.setObjectName("TopNavButton")
        self.prev_file_button.setProperty("class", "TopNavButton")
        self.prev_file_button.clicked.connect(self._go_to_previous_file)
        left_layout.addWidget(self.prev_file_button)
        
        self.next_file_button = QPushButton()
        self.next_file_button.setIcon(QIcon(get_icon_path("round_chevron_right.png")))
        self.next_file_button.setToolTip("Fichier suivant")
        self.next_file_button.setObjectName("TopNavButton")
        self.next_file_button.setProperty("class", "TopNavButton")
        self.next_file_button.clicked.connect(self._go_to_next_file)
        left_layout.addWidget(self.next_file_button)
        
        self.navigation_label = QLabel("Fichier - / -")
        self.navigation_label.setObjectName("NavigationLabel")
        left_layout.addWidget(self.navigation_label)
        # ----------------------------------------------------------

        # --- Widget Central (Sans objectName ni style direct) --- 
        central_controls_widget = QWidget() # Renommé central_widget pour cohérence
        central_controls_widget.setObjectName("CentralToolbarWidget") # Donner un nom pour le style
        central_controls_layout = QHBoxLayout(central_controls_widget)
        central_controls_layout.setContentsMargins(5, 3, 5, 3) # Garder marge interne
        central_controls_layout.setSpacing(8)
        
        # -- Sous-groupe: Zoom --
        self.zoom_out_button = QPushButton()
        self.zoom_out_button.setIcon(QIcon(get_icon_path("round_zoom_out.png")))
        self.zoom_out_button.setToolTip("Zoom arrière")
        self.zoom_out_button.setObjectName("TopNavButton")
        self.zoom_out_button.clicked.connect(self._zoom_out)
        central_controls_layout.addWidget(self.zoom_out_button)
        
        self.zoom_input = QLineEdit("100") 
        self.zoom_input.setFixedWidth(50)
        self.zoom_input.setAlignment(Qt.AlignRight)
        self.zoom_input.setToolTip("Entrez le pourcentage de zoom (ex: 150) et appuyez sur Entrée")
        self.zoom_input.setObjectName("ZoomInput")
        self.zoom_input.returnPressed.connect(self._go_to_entered_zoom)
        central_controls_layout.addWidget(self.zoom_input)
        
        self.zoom_percent_label = QLabel("%")
        self.zoom_percent_label.setObjectName("ZoomPercentLabel")
        central_controls_layout.addWidget(self.zoom_percent_label)
        
        self.zoom_in_button = QPushButton()
        self.zoom_in_button.setIcon(QIcon(get_icon_path("round_zoom_in.png")))
        self.zoom_in_button.setToolTip("Zoom avant")
        self.zoom_in_button.setObjectName("TopNavButton")
        self.zoom_in_button.clicked.connect(self._zoom_in)
        central_controls_layout.addWidget(self.zoom_in_button)

        central_controls_layout.addSpacing(10) # Petit séparateur

        # -- Sous-groupe: Ajustement --
        self.fit_width_button = QPushButton()
        self.fit_width_button.setIcon(QIcon(get_icon_path("round_fit_page_width.png")))
        self.fit_width_button.setToolTip("Ajuster à la largeur")
        self.fit_width_button.setObjectName("TopNavButton")
        self.fit_width_button.clicked.connect(self._fit_to_width)
        central_controls_layout.addWidget(self.fit_width_button)
        
        self.fit_height_button = QPushButton()
        self.fit_height_button.setIcon(QIcon(get_icon_path("round_fit_page_height.png")))
        self.fit_height_button.setToolTip("Ajuster à la hauteur (basé sur la première page pour PDF)")
        self.fit_height_button.setObjectName("TopNavButton")
        self.fit_height_button.clicked.connect(self._fit_to_height)
        central_controls_layout.addWidget(self.fit_height_button)

        self.fit_page_button = QPushButton()
        self.fit_page_button.setIcon(QIcon(get_icon_path("round_fit_screen.png")))
        self.fit_page_button.setToolTip("Ajuster à la page (meilleur ajustement)")
        self.fit_page_button.setObjectName("TopNavButton")
        self.fit_page_button.clicked.connect(self._fit_to_page)
        central_controls_layout.addWidget(self.fit_page_button)

        central_controls_layout.addSpacing(20) # Séparateur

        # -- Sous-groupe: Navigation Page (PDF) --
        self.page_input = QLineEdit("1")
        self.page_input.setFixedWidth(50)
        self.page_input.setAlignment(Qt.AlignRight)
        self.page_input.setToolTip("Entrez le numéro de page et appuyez sur Entrée")
        self.page_input.setObjectName("PageInput")
        self.page_input.returnPressed.connect(self._go_to_entered_page)
        central_controls_layout.addWidget(self.page_input)
        
        self.total_pages_label = QLabel("/ -")
        self.total_pages_label.setObjectName("TotalPagesLabel")
        central_controls_layout.addWidget(self.total_pages_label)
        # ----------------------------------------

        # --- Widget Droit --- 
        right_widget = QWidget()
        right_widget.setObjectName("RightToolbarWidget")
        right_layout = QHBoxLayout(right_widget) # Ajouter le layout au widget
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(8)

        self.download_button = QPushButton()
        self.download_button.setIcon(QIcon(get_icon_path("round_file_download.png")))
        self.download_button.setToolTip("Télécharger le fichier")
        self.download_button.setObjectName("TopNavButton")
        self.download_button.setProperty("class", "TopNavButton")
        self.download_button.clicked.connect(self._download_file)
        right_layout.addWidget(self.download_button)
        # ---------------------------------------------

        # --- Assemblage final de la barre d'outils --- 
        toolbar_layout.addWidget(left_widget, 0, 0, Qt.AlignLeft)             # Widget gauche -> Colonne 0, Aligné à GAUCHE
        toolbar_layout.addWidget(central_controls_widget, 0, 1, Qt.AlignCenter) # Groupe central -> Colonne 1, Aligné au centre
        toolbar_layout.addWidget(right_widget, 0, 2, Qt.AlignRight)           # Widget droite -> Colonne 2, Aligné à droite

        # Définir l'étirement des colonnes pour centrer la colonne 1
        toolbar_layout.setColumnStretch(0, 1) # Colonne gauche prend l'espace
        toolbar_layout.setColumnStretch(1, 0) # Colonne centrale ne s'étire pas (prend sa taille naturelle)
        toolbar_layout.setColumnStretch(2, 1) # Colonne droite prend l'espace
        # ---------------------------------------------
        
        main_layout.addWidget(toolbar_container) 
        # ------------------------------------        

        # --- Visionneuse (QScrollArea) --- 
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # Important!
        self.scroll_area.setObjectName("MediaViewerScrollArea")
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        # --- Installer le filtre d'événements sur le viewport --- 
        self.scroll_area.viewport().installEventFilter(self)
        # --- Définir le curseur initial pour le viewport --- 
        self.scroll_area.viewport().setCursor(Qt.OpenHandCursor)
        # --- Connecter le signal de scroll pour MAJ page --- 
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._handle_scroll_change)
        # -----------------------------------------------------
        self.scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_content_layout.setContentsMargins(0,0,0,0)
        self.scroll_content_layout.setSpacing(5)
        self.scroll_content_layout.setAlignment(Qt.AlignCenter) 
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area, 1)
        # -----------------------------------

        # --- Bouton Fermer --- 
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fermer")
        close_button.setObjectName("TopNavButton")
        close_button.setMinimumWidth(100)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self._load_media() 
        self._update_navigation_state() 

    def _clear_previous_content(self):
        """ Vide le contenu actuel et réinitialise les états liés au PDF. """
        if self.pdf_doc:
            try: self.pdf_doc.close()
            except: pass
            self.pdf_doc = None
            
        # Vider layout
        while self.scroll_content_layout.count():
            child = self.scroll_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # --- Réinitialiser les listes PDF --- 
        self.page_labels = []
        self.original_pdf_pixmaps = []
        self.image_display_label = None
        self.original_image_pixmap = None

    def _load_media(self):
        self.file_path = self.file_list[self.current_file_index]
        self.is_pdf = self.file_path.lower().endswith('.pdf')
        self.is_image = any(self.file_path.lower().endswith(ext) for ext in
                            ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.pbm',
                             '.pgm', '.ppm', '.xbm', '.xpm', '.svg'])
        self.setWindowTitle(f"Visualiseur - {os.path.basename(self.file_path)}")

        self._clear_previous_content()
        
        if not os.path.exists(self.file_path):
            QMessageBox.critical(self, "Erreur Fichier", f"""Le fichier n'a pas été trouvé:
{self.file_path}""")
            self.page_input.setText("-") 
            self.total_pages_label.setText("/ -")
            self.zoom_out_button.setVisible(False)
            self.zoom_input.setVisible(False)
            self.zoom_percent_label.setVisible(False)
            self.zoom_in_button.setVisible(False)
            self.fit_width_button.setVisible(False)
            self.fit_height_button.setVisible(False)
            self.fit_page_button.setVisible(False)
            self.download_button.setEnabled(False)
            self.prev_file_button.setEnabled(self.current_file_index > 0)
            self.next_file_button.setEnabled(self.current_file_index < len(self.file_list) - 1)
            return

        # --- Mise à jour état initial barre d'outils --- 
        can_zoom = self.is_image or self.is_pdf
        # Gérer la visibilité de l'ensemble des contrôles de zoom et fit
        self.zoom_out_button.setVisible(can_zoom)
        self.zoom_input.setVisible(can_zoom)
        self.zoom_percent_label.setVisible(can_zoom)
        self.zoom_in_button.setEnabled(can_zoom)
        self.fit_width_button.setVisible(can_zoom) 
        self.fit_height_button.setVisible(can_zoom) 
        self.fit_page_button.setVisible(can_zoom) # <-- Gérer visibilité
        
        if can_zoom:
             self._update_zoom_input() # Mettre à jour l'input
             # Activer/Désactiver les boutons en fonction des limites
             self._update_zoom_buttons_state()
             
        self.download_button.setEnabled(True)
        self.prev_file_button.setEnabled(self.current_file_index > 0)
        self.next_file_button.setEnabled(self.current_file_index < len(self.file_list) - 1)
        
        # Visibilité inputs Page
        self.page_input.setVisible(self.is_pdf)
        self.total_pages_label.setVisible(self.is_pdf)
        # --------------------------------------------------

        if self.is_image:
            # --- Charger l'image originale --- 
            self.original_image_pixmap = QPixmap(self.file_path)
            if self.original_image_pixmap.isNull():
                error_label = QLabel("Impossible de charger l'image...")
                self.scroll_content_layout.addWidget(error_label)
                self.zoom_out_button.setVisible(False)
                self.zoom_input.setVisible(False)
                self.zoom_percent_label.setVisible(False)
                self.zoom_in_button.setVisible(False)
                self.fit_width_button.setVisible(False)
                self.fit_height_button.setVisible(False)
                self.fit_page_button.setVisible(False)
            else:
                # --- Créer le QLabel pour l'affichage --- 
                self.image_display_label = QLabel()
                self.image_display_label.setAlignment(Qt.AlignCenter)
                self.image_display_label.setScaledContents(True)
                # Ajouter le QLabel au layout
                self.scroll_content_layout.addWidget(self.image_display_label)
                self.scroll_content_layout.addStretch()
                
                # --- Appliquer Fit to Page directement (différé) --- 
                QTimer.singleShot(0, self._fit_to_page)
            # -----------------------------------

        elif self.is_pdf:
            self.page_input.setVisible(True)
            self.total_pages_label.setVisible(True)
            # --- Rendu unique haute résolution --- 
            self._render_all_pdf_pages_high_res()
            if self.page_labels: # Si le rendu a réussi
                 # --- Appliquer Fit to Page directement (différé) --- 
                 QTimer.singleShot(0, self._fit_to_page)
            # ----------------------------------
        else:
             # ... (gestion type non supporté, désactiver zoom)
             error_label = QLabel(f"Type non supporté...")
             self.scroll_content_layout.addWidget(error_label)
             self.zoom_out_button.setVisible(False)
             self.zoom_input.setVisible(False)
             self.zoom_percent_label.setVisible(False)
             self.zoom_in_button.setVisible(False)
             self.fit_width_button.setVisible(False)
             self.fit_height_button.setVisible(False)
             self.fit_page_button.setVisible(False)
             
        # --- AJOUT: Mise à jour état navigation après chargement --- 
        self._update_navigation_state()
        # ---------------------------------------------------------

    # --- NOUVELLE fonction pour le rendu initial PDF --- 
    def _render_all_pdf_pages_high_res(self):
        if not PYMUPDF_AVAILABLE:
             # ... (gestion module manquant)
             return
        try:
            self.pdf_doc = fitz.open(self.file_path)
            self.total_pages = len(self.pdf_doc)
            if self.total_pages == 0:
                 # ... (gestion PDF vide)
                 return
            
            # Configurer nav page
            self.page_input.setText("1")
            self.page_validator = QIntValidator(1, self.total_pages, self.page_input)
            self.page_input.setValidator(self.page_validator)
            self.total_pages_label.setText(f" / {self.total_pages}")
            
            # Matrice pour rendu haute résolution
            render_matrix = fitz.Matrix(self.PDF_RENDER_ZOOM, self.PDF_RENDER_ZOOM)
            max_width = 0
            
            # Vider les listes avant de remplir
            self.page_labels = []
            self.original_pdf_pixmaps = []
            
            for page_num in range(self.total_pages):
                page = self.pdf_doc.load_page(page_num)
                pix = page.get_pixmap(matrix=render_matrix, alpha=False)
                
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                qpixmap_high_res = QPixmap.fromImage(qimage)
                self.original_pdf_pixmaps.append(qpixmap_high_res)
                
                if qpixmap_high_res.width() > max_width:
                     max_width = qpixmap_high_res.width()
                
                # Créer le QLabel
                page_label = QLabel()
                page_label.setAlignment(Qt.AlignCenter)
                page_label.setScaledContents(True) # IMPORTANT pour le zoom Qt
                # Pas besoin de setPixmap ici, _apply_pdf_zoom le fera avec la bonne taille initiale
                self.page_labels.append(page_label)
                self.scroll_content_layout.addWidget(page_label)
                
            self.scroll_content_widget.setMinimumWidth(int(max_width / self.PDF_RENDER_ZOOM) + 20) # Basé sur taille 100%

        except Exception as e:
            # ... (gestion erreur ouverture)
            QMessageBox.critical(self, "Erreur PDF", f"Impossible de rendre le PDF initial:\n{e}")
            if self.pdf_doc: self.pdf_doc.close(); self.pdf_doc = None
            self.total_pages = 0
            self.page_labels = []
            self.original_pdf_pixmaps = []
            # Mettre à jour UI pour erreur
            self.page_input.setVisible(False)
            self.total_pages_label.setVisible(False)
            self.zoom_out_button.setVisible(False)
            self.zoom_input.setVisible(False)
            self.zoom_percent_label.setVisible(False)
            self.zoom_in_button.setVisible(False)
            self.fit_width_button.setVisible(False)
            self.fit_height_button.setVisible(False)
            self.fit_page_button.setVisible(False)
            self.download_button.setEnabled(False)
            return
        finally:
            # Fermer le document après rendu initial car on a les pixmaps
            if self.pdf_doc:
                 try: self.pdf_doc.close(); self.pdf_doc = None
                 except: pass
    # ------------------------------------------------------
    
    # --- Méthode de zoom PDF modifiée (mise à l'échelle Qt) --- 
    def _apply_pdf_zoom(self, new_zoom, anchor_scroll=True):
        if not self.page_labels or not self.original_pdf_pixmaps: return
        
        # --- Sauvegarde ancre VERTICALE --- 
        old_zoom = self.current_zoom
        viewport = self.scroll_area.viewport()
        scrollbar_v = self.scroll_area.verticalScrollBar()
        current_scroll_y = scrollbar_v.value()
        viewport_center_y = current_scroll_y + viewport.height() / 2
        anchor_page_index = -1
        relative_offset_in_page = 0.5
        cumulative_height = 0
        for i, label in enumerate(self.page_labels):
            label_height = label.height()
            label_top_y = cumulative_height
            label_bottom_y = label_top_y + label_height
            if label_top_y <= viewport_center_y < label_bottom_y:
                anchor_page_index = i
                if label_height > 0:
                     relative_offset_in_page = (viewport_center_y - label_top_y) / label_height
                break
            cumulative_height += label_height + self.scroll_content_layout.spacing()
        # -----------------------------------
        
        # --- Sauvegarde ancre HORIZONTALE --- 
        scrollbar_h = self.scroll_area.horizontalScrollBar()
        current_scroll_x = scrollbar_h.value()
        viewport_width = viewport.width()
        viewport_center_x = current_scroll_x + viewport_width / 2
        old_content_width = self.scroll_content_widget.width()
        anchor_x_ratio = 0.5 # Défaut au centre si largeur nulle
        if old_content_width > 0:
             anchor_x_ratio = viewport_center_x / old_content_width
        # ------------------------------------
        
        self.current_zoom = new_zoom
        self._update_zoom_input() 
        self._update_zoom_buttons_state() # <-- Mettre à jour état boutons
        
        # --- Redimensionner tous les QLabels --- 
        new_anchor_page_top_y = 0
        new_anchor_page_height = 0
        cumulative_height = 0
        max_width = 0
        
        for i, label in enumerate(self.page_labels):
            original_pixmap = self.original_pdf_pixmaps[i]
            original_size = original_pixmap.size()
            new_width = int(original_size.width() * (self.current_zoom / self.PDF_RENDER_ZOOM))
            new_height = int(original_size.height() * (self.current_zoom / self.PDF_RENDER_ZOOM))
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            label.setFixedSize(new_width, new_height)
            label.setPixmap(original_pixmap)
            
            if i == anchor_page_index:
                 new_anchor_page_top_y = cumulative_height
                 new_anchor_page_height = new_height
                 
            cumulative_height += new_height + self.scroll_content_layout.spacing()
            if new_width > max_width: max_width = new_width
        # ---------------------------------------
            
        # Mettre à jour la largeur minimale du contenu AVANT d'ajuster le scroll horizontal
        new_content_width = max_width + 20 
        self.scroll_content_widget.setMinimumWidth(new_content_width)
        
        # Mettre à jour les labels/boutons UI
        self.total_pages_label.setText(f" / {self.total_pages}") 
        self.page_input.setText(str(anchor_page_index + 1) if anchor_page_index != -1 else "-") 

        # --- Calcul et application scroll VERTICAL --- 
        new_center_target_y = new_anchor_page_top_y + relative_offset_in_page * new_anchor_page_height
        new_viewport_height = viewport.height()
        target_scroll_y = new_center_target_y - new_viewport_height / 2
        
        # --- Calcul et application scroll HORIZONTAL --- 
        target_center_x = anchor_x_ratio * new_content_width
        # new_viewport_width = viewport.width() # Récupérer à nouveau au cas où la fenêtre a été redim
        target_scroll_x = target_center_x - viewport_width / 2
        # -------------------------------------------

        def adjust_scrollbars():
            # Ajustement Vertical
            max_scroll_v = scrollbar_v.maximum()
            final_scroll_y = max(0, min(int(target_scroll_y), max_scroll_v))
            scrollbar_v.setValue(final_scroll_y)
            # Ajustement Horizontal
            max_scroll_h = scrollbar_h.maximum()
            final_scroll_x = max(0, min(int(target_scroll_x), max_scroll_h))
            scrollbar_h.setValue(final_scroll_x)
            
        QTimer.singleShot(10, adjust_scrollbars) # Utiliser un seul timer
        # --------------------------------------------------------------------------
    
    # --- Modifiée pour accepter new_zoom --- 
    def _apply_image_zoom(self, new_zoom, anchor_scroll=True):
        if not self.image_display_label or not self.original_image_pixmap:
             return
             
        # --- Début du bloc Try/Except principal --- 
        try:
            # --- Mettre à jour self.current_zoom --- 
            self.current_zoom = new_zoom
            # -------------------------------------
            
            # --- Sauvegarde ancre HORIZONTALE --- 
            viewport = self.scroll_area.viewport()
            scrollbar_h = self.scroll_area.horizontalScrollBar()
            current_scroll_x = scrollbar_h.value()
            viewport_width = viewport.width()
            viewport_center_x = current_scroll_x + viewport_width / 2
            old_content_width = self.image_display_label.width()
            anchor_x_ratio = 0.5
            if old_content_width > 0:
                 anchor_x_ratio = viewport_center_x / old_content_width
                 
            # --- Sauvegarde ancre VERTICALE --- 
            scrollbar_v = self.scroll_area.verticalScrollBar()
            current_scroll_y = scrollbar_v.value()
            viewport_height = viewport.height()
            viewport_center_y = current_scroll_y + viewport_height / 2
            old_content_height = self.image_display_label.height()
            anchor_y_ratio = 0.5
            if old_content_height > 0:
                anchor_y_ratio = viewport_center_y / old_content_height
            # -----------------------------------
                 
            original_size = self.original_image_pixmap.size()
            new_width = int(original_size.width() * self.current_zoom)
            new_height = int(original_size.height() * self.current_zoom)
            if new_width <= 0 or new_height <= 0: return
            
            # --- Redimensionner le QLabel --- 
            self.image_display_label.setFixedSize(new_width, new_height)
            self.image_display_label.setPixmap(self.original_image_pixmap) 
            # ------------------------------
            
            # --- Mettre à jour la taille du widget conteneur --- 
            self.scroll_content_widget.setMinimumWidth(new_width)
            # -------------------------------------------------

            # Mettre à jour UI
            self._update_zoom_input() 
            self._update_zoom_buttons_state() 
            self.total_pages_label.setText(f"Zoom: {int(self.current_zoom * 100)}%") 
            
            # --- Calcul scroll HORIZONTAL --- 
            new_content_width = new_width 
            target_center_x = anchor_x_ratio * new_content_width
            target_scroll_x = target_center_x - viewport_width / 2
            
            # --- Calcul scroll VERTICAL --- 
            new_content_height = new_height
            target_center_y = anchor_y_ratio * new_content_height
            target_scroll_y = target_center_y - viewport_height / 2
            # -----------------------------------------

            # --- Encapsuler l'appel au Timer --- 
            try:
                def adjust_scrollbars():
                    # --- Encapsuler le contenu de adjust_scrollbars --- 
                    try:
                        # Ajustement Horizontal
                        max_scroll_h = scrollbar_h.maximum()
                        final_scroll_x = max(0, min(int(target_scroll_x), max_scroll_h))
                        scrollbar_h.setValue(final_scroll_x)
                        # Ajustement Vertical
                        max_scroll_v = scrollbar_v.maximum()
                        final_scroll_y = max(0, min(int(target_scroll_y), max_scroll_v))
                        scrollbar_v.setValue(final_scroll_y)
                    except Exception as e_inner:
                        print(f"ERREUR dans adjust_scrollbars (image): {e_inner}")
                        import traceback
                        traceback.print_exc()
                    # ---------------------------------------------------
                
                QTimer.singleShot(10, adjust_scrollbars)
            except Exception as e_timer:
                print(f"ERREUR lors de la configuration du timer adjust_scrollbars (image): {e_timer}")
                import traceback
                traceback.print_exc()
            # -------------------------------------
                
        except Exception as e_main:
            print(f"ERREUR principale dans _apply_image_zoom: {e_main}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur Interne Zoom Image", f"Une erreur interne est survenue dans _apply_image_zoom:\n{e_main}")
        # --- Fin du bloc Try/Except principal --- 
        # ------------------------------------------

    # --- REINTRODUCTION Slots Zoom Buttons --- 
    def _zoom_in(self):
        max_zoom = 5.0 # Limite max
        new_zoom = self.current_zoom + self.zoom_step
        if new_zoom > max_zoom: 
            new_zoom = max_zoom
            
        if abs(new_zoom - self.current_zoom) > 0.001:
            # --- Mettre à jour self.current_zoom avant l'appel --- 
            # self.current_zoom = new_zoom # Fait maintenant dans _apply_..._zoom
            if self.is_pdf:
                self._apply_pdf_zoom(new_zoom)
            elif self.is_image:
                self._apply_image_zoom(new_zoom) # Passer new_zoom
        
    def _zoom_out(self):
        min_zoom = 0.1 # Limite min
        new_zoom = self.current_zoom - self.zoom_step
        if new_zoom < min_zoom:
            new_zoom = min_zoom
            
        if abs(new_zoom - self.current_zoom) > 0.001:
            # --- Mettre à jour self.current_zoom avant l'appel --- 
            # self.current_zoom = new_zoom # Fait maintenant dans _apply_..._zoom
            if self.is_pdf:
                self._apply_pdf_zoom(new_zoom)
            elif self.is_image:
                self._apply_image_zoom(new_zoom) # Passer new_zoom
    # ----------------------------------
    
    # --- NOUVEAU Helper pour MAJ état boutons zoom --- 
    def _update_zoom_buttons_state(self):
        "Active/Désactive les boutons zoom selon les limites." 
        min_zoom = 0.1
        max_zoom = 5.0
        self.zoom_out_button.setEnabled(self.current_zoom > min_zoom + 0.001)
        self.zoom_in_button.setEnabled(self.current_zoom < max_zoom - 0.001)
    # ------------------------------------------------
    
    # --- Helper pour mettre à jour l'input zoom (inchangé) --- 
    def _update_zoom_input(self):
        "Met à jour le QLineEdit de zoom avec la valeur actuelle." 
        # Bloquer les signaux pour éviter déclenchement _go_to_entered_zoom
        self.zoom_input.blockSignals(True)
        self.zoom_input.setText(str(int(self.current_zoom * 100)))
        self.zoom_input.blockSignals(False)
    # -----------------------------------------------------
    
    # --- Slot pour gérer le zoom entré --- 
    def _go_to_entered_zoom(self):
         "Applique le zoom entré dans le QLineEdit." 
         try:
             zoom_text = self.zoom_input.text().replace('%', '').strip()
             
             # --- Effacer le focus AVANT de traiter --- 
             self.zoom_input.clearFocus()
             # -----------------------------------------
             
             print(f"_go_to_entered_zoom: Valeur lue = {zoom_text}") # Log de test

             zoom_percent = int(zoom_text)
             new_zoom = zoom_percent / 100.0
             
             # --- Validation simple --- 
             min_zoom = 0.1 # 10%
             max_zoom = 5.0 # 500%
             new_zoom = max(min_zoom, min(new_zoom, max_zoom))
             # -----------------------
             
             # --- Réactiver la logique d'application --- 
             # Appliquer si différent du zoom actuel pour éviter recalcul inutile
             if abs(new_zoom - self.current_zoom) > 0.001:
                 # Ne pas mettre à jour self.current_zoom ici, sera fait dans la fonction appelée
                 if self.is_pdf:
                     self._apply_pdf_zoom(new_zoom) # Appel direct pour PDF
                 elif self.is_image:
                     # --- Utiliser QTimer.singleShot pour l'image --- 
                     QTimer.singleShot(0, lambda nz=new_zoom: self._apply_image_zoom(nz))
                     # Note: Le try/except autour de _apply_image_zoom est maintenant DANS la fonction elle-même
                     # ------------------------------------------------
             else:
                 # Même zoom, juste s'assurer que l'input est bien formaté
                 self._update_zoom_input()
             # print(f"_go_to_entered_zoom: Logique d'application du zoom désactivée pour test.") # Supprimer log de test
             # -------------------------------------------
                 
         except ValueError:
             # Entrée invalide, remettre la valeur actuelle
             # print("_go_to_entered_zoom: Erreur de valeur.") # Supprimer log de test
             QMessageBox.warning(self, "Zoom invalide", "Veuillez entrer un nombre entier pour le pourcentage de zoom.")
             self._update_zoom_input() # Remettre l'ancienne valeur
         except Exception as e:
             # Restaurer le contenu du bloc except
             print(f"ERREUR inattendue dans _go_to_entered_zoom: {e}")
             import traceback
             traceback.print_exc()
             QMessageBox.critical(self, "Erreur Interne", f"Une erreur inattendue est survenue:\n{e}")
             self._update_zoom_input()
    # -------------------------------------------

    # --- Méthodes de navigation fichier et download (inchangées) --- 
    def _go_to_previous_file(self):
        """Charge et affiche le fichier précédent dans la liste."""
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self._load_media()
            # Pas besoin d'appeler _update_navigation_state ici si _load_media le fait
            # Sinon, décommenter la ligne suivante :
            # self._update_navigation_state()

    def _go_to_next_file(self):
        """Charge et affiche le fichier suivant dans la liste."""
        if self.current_file_index < len(self.file_list) - 1:
            self.current_file_index += 1
            self._load_media()
            # Pas besoin d'appeler _update_navigation_state ici si _load_media le fait
            # Sinon, décommenter la ligne suivante :
            # self._update_navigation_state()
            
    def _download_file(self):
        current_path = self.file_list[self.current_file_index]
        file_name = os.path.basename(current_path)
        save_path, _ = QFileDialog.getSaveFileName(self, 
                                                  "Télécharger le fichier", 
                                                  file_name,
                                                  f"Fichiers (*{os.path.splitext(file_name)[1]});;Tous les fichiers (*.*)")
        if save_path:
            try:
                shutil.copyfile(current_path, save_path)
                QMessageBox.information(self, "Succès", f"Fichier téléchargé:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de copier:\n{e}")
    # ----------------------------------------------------------

    # --- Gestion de la fermeture (accept/reject deviennent close) --- 
    def closeEvent(self, event):
        # La logique de fermeture du doc PDF reste valide
        if self.pdf_doc:
             try: self.pdf_doc.close()
             except: pass
             self.pdf_doc = None
        super().closeEvent(event)
        
    # --- NOUVEAU Slot pour gérer le signal valueChanged du scroll --- 
    def _handle_scroll_change(self):
        """Redémarre le timer à chaque changement de scroll."""
        if self.is_pdf: # Mettre à jour seulement si PDF
            self._scroll_update_timer.start()
    # --------------------------------------------------------------

    # --- Slot Go To Page modifié --- 
    def _go_to_entered_page(self):
        if not self.page_labels: # Vérifier la nouvelle liste
            return
        try:
            target_page_num = int(self.page_input.text()) - 1
            if 0 <= target_page_num < len(self.page_labels): # Utiliser len(page_labels)
                target_y = 0
                for i, label in enumerate(self.page_labels): # Itérer sur les labels
                    if i == target_page_num:
                        break
                    target_y += label.height() + self.scroll_content_layout.spacing()
                scrollbar = self.scroll_area.verticalScrollBar()
                scrollbar.setValue(target_y)
            else:
                 # Remettre la page actuelle (basé sur scroll)
                 self._update_current_page_input() # Nouvelle petite fonction helper
        except ValueError:
             self._update_current_page_input()
             
    # --- Helper pour mettre à jour l'input page basé sur scroll --- 
    def _update_current_page_input(self):
         if not self.page_labels: return
         # Trouver la page dont le haut est le plus proche du haut de la vue
         scroll_y = self.scroll_area.verticalScrollBar().value()
         current_page_idx = 0
         cumulative_height = 0
         min_diff = float('inf')
         
         for i, label in enumerate(self.page_labels):
              label_top_y = cumulative_height
              diff = abs(scroll_y - label_top_y)
              if diff < min_diff:
                   min_diff = diff
                   current_page_idx = i
              if label_top_y > scroll_y + 5: # Optimisation: arrêter si on dépasse trop
                   break
              cumulative_height += label.height() + self.scroll_content_layout.spacing()
              
         self.page_input.blockSignals(True)
         self.page_input.setText(str(current_page_idx + 1))
         self.page_input.blockSignals(False)
    # ----------------------------------------------------------

    # --- Implémentation du filtre d'événements --- 
    def eventFilter(self, source, event):
        # Vérifier si l'événement provient du viewport de notre QScrollArea
        if source == self.scroll_area.viewport():
            # --- Drag-to-Scroll --- 
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.is_dragging = True
                    self.last_drag_pos = event.globalPos()
                    self.scroll_area.viewport().setCursor(Qt.ClosedHandCursor)
                    return True # Événement géré
            elif event.type() == QEvent.MouseMove:
                if self.is_dragging:
                    delta = event.globalPos() - self.last_drag_pos
                    # Ajuster les barres de défilement
                    h_bar = self.scroll_area.horizontalScrollBar()
                    v_bar = self.scroll_area.verticalScrollBar()
                    h_bar.setValue(h_bar.value() - delta.x())
                    v_bar.setValue(v_bar.value() - delta.y())
                    # Mettre à jour la dernière position
                    self.last_drag_pos = event.globalPos()
                    return True # Événement géré
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton and self.is_dragging:
                    self.is_dragging = False
                    self.scroll_area.viewport().setCursor(Qt.OpenHandCursor)
                    return True # Événement géré
                
            # --- Ctrl + Wheel Zoom --- 
            elif event.type() == QEvent.Wheel:
                if event.modifiers() & Qt.ControlModifier:
                    delta = event.angleDelta().y()
                    if delta > 0:
                        self._zoom_in()
                    elif delta < 0:
                        self._zoom_out()
                    return True # Événement géré, ne pas scroller
                # Si Ctrl n'est pas pressé, laisser l'événement pour le scroll normal
            # -------------------------
                
        # Passer l'événement au gestionnaire par défaut pour les autres cas
        return super().eventFilter(source, event)
    # ----------------------------------------------

    # --- NOUVEAU Slot pour ajuster à la largeur --- 
    def _fit_to_width(self):
        if not (self.is_image or self.is_pdf):
             return
             
        viewport_width = self.scroll_area.viewport().width()
        scrollbar_v = self.scroll_area.verticalScrollBar()
        
        # Marge pour éviter la barre de défilement verticale si elle apparaît
        margin = 0
        if scrollbar_v.isVisible():
             margin = scrollbar_v.width() + self.scroll_area.frameWidth() * 2 # Prendre en compte la bordure aussi
             
        available_width = max(1, viewport_width - margin) # Assurer une largeur > 0
        
        new_zoom = self.current_zoom # Défaut si calcul échoue
        
        try:
            if self.is_image and self.original_image_pixmap:
                original_width = self.original_image_pixmap.width()
                if original_width > 0:
                     new_zoom = available_width / original_width
                
            elif self.is_pdf and self.original_pdf_pixmaps:
                max_original_pdf_width = 0
                for pixmap in self.original_pdf_pixmaps:
                     # Calculer la largeur originale "théorique" (à zoom 1.0)
                     original_page_width = pixmap.width() / self.PDF_RENDER_ZOOM
                     if original_page_width > max_original_pdf_width:
                          max_original_pdf_width = original_page_width
                          
                if max_original_pdf_width > 0:
                     new_zoom = available_width / max_original_pdf_width
            
            # Appliquer les limites de zoom
            min_zoom_limit = 0.1
            max_zoom_limit = 5.0
            new_zoom = max(min_zoom_limit, min(new_zoom, max_zoom_limit))
            
            # Appliquer le nouveau zoom
            if abs(new_zoom - self.current_zoom) > 0.001:
                 if self.is_pdf:
                     self._apply_pdf_zoom(new_zoom)
                 elif self.is_image:
                     self._apply_image_zoom(new_zoom)
                     
        except Exception as e:
             print(f"Erreur dans _fit_to_width: {e}")
             # Ne pas planter, juste ne pas appliquer le zoom
    # ------------------------------------------

    # --- NOUVEAU Slot pour ajuster à la hauteur --- 
    def _fit_to_height(self):
        if not (self.is_image or self.is_pdf):
            return

        viewport_height = self.scroll_area.viewport().height()
        scrollbar_h = self.scroll_area.horizontalScrollBar()
        
        # Marge pour la barre de défilement horizontale
        margin = 0
        if scrollbar_h.isVisible():
            margin = scrollbar_h.height() + self.scroll_area.frameWidth() * 2
            
        available_height = max(1, viewport_height - margin)
        
        new_zoom = self.current_zoom
        
        try:
            if self.is_image and self.original_image_pixmap:
                original_height = self.original_image_pixmap.height()
                if original_height > 0:
                    new_zoom = available_height / original_height
            
            elif self.is_pdf and self.original_pdf_pixmaps:
                # Basé sur la première page
                if len(self.original_pdf_pixmaps) > 0:
                    first_page_pixmap = self.original_pdf_pixmaps[0]
                    original_page_height = first_page_pixmap.height() / self.PDF_RENDER_ZOOM
                    if original_page_height > 0:
                        new_zoom = available_height / original_page_height
            
            # Appliquer limites
            min_zoom_limit = 0.1
            max_zoom_limit = 5.0
            new_zoom = max(min_zoom_limit, min(new_zoom, max_zoom_limit))
            
            # Appliquer
            if abs(new_zoom - self.current_zoom) > 0.001:
                if self.is_pdf:
                    self._apply_pdf_zoom(new_zoom)
                elif self.is_image:
                    self._apply_image_zoom(new_zoom)
                    
        except Exception as e:
            print(f"Erreur dans _fit_to_height: {e}")
    # --------------------------------------------

    # --- NOUVEAU Slot pour ajuster à la page (Best Fit) --- 
    def _fit_to_page(self):
        if not (self.is_image or self.is_pdf):
            return

        viewport = self.scroll_area.viewport()
        viewport_width = viewport.width()
        viewport_height = viewport.height()
        scrollbar_v = self.scroll_area.verticalScrollBar()
        scrollbar_h = self.scroll_area.horizontalScrollBar()
        
        # Calcul des marges potentielles (même si les barres ne sont pas encore visibles)
        v_margin = scrollbar_v.sizeHint().width() + self.scroll_area.frameWidth() * 2
        h_margin = scrollbar_h.sizeHint().height() + self.scroll_area.frameWidth() * 2
        
        # Estimer la largeur/hauteur disponible SANS barres initialement
        available_width = max(1, viewport_width)
        available_height = max(1, viewport_height)
        
        zoom_w = self.current_zoom
        zoom_h = self.current_zoom
        
        try:
            # --- Calcul zoom pour largeur --- 
            content_width = 0
            if self.is_image and self.original_image_pixmap:
                content_width = self.original_image_pixmap.width()
            elif self.is_pdf and self.original_pdf_pixmaps:
                max_w = 0
                for pixmap in self.original_pdf_pixmaps:
                    w = pixmap.width() / self.PDF_RENDER_ZOOM
                    if w > max_w: max_w = w
                content_width = max_w
            
            if content_width > 0:
                # Calcul initial sans marge
                zoom_w_no_margin = available_width / content_width
                # Si ce zoom nécessite une barre V, recalculer avec marge
                estimated_height_at_zoom = (self.original_image_pixmap.height() * zoom_w_no_margin if self.is_image 
                                            else (self.original_pdf_pixmaps[0].height() / self.PDF_RENDER_ZOOM) * zoom_w_no_margin if self.is_pdf else 0)
                if estimated_height_at_zoom > available_height:
                     zoom_w = (available_width - v_margin) / content_width
                else:
                     zoom_w = zoom_w_no_margin
                zoom_w = max(0.01, zoom_w) # Empêcher zoom quasi nul
            # ------------------------------

            # --- Calcul zoom pour hauteur --- 
            content_height = 0
            if self.is_image and self.original_image_pixmap:
                content_height = self.original_image_pixmap.height()
            elif self.is_pdf and self.original_pdf_pixmaps:
                if len(self.original_pdf_pixmaps) > 0:
                    content_height = self.original_pdf_pixmaps[0].height() / self.PDF_RENDER_ZOOM

            if content_height > 0:
                # Calcul initial sans marge
                zoom_h_no_margin = available_height / content_height
                # Si ce zoom nécessite une barre H, recalculer avec marge
                estimated_width_at_zoom = (self.original_image_pixmap.width() * zoom_h_no_margin if self.is_image 
                                           else content_width * zoom_h_no_margin if self.is_pdf else 0)
                if estimated_width_at_zoom > available_width:
                     zoom_h = (available_height - h_margin) / content_height
                else:
                    zoom_h = zoom_h_no_margin
                zoom_h = max(0.01, zoom_h)
            # -----------------------------
            
            # Choisir le plus petit zoom
            new_zoom = min(zoom_w, zoom_h)
            
            # Appliquer limites
            min_zoom_limit = 0.1
            max_zoom_limit = 5.0
            new_zoom = max(min_zoom_limit, min(new_zoom, max_zoom_limit))
            
            # Appliquer
            if abs(new_zoom - self.current_zoom) > 0.001:
                if self.is_pdf:
                    self._apply_pdf_zoom(new_zoom, anchor_scroll=False)
                    # --- Forcer la page à 1 après fit PDF --- 
                    self.page_input.blockSignals(True) # Éviter déclenchement prématuré
                    self.page_input.setText("1")
                    self.page_input.blockSignals(False)
                    # ---------------------------------------
                elif self.is_image:
                    self._apply_image_zoom(new_zoom, anchor_scroll=False)

        except Exception as e:
            print(f"Erreur dans _fit_to_page: {e}")
    # ---------------------------------------------------

    # --- NOUVEAU Helper pour mettre à jour l'état de navigation --- 
    def _update_navigation_state(self):
        """Met à jour le label de navigation et l'état des boutons Préc/Suivant."""
        total_files = len(self.file_list)
        if total_files > 0:
            self.navigation_label.setText(f"Fichier {self.current_file_index + 1} / {total_files}")
            # Activer/Désactiver bouton Précédent
            self.prev_file_button.setEnabled(self.current_file_index > 0)
            # Activer/Désactiver bouton Suivant
            self.next_file_button.setEnabled(self.current_file_index < total_files - 1)
        else:
            # Cas où la liste serait vide (ne devrait pas arriver avec la validation __init__)
            self.navigation_label.setText("Fichier - / -")
            self.prev_file_button.setEnabled(False)
            self.next_file_button.setEnabled(False)
    # ---------------------------------------------------------------------

# Exemple d'utilisation (pour test seulement)
if __name__ == '__main__':
    # --- Le code de modification de sys.path a été déplacé en haut ---
    # -------------------------------------------------------------
    
    app = QApplication(sys.argv)

    # --- Mettre à jour pour utiliser une liste --- 
    # test_file = r"C:\Users\etienne.mg\Downloads\test.pdf" # Ancien
    test_files = [
        r"C:\Users\etienne.mg\Downloads\test.pdf",
        r"C:\Users\etienne.mg\Downloads\Media.jpg", # Ajouter un autre fichier image/pdf
        r"C:\Users\etienne.mg\Downloads\autre.pdf"  # Et un autre
    ]
    initial_idx = 0
    # ------------------------------------------

    # --- Vérifier la liste et l'index --- 
    valid_files = [f for f in test_files if f and os.path.exists(f)]
    if not valid_files:
         msgBox = QMessageBox()
         msgBox.setIcon(QMessageBox.Warning)
         msgBox.setText("Aucun fichier de test valide trouvé.")
         msgBox.setInformativeText("Veuillez éditer le fichier media_viewer.py et spécifier des chemins valides dans la liste 'test_files' à la fin du fichier pour lancer ce test.")
         msgBox.setWindowTitle("Erreur de Test")
         msgBox.setStandardButtons(QMessageBox.Ok)
         msgBox.exec_()
         sys.exit(1)
    # Assurer que l'index est valide pour la liste filtrée
    if not (0 <= initial_idx < len(valid_files)):
        initial_idx = 0
    # ------------------------------------

    # --- Passer la liste et l'index --- 
    viewer = MediaViewer(valid_files, initial_idx)
    # --- Afficher la fenêtre non modale --- 
    viewer.show()
    # --- Garder l'application en cours d'exécution --- 
    sys.exit(app.exec_())
    # --------------------------------------------

 