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
    QFileDialog
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
from PyQt5.QtGui import QPixmap, QImage, QIcon
# ---------------------------------------
from PyQt5.QtCore import Qt, QUrl, QTimer, QBuffer, QByteArray, QIODevice, QSize, QPoint # Ajout QSize et QPoint

# --- Icon Loader --- 
from utils.icon_loader import get_icon_path
# -----------------

# --- Placeholder Widget --- 
class PagePlaceholder(QWidget):
    """ Widget vide avec une taille fixe et stockant le numéro de page. """
    def __init__(self, page_num, width, height, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.setFixedSize(width, height)
        # Optionnel: ajouter un style pour voir le placeholder
        # self.setStyleSheet("background-color: #444; border: 1px solid #555;")
        self.pixmap_label = None # Label pour afficher le pixmap rendu
        self.setLayout(QVBoxLayout()) # Pour pouvoir ajouter le label plus tard
        self.layout().setContentsMargins(0,0,0,0)
        
    def display_pixmap(self, pixmap):
        if not self.pixmap_label:
            self.pixmap_label = QLabel()
            self.pixmap_label.setAlignment(Qt.AlignCenter)
            # --- S'assurer que le label prend la taille du placeholder --- 
            # self.pixmap_label.setMinimumSize(self.width(), self.height()) # Plus besoin ici
            # Utiliser setScaledContents pour que le pixmap s'adapte au label
            self.pixmap_label.setScaledContents(True) 
            self.layout().addWidget(self.pixmap_label)
            
        # --- Redimensionner le QLabel à la taille actuelle du placeholder --- 
        # Ceci est crucial lors du zoom/dézoom
        self.pixmap_label.setFixedSize(self.size())
        # -----------------------------------------------------------------
        
        self.pixmap_label.setPixmap(pixmap)
        self.pixmap_label.setVisible(True)
        
    def clear_pixmap(self):
        if self.pixmap_label:
             # Cache le label au lieu de le supprimer pour réutilisation
            self.pixmap_label.clear() 
            self.pixmap_label.setVisible(False) 
# ------------------------

class MediaViewer(QDialog):
    """
    Fenêtre modale pour afficher des fichiers image ou PDF (rendus comme images).
    Utilise PyMuPDF pour les PDF avec rendu à la demande (Lazy Rendering).
    Inclut une barre d'outils personnalisée.
    """
    def __init__(self, file_list: list, initial_index: int, parent=None):
        super().__init__(parent)
        if not file_list or not (0 <= initial_index < len(file_list)):
             raise ValueError("Liste de fichiers vide ou index initial invalide.")
        
        self.setModal(True)
        self.resize(900, 700)

        self.file_list = file_list
        self.current_file_index = initial_index
        self.pdf_doc = None
        self.current_zoom = 1.0
        self.zoom_step = 0.1 
        
        # --- Attributs pour Lazy Loading --- 
        self.page_placeholders = [] # Liste des widgets PagePlaceholder
        self.rendered_pixmaps = {} # Cache: {page_num: QPixmap}
        self.visible_pages = set() # Set des numéros de page actuellement visibles
        self._render_timer = QTimer() # Timer pour différer le rendu au scroll
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(150) # Délai en ms avant de rendre après scroll
        self._render_timer.timeout.connect(self._update_visible_pages)
        # ----------------------------------

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # --- Barre d'outils (inchangée) --- 
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 0, 5, 0)
        toolbar_layout.setSpacing(8)
        # ... (création boutons: prev_file, next_file, zoom_out, zoom_in, download)
        self.prev_file_button = QPushButton()
        self.prev_file_button.setIcon(QIcon(get_icon_path("round_arrow_back.png")))
        self.prev_file_button.setToolTip("Fichier précédent")
        self.prev_file_button.setObjectName("ToolBarButton")
        self.prev_file_button.clicked.connect(self._go_to_previous_file)
        toolbar_layout.addWidget(self.prev_file_button)
        self.next_file_button = QPushButton()
        self.next_file_button.setIcon(QIcon(get_icon_path("round_arrow_forward.png")))
        self.next_file_button.setToolTip("Fichier suivant")
        self.next_file_button.setObjectName("ToolBarButton")
        self.next_file_button.clicked.connect(self._go_to_next_file)
        toolbar_layout.addWidget(self.next_file_button)
        toolbar_layout.addSpacing(20)
        self.zoom_out_button = QPushButton()
        self.zoom_out_button.setIcon(QIcon(get_icon_path("round_zoom_out.png")))
        self.zoom_out_button.setToolTip("Zoom arrière")
        self.zoom_out_button.setObjectName("ToolBarButton")
        self.zoom_out_button.clicked.connect(self._zoom_out)
        toolbar_layout.addWidget(self.zoom_out_button)
        self.zoom_in_button = QPushButton()
        self.zoom_in_button.setIcon(QIcon(get_icon_path("round_zoom_in.png")))
        self.zoom_in_button.setToolTip("Zoom avant")
        self.zoom_in_button.setObjectName("ToolBarButton")
        self.zoom_in_button.clicked.connect(self._zoom_in)
        toolbar_layout.addWidget(self.zoom_in_button)
        self.page_info_label = QLabel("")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        self.page_info_label.setMinimumWidth(150) # Un peu plus large pour le texte zoom/page
        toolbar_layout.addWidget(self.page_info_label)
        toolbar_layout.addStretch()
        self.download_button = QPushButton()
        self.download_button.setIcon(QIcon(get_icon_path("round_download.png")))
        self.download_button.setToolTip("Télécharger le fichier actuel")
        self.download_button.setObjectName("ToolBarButton")
        self.download_button.clicked.connect(self._download_file)
        toolbar_layout.addWidget(self.download_button)
        main_layout.addLayout(toolbar_layout)
        # ------------------------------------

        # --- Visionneuse (QScrollArea) --- 
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # Important!
        self.scroll_area.setObjectName("MediaViewerScrollArea")
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        # Connecter le signal de scroll
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        # Widget conteneur pour le contenu
        self.scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(self.scroll_content_widget)
        self.scroll_content_layout.setContentsMargins(0,0,0,0)
        self.scroll_content_layout.setSpacing(5)
        self.scroll_content_layout.setAlignment(Qt.AlignCenter) 
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area, 1)
        # -----------------------------------

        # --- Bouton Fermer (inchangé) --- 
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fermer")
        close_button.setObjectName("TopNavButton")
        close_button.setMinimumWidth(100)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self._load_media() 

    def _clear_previous_content(self):
        """ Vide le contenu actuel et réinitialise les états liés au PDF. """
        # Fermer doc PDF précédent
        if self.pdf_doc:
            try: self.pdf_doc.close()
            except: pass
            self.pdf_doc = None
            
        # Vider layout
        while self.scroll_content_layout.count():
            child = self.scroll_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Réinitialiser listes/cache
        self.page_placeholders = []
        self.rendered_pixmaps = {}
        self.visible_pages = set()

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
            self.page_info_label.setText("Erreur Fichier")
            self.zoom_in_button.setEnabled(False)
            self.zoom_out_button.setEnabled(False)
            self.download_button.setEnabled(False)
            return

        # Mise à jour état barre d'outils
        self.zoom_in_button.setEnabled(self.is_pdf)
        self.zoom_out_button.setEnabled(self.is_pdf and self.current_zoom > self.zoom_step + 0.01)
        self.download_button.setEnabled(True)
        self.prev_file_button.setEnabled(self.current_file_index > 0)
        self.next_file_button.setEnabled(self.current_file_index < len(self.file_list) - 1)
        self.page_info_label.setText("")
        self.page_info_label.setVisible(self.is_pdf)

        if self.is_image:
            pixmap = QPixmap(self.file_path)
            if pixmap.isNull():
                error_label = QLabel("Impossible de charger l'image...")
                self.scroll_content_layout.addWidget(error_label)
            else:
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignCenter)
                self.scroll_content_layout.addWidget(image_label)
                # Ajouter un stretch pour que l'image unique soit centrée verticalement aussi
                self.scroll_content_layout.addStretch()

        elif self.is_pdf:
            if not PYMUPDF_AVAILABLE:
                error_label = QLabel("PyMuPDF requis...")
                self.scroll_content_layout.addWidget(error_label)
                return
            
            try:
                self.pdf_doc = fitz.open(self.file_path)
                self.total_pages = len(self.pdf_doc)
                if self.total_pages == 0:
                    error_label = QLabel("PDF Vide...")
                    self.scroll_content_layout.addWidget(error_label)
                    return

                # --- Création des placeholders --- 
                zoom_matrix = fitz.Matrix(self.current_zoom, self.current_zoom)
                total_height = 0
                for page_num in range(self.total_pages):
                    page = self.pdf_doc.load_page(page_num)
                    rect = page.rect
                    # Calculer taille avec zoom
                    scaled_width = int(rect.width * zoom_matrix.a)
                    scaled_height = int(rect.height * zoom_matrix.d)
                    total_height += scaled_height + self.scroll_content_layout.spacing()
                    
                    placeholder = PagePlaceholder(page_num, scaled_width, scaled_height)
                    self.page_placeholders.append(placeholder)
                    self.scroll_content_layout.addWidget(placeholder)
                # ---------------------------------
                
                # Ajuster la largeur minimale du widget conteneur si nécessaire
                max_width = max(ph.width() for ph in self.page_placeholders) if self.page_placeholders else 400
                self.scroll_content_widget.setMinimumWidth(max_width + 20) # Ajouter marge
                
                # Mettre à jour info page
                self.page_info_label.setText(f"Zoom: {int(self.current_zoom*100)}% ({self.total_pages} pages)")

                # -- Rendre les pages initialement visibles -- 
                # Utiliser QTimer pour s'assurer que le layout est à jour
                QTimer.singleShot(0, self._update_visible_pages) 
                # ------------------------------------------

            except Exception as e:
                QMessageBox.critical(self, "Erreur PDF", f"Impossible d'ouvrir/lire PDF:\n{e}")
                if self.pdf_doc: self.pdf_doc.close(); self.pdf_doc = None
                return

        else:
            error_label = QLabel(f"Type non supporté...")
            self.scroll_content_layout.addWidget(error_label)
            
    # --- Slots et méthodes pour Lazy Loading et Zoom --- 
    def _on_scroll_changed(self, value):
        """ Déclenche la mise à jour des pages visibles après un court délai. """
        # Redémarre le timer à chaque changement de valeur
        self._render_timer.start() 
        
    def _update_visible_pages(self):
        """ Identifie et rend les pages PDF actuellement visibles. """
        if not self.pdf_doc or not self.page_placeholders:
            return

        viewport_rect = self.scroll_area.viewport().rect()
        current_visible_pages = set()
        processed_placeholders = set()

        for i, placeholder in enumerate(self.page_placeholders):
            # Vérifier si le widget placeholder est visible dans le viewport
            placeholder_pos = placeholder.mapTo(self.scroll_area.viewport(), QPoint(0, 0))
            placeholder_rect = placeholder.rect().translated(placeholder_pos)

            if viewport_rect.intersects(placeholder_rect):
                page_num = placeholder.page_num
                current_visible_pages.add(page_num)
                processed_placeholders.add(i)
                
                # Rendre si pas déjà dans le cache ou si le cache est invalide (zoom a changé)
                if page_num not in self.rendered_pixmaps:
                    try:
                        self._render_and_display_page(page_num, placeholder)
                    except Exception as e:
                         print(f"Erreur rendu page {page_num}: {e}") # Log l'erreur
                         # Afficher un message d'erreur sur le placeholder?
            else:
                 # Optionnel: Décharger les pages non visibles du cache
                 page_num = placeholder.page_num
                 if page_num in self.rendered_pixmaps:
                     # print(f"Déchargement page {page_num}") # Debug
                     placeholder.clear_pixmap()
                     del self.rendered_pixmaps[page_num]
                     
        # Mettre à jour l'ensemble des pages visibles
        self.visible_pages = current_visible_pages
        # print(f"Pages visibles: {self.visible_pages}") # Debug
        
    def _render_and_display_page(self, page_num, placeholder):
        """ Rend une page PDF spécifique et l'affiche dans son placeholder. """
        if not self.pdf_doc or page_num < 0 or page_num >= self.total_pages:
             return
             
        # print(f"Rendu page {page_num} au zoom {self.current_zoom}") # Debug
        page = self.pdf_doc.load_page(page_num)
        zoom_matrix = fitz.Matrix(self.current_zoom, self.current_zoom)
        pix = page.get_pixmap(matrix=zoom_matrix, alpha=False)
        
        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        qpixmap = QPixmap.fromImage(qimage)
        
        # Stocker dans le cache
        self.rendered_pixmaps[page_num] = qpixmap 
        
        # Afficher dans le placeholder
        placeholder.display_pixmap(qpixmap)

    def _zoom_in(self):
        new_zoom = self.current_zoom + self.zoom_step
        # Limiter le zoom max si nécessaire
        # if new_zoom > 3.0: return 
        self._apply_zoom(new_zoom)
        
    def _zoom_out(self):
        new_zoom = self.current_zoom - self.zoom_step
        # Limiter le zoom min
        if new_zoom < 0.1: return 
        self._apply_zoom(new_zoom)

    def _apply_zoom(self, new_zoom):
        """ Applique un nouveau niveau de zoom en conservant le point central visible. """
        if not self.pdf_doc or not self.page_placeholders: return
        
        # --- 1. Sauvegarder l'état actuel avant zoom --- 
        old_zoom = self.current_zoom
        viewport = self.scroll_area.viewport()
        scrollbar = self.scroll_area.verticalScrollBar()
        visible_rect = viewport.rect()
        current_scroll_y = scrollbar.value()
        viewport_center_y = current_scroll_y + visible_rect.height() / 2
        
        anchor_page_num = -1
        relative_offset_in_page = 0.5 # Défaut au milieu si aucune page trouvée
        
        cumulative_height = 0
        for placeholder in self.page_placeholders:
            placeholder_height = placeholder.height()
            placeholder_top_y = cumulative_height
            placeholder_bottom_y = placeholder_top_y + placeholder_height
            
            if placeholder_top_y <= viewport_center_y < placeholder_bottom_y:
                anchor_page_num = placeholder.page_num
                if placeholder_height > 0:
                     relative_offset_in_page = (viewport_center_y - placeholder_top_y) / placeholder_height
                break # Page d'ancrage trouvée
            cumulative_height += placeholder_height + self.scroll_content_layout.spacing()
        # ----------------------------------------------

        self.current_zoom = new_zoom
        print(f"Application Zoom: {self.current_zoom}") # Debug
        
        self.rendered_pixmaps = {}
        for placeholder in self.page_placeholders:
             placeholder.clear_pixmap()
        
        # --- 2. Recalculer tailles et trouver nouvelle position ancre --- 
        zoom_matrix = fitz.Matrix(self.current_zoom, self.current_zoom)
        new_anchor_page_top_y = 0
        new_anchor_page_height = 0
        cumulative_height = 0
        max_width = 0
        
        for i, placeholder in enumerate(self.page_placeholders):
            page = self.pdf_doc.load_page(placeholder.page_num)
            rect = page.rect
            scaled_width = int(rect.width * zoom_matrix.a)
            scaled_height = int(rect.height * zoom_matrix.d)
            
            placeholder.setFixedSize(scaled_width, scaled_height) # Redimensionner
            
            # Garder trace de la position de l'ancienne page d'ancrage
            if placeholder.page_num == anchor_page_num:
                 new_anchor_page_top_y = cumulative_height
                 new_anchor_page_height = scaled_height
                 
            cumulative_height += scaled_height + self.scroll_content_layout.spacing()
            if scaled_width > max_width: max_width = scaled_width
        # -------------------------------------------------------------
            
        self.scroll_content_widget.setMinimumWidth(max_width + 20)
        self.page_info_label.setText(f"Zoom: {int(self.current_zoom*100)}% ({self.total_pages} pages)")
        self.zoom_out_button.setEnabled(self.current_zoom > self.zoom_step + 0.01)

        # --- 3. Calculer la nouvelle valeur de scroll --- 
        new_center_target_y = new_anchor_page_top_y + relative_offset_in_page * new_anchor_page_height
        # Recalculer viewport height car la scrollbar peut apparaître/disparaître
        new_viewport_height = viewport.height() 
        target_scroll_y = new_center_target_y - new_viewport_height / 2
        # -------------------------------------------------

        # Re-rendre les pages visibles (différé)
        QTimer.singleShot(0, self._update_visible_pages)
        
        # --- 4. Appliquer la nouvelle valeur de scroll (différé aussi) --- 
        # Utiliser un timer pour s'assurer que la range de la scrollbar est mise à jour
        def adjust_scroll():
            max_scroll = scrollbar.maximum()
            final_scroll_y = max(0, min(int(target_scroll_y), max_scroll))
            scrollbar.setValue(final_scroll_y)
            # print(f"Scroll ajusté à {final_scroll_y} (max: {max_scroll})") # Debug
        QTimer.singleShot(10, adjust_scroll) # Petit délai
        # --------------------------------------------------------------
    # -----------------------------------------------------

    # --- Méthodes de navigation fichier et download (inchangées) --- 
    def _go_to_previous_file(self):
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self._load_media()
    
    def _go_to_next_file(self):
        if self.current_file_index < len(self.file_list) - 1:
            self.current_file_index += 1
            self._load_media()
            
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

    # --- Gestion de la fermeture (inchangée) --- 
    def closeEvent(self, event):
        if self.pdf_doc:
             try: self.pdf_doc.close()
             except: pass
             self.pdf_doc = None
        super().closeEvent(event)
        
    def accept(self):
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None
        super().accept()
        
    def reject(self):
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None
        super().reject()
# ----------------------------------------------------------

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
    # ----------------------------------
    viewer.exec_()

