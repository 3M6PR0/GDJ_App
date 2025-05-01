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
    QFileDialog, QLineEdit
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
from PyQt5.QtCore import Qt, QUrl, QTimer, QBuffer, QByteArray, QIODevice, QSize, QPoint, QRect # Ajout QRect

# --- Icon Loader --- 
from utils.icon_loader import get_icon_path
# -----------------

class MediaViewer(QDialog):
    """
    Fenêtre modale pour afficher des fichiers image ou PDF.
    Utilise PyMuPDF pour rendre les pages PDF en haute résolution une fois.
    Le zoom est géré par mise à l'échelle Qt des QLabels.
    Inclut une barre d'outils personnalisée avec navigation de page interactive.
    """
    PDF_RENDER_ZOOM = 1.5 # Facteur de zoom pour le rendu initial des PDF (150%)
    SCROLL_UPDATE_DELAY = 150 # ms délai pour mise à jour page après scroll

    def __init__(self, file_list: list, initial_index: int, parent=None):
        super().__init__(parent)
        if not file_list or not (0 <= initial_index < len(file_list)):
             raise ValueError("Liste de fichiers vide ou index initial invalide.")
        
        self.setModal(True)
        self.resize(900, 700)

        self.file_list = file_list
        self.current_file_index = initial_index
        self.pdf_doc = None
        self.total_pages = 0 
        self.current_zoom = 1.0
        self.zoom_step = 0.1
        
        # --- Nouveaux attributs pour cette approche --- 
        self.page_labels = [] # Liste des QLabel contenant les pages PDF rendues
        self.original_pdf_pixmaps = [] # Liste des QPixmap originaux haute résolution
        self.image_display_label = None 
        self.original_image_pixmap = None 
        
        # --- Timer pour mise à jour page au scroll --- 
        self._scroll_update_timer = QTimer(self)
        self._scroll_update_timer.setSingleShot(True)
        self._scroll_update_timer.setInterval(self.SCROLL_UPDATE_DELAY)
        self._scroll_update_timer.timeout.connect(self._update_current_page_input)
        # --------------------------------------------

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
        
        # --- Remplacement du Label Page par Input + Label Total --- 
        self.page_input = QLineEdit("1") # Input pour numéro de page
        self.page_input.setFixedWidth(50) # Largeur fixe
        self.page_input.setAlignment(Qt.AlignRight)
        self.page_input.setToolTip("Entrez le numéro de page et appuyez sur Entrée")
        self.page_input.setObjectName("PageInput") # Pour style QSS
        # Ajouter un validateur sera fait dans _load_media quand on connait total_pages
        self.page_input.returnPressed.connect(self._go_to_entered_page)
        toolbar_layout.addWidget(self.page_input)

        self.total_pages_label = QLabel("/ -") # Label pour le total
        self.total_pages_label.setObjectName("TotalPagesLabel")
        toolbar_layout.addWidget(self.total_pages_label)
        
        # Cacher ces widgets par défaut
        self.page_input.setVisible(False)
        self.total_pages_label.setVisible(False)
        # ----------------------------------------------------------
        
        toolbar_layout.addStretch() # Pousse le reste (download) vers la droite
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
        # --- Connecter le signal de scroll --- 
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._handle_scroll_change)
        # --------------------------------------
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
            self.zoom_in_button.setEnabled(False)
            self.zoom_out_button.setEnabled(False)
            self.download_button.setEnabled(False)
            self.prev_file_button.setEnabled(self.current_file_index > 0)
            self.next_file_button.setEnabled(self.current_file_index < len(self.file_list) - 1)
            return

        # --- Mise à jour état initial barre d'outils (Zoom activé pour Image ou PDF) --- 
        can_zoom = self.is_image or self.is_pdf
        self.zoom_in_button.setEnabled(can_zoom)
        self.zoom_out_button.setEnabled(can_zoom and self.current_zoom > self.zoom_step + 0.01)
        self.download_button.setEnabled(True)
        self.prev_file_button.setEnabled(self.current_file_index > 0)
        self.next_file_button.setEnabled(self.current_file_index < len(self.file_list) - 1)
        self.page_input.setVisible(False)
        self.total_pages_label.setVisible(False)
        # ------------------------------------------------------------------------------

        if self.is_image:
            # --- Charger l'image originale --- 
            self.original_image_pixmap = QPixmap(self.file_path)
            if self.original_image_pixmap.isNull():
                error_label = QLabel("Impossible de charger l'image...")
                self.scroll_content_layout.addWidget(error_label)
                self.zoom_in_button.setEnabled(False) # Désactiver zoom si erreur
                self.zoom_out_button.setEnabled(False)
            else:
                # --- Créer le QLabel pour l'affichage --- 
                self.image_display_label = QLabel()
                self.image_display_label.setAlignment(Qt.AlignCenter)
                # Appliquer le zoom initial à l'image
                self._apply_image_zoom()
                # Ajouter le QLabel au layout
                self.scroll_content_layout.addWidget(self.image_display_label)
                self.scroll_content_layout.addStretch()
                # Mettre à jour l'info (fait dans _apply_image_zoom)
            # -----------------------------------

        elif self.is_pdf:
            self.page_input.setVisible(True)
            self.total_pages_label.setVisible(True)
            # --- Rendu unique haute résolution --- 
            self._render_all_pdf_pages_high_res()
            # Appliquer le zoom initial (qui redimensionne les labels)
            if self.page_labels: # Si le rendu a réussi
                 self._apply_pdf_zoom(1.0)
            # ----------------------------------
        else:
             # ... (gestion type non supporté, désactiver zoom)
             error_label = QLabel(f"Type non supporté...")
             self.scroll_content_layout.addWidget(error_label)
             self.zoom_in_button.setEnabled(False)
             self.zoom_out_button.setEnabled(False)
             self.page_input.setVisible(False)
             self.total_pages_label.setVisible(False)
             
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
            self.zoom_in_button.setEnabled(False)
            self.zoom_out_button.setEnabled(False)
            return
        finally:
            # Fermer le document après rendu initial car on a les pixmaps
            if self.pdf_doc:
                 try: self.pdf_doc.close(); self.pdf_doc = None
                 except: pass
    # ------------------------------------------------------
    
    # --- Méthode de zoom PDF modifiée (mise à l'échelle Qt) --- 
    def _apply_pdf_zoom(self, new_zoom):
        if not self.page_labels or not self.original_pdf_pixmaps: return
        
        # --- Sauvegarde ancre (presque inchangé) --- 
        old_zoom = self.current_zoom
        viewport = self.scroll_area.viewport()
        scrollbar = self.scroll_area.verticalScrollBar()
        current_scroll_y = scrollbar.value()
        viewport_center_y = current_scroll_y + viewport.height() / 2
        anchor_page_index = -1
        relative_offset_in_page = 0.5
        cumulative_height = 0
        for i, label in enumerate(self.page_labels):
            label_height = label.height() # Taille actuelle du label
            label_top_y = cumulative_height
            label_bottom_y = label_top_y + label_height
            if label_top_y <= viewport_center_y < label_bottom_y:
                anchor_page_index = i
                if label_height > 0:
                     relative_offset_in_page = (viewport_center_y - label_top_y) / label_height
                break
            cumulative_height += label_height + self.scroll_content_layout.spacing()
        # -------------------------------------------
        
        self.current_zoom = new_zoom
        
        # --- Redimensionner tous les QLabels --- 
        new_anchor_page_top_y = 0
        new_anchor_page_height = 0
        cumulative_height = 0
        max_width = 0
        
        for i, label in enumerate(self.page_labels):
            original_pixmap = self.original_pdf_pixmaps[i]
            original_size = original_pixmap.size()
            # Calculer la nouvelle taille basée sur le zoom ET la résolution de rendu initiale
            new_width = int(original_size.width() * (self.current_zoom / self.PDF_RENDER_ZOOM))
            new_height = int(original_size.height() * (self.current_zoom / self.PDF_RENDER_ZOOM))
            
            # Empêcher taille nulle
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            # Appliquer la nouvelle taille ET le pixmap original au QLabel
            label.setFixedSize(new_width, new_height)
            label.setPixmap(original_pixmap)
            # setScaledContents(True) est déjà défini lors de la création du label
            
            if i == anchor_page_index:
                 new_anchor_page_top_y = cumulative_height
                 new_anchor_page_height = new_height
                 
            cumulative_height += new_height + self.scroll_content_layout.spacing()
            if new_width > max_width: max_width = new_width
        # ---------------------------------------
            
        self.scroll_content_widget.setMinimumWidth(max_width + 20)
        self.total_pages_label.setText(f" / {self.total_pages}") # Mettre à jour label total
        self.page_input.setText(str(anchor_page_index + 1) if anchor_page_index != -1 else "-") # Mettre à jour input page
        self.zoom_out_button.setEnabled(self.current_zoom > self.zoom_step + 0.01)

        # --- Calcul et application scroll (inchangé mais basé sur tailles label) --- 
        new_center_target_y = new_anchor_page_top_y + relative_offset_in_page * new_anchor_page_height
        new_viewport_height = viewport.height()
        target_scroll_y = new_center_target_y - new_viewport_height / 2
        
        def adjust_scroll():
            max_scroll = scrollbar.maximum()
            final_scroll_y = max(0, min(int(target_scroll_y), max_scroll))
            scrollbar.setValue(final_scroll_y)
        QTimer.singleShot(10, adjust_scroll) # Petit délai
        # --------------------------------------------------------------------------
    
    def _apply_image_zoom(self):
        if not self.image_display_label or not self.original_image_pixmap:
             return
        original_size = self.original_image_pixmap.size()
        new_width = int(original_size.width() * self.current_zoom)
        new_height = int(original_size.height() * self.current_zoom)
        if new_width <= 0 or new_height <= 0: return
        
        # Utiliser setFixedSize sur le QLabel suffit car setScaledContents=True
        self.image_display_label.setFixedSize(new_width, new_height)
        self.image_display_label.setPixmap(self.original_image_pixmap) # Assurer que le pixmap original est là
        
        self.total_pages_label.setText(f"Zoom: {int(self.current_zoom * 100)}%")
        self.zoom_out_button.setEnabled(self.current_zoom > self.zoom_step + 0.01)

    # --- Slots Zoom modifiés --- 
    def _zoom_in(self):
        new_zoom = self.current_zoom + self.zoom_step
        # Limite max optionnelle
        # if new_zoom > 5.0: return 
        self.current_zoom = new_zoom # Mettre à jour le zoom
        if self.is_pdf:
             self._apply_pdf_zoom(self.current_zoom) # Passer le nouveau zoom
        elif self.is_image:
             self._apply_image_zoom()
        
    def _zoom_out(self):
        new_zoom = self.current_zoom - self.zoom_step
        if new_zoom < 0.1: return # Limite min
        self.current_zoom = new_zoom # Mettre à jour le zoom
        if self.is_pdf:
             self._apply_pdf_zoom(self.current_zoom) # Passer le nouveau zoom
        elif self.is_image:
             self._apply_image_zoom()
    # -----------------------------
    
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

