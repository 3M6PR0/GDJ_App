from PyQt5.QtWidgets import QTabBar, QApplication
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QDrag
import logging

logger = logging.getLogger('GDJ_App')

class DraggableTabBar(QTabBar):
    MIME_TYPE = "application/x-rapportdepense-tab-filepath" # Type MIME personnalisé

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_position = QPoint()
        self.parent_tab_widget = parent # Garder une référence au QTabWidget parent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()

        tab_index = self.tabAt(self.drag_start_position)
        if tab_index < 0:
            super().mouseMoveEvent(event)
            return

        current_widget = None
        if self.parent_tab_widget and hasattr(self.parent_tab_widget, 'widget'):
            current_widget = self.parent_tab_widget.widget(tab_index)

        file_path = None
        doc = None
        if current_widget:
            if hasattr(current_widget, 'document'):
                doc = current_widget.document
            elif hasattr(current_widget, 'document_object'): # Fallback
                doc = current_widget.document_object

        if doc:
            if hasattr(doc, 'file_path') and doc.file_path: # Priorité 1
                file_path = doc.file_path
            elif hasattr(doc, 'nom_fichier') and doc.nom_fichier: # Priorité 2 (souvent utilisé après sauvegarde)
                file_path = doc.nom_fichier
            elif hasattr(doc, 'original_file_path') and doc.original_file_path: # Priorité 3 (souvent utilisé après chargement)
                file_path = doc.original_file_path
        
        if not file_path:
            logger.warning(f"Onglet {tab_index} - Document non sauvegardé ou chemin de fichier (file_path, nom_fichier, original_file_path) non disponible pour le drag. Widget: {current_widget}, Document: {doc}")
            # On pourrait envisager de sérialiser le contenu si non sauvegardé, mais c'est plus complexe.
            # Pour l'instant, on ne permet le drag que des documents avec un file_path.
            super().mouseMoveEvent(event)
            return

        if file_path:
            logger.debug(f"Début du drag pour l'onglet {tab_index}, fichier: {file_path}")
            mime_data.setData(self.MIME_TYPE, file_path.encode('utf-8'))
            drag.setMimeData(mime_data)
            
            # L'action par défaut sera CopyAction. Si le drop est sur la même instance et le même QTabWidget,
            # Qt peut gérer le MoveAction (réarrangement) si setMovable(True) est sur le QTabWidget.
            # Pour le drag inter-fenêtres/inter-instances, on traitera cela comme une copie.
            # Le QDrag.exec_() bloquera jusqu'à ce que le drag soit terminé.
            drop_action = drag.exec_(Qt.CopyAction | Qt.MoveAction)

            if drop_action == Qt.MoveAction:
                # Normalement géré par QTabWidget lui-même si c'est un réarrangement interne.
                # Pour un drag vers une AUTRE fenêtre, on ne ferme PAS l'onglet source ici.
                # La logique de fermeture devrait être gérée par la cible si elle le souhaite (rare pour un drag inter-instance).
                logger.debug(f"Drag terminé avec MoveAction. L'onglet source reste ouvert pour le drag inter-fenêtre.")
            elif drop_action == Qt.CopyAction:
                logger.debug("Drag terminé avec CopyAction.")
            else:
                logger.debug(f"Drag annulé ou drop non géré. Action retournée: {drop_action}")
        else:
            # Pas de file_path, donc comportement par défaut
            super().mouseMoveEvent(event) 