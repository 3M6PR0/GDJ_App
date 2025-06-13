"""Définit l'item graphique pour un élément de texte."""

from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QInputDialog, QLineEdit, QGraphicsProxyWidget
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QObject, pyqtSignal

from models.documents.lamicoid_2.elements import ElementTexte
from .base_item import EditableItemBase

class SelectionSignalHelper(QObject):
    element_selected = pyqtSignal(object)

class TexteItem(EditableItemBase):
    """
    Un item éditable qui affiche un élément de texte.
    La boîte englobante est gérée par EditableItemBase.
    """
    def __init__(self, element_texte: ElementTexte, parent: QGraphicsItem = None):
        super().__init__(model_item=element_texte, parent=parent)
        self.signal_helper = SelectionSignalHelper()
        self.setPos(self.model_item.x_mm, self.model_item.y_mm)
        
        # Mettre à jour la géométrie de la boîte en fonction du texte
        self._update_bounding_box()

    def _update_bounding_box(self):
        """Ajuste le rectangle de l'item à la taille du texte, en tenant compte du word wrap."""
        font = QFont(self.model_item.nom_police, self.model_item.taille_police_pt)
        # Largeur cible = largeur actuelle de l'élément
        width = self.rect().width() if self.rect().width() > 0 else 100
        temp_text_item = QGraphicsTextItem(self.model_item.contenu)
        temp_text_item.setFont(font)
        temp_text_item.setTextWidth(width)
        text_rect = temp_text_item.boundingRect()
        self.setRect(0, 0, width, text_rect.height())

    def paint(self, painter, option, widget=None):
        # 1. Laisser la classe de base dessiner le cadre de sélection si nécessaire
        super().paint(painter, option, widget)

        # 2. Dessiner le texte avec word wrap
        painter.setPen(QColor(Qt.black))
        font = QFont(self.model_item.nom_police, self.model_item.taille_police_pt)
        font.setBold(getattr(self.model_item, 'bold', False))
        font.setItalic(getattr(self.model_item, 'italic', False))
        font.setUnderline(getattr(self.model_item, 'underline', False))
        painter.setFont(font)
        align = getattr(self.model_item, 'align', Qt.AlignHCenter)
        flags = align | Qt.AlignVCenter | Qt.TextWordWrap
        painter.drawText(self.rect(), flags, self.model_item.contenu)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Surcharge pour mettre à jour le modèle après un déplacement."""
        if change == QGraphicsItem.ItemSelectedChange:
            print(f"[DEBUG] TexteItem sélection changée : {value}")
            self.signal_helper.element_selected.emit(self if value else None)
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Mettre à jour x_mm/y_mm en fonction de la position réelle de l'item dans la scène
            scene = self.scene()
            if scene and hasattr(scene.parent(), 'current_template') and scene.parent().current_template:
                from pages.documents.lamicoid_2.template_editor_view import _pixels_to_mm
                lamicoid_width = scene.parent().current_template.largeur_mm
                lamicoid_height = scene.parent().current_template.hauteur_mm
                # La position de l'item est relative au centre de la scène
                pos = self.pos()
                # On veut x_mm = (position en mm depuis le centre du lamicoid) + centre du lamicoid
                x_mm = lamicoid_width / 2 + _pixels_to_mm(pos.x())
                y_mm = lamicoid_height / 2 + _pixels_to_mm(pos.y())
                self.model_item.x_mm = x_mm
                self.model_item.y_mm = y_mm
        return super().itemChange(change, value)

    def set_alignment(self, alignment):
        """Définit l'alignement du texte."""
        self.model_item.align = alignment
        self.update()  # Force le redessinage de l'item 

    def mouseDoubleClickEvent(self, event):
        # Édition inline avec QLineEdit ajouté à la scène
        scene = self.scene()
        if not scene:
            return
        # Créer le QLineEdit
        editor = QLineEdit(self.model_item.contenu)
        editor.setFrame(False)
        editor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont(self.model_item.nom_police, self.model_item.taille_police_pt)
        font.setBold(getattr(self.model_item, 'bold', False))
        font.setItalic(getattr(self.model_item, 'italic', False))
        font.setUnderline(getattr(self.model_item, 'underline', False))
        editor.setFont(font)
        # Ajouter à la scène
        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(editor)
        rect = self.rect()
        proxy.setPos(rect.x(), rect.y())
        proxy.resize(rect.width(), rect.height())
        editor.setFocus()
        editor.selectAll()
        # Fonction de validation
        def finish_edit():
            new_text = editor.text()
            if new_text != self.model_item.contenu:
                self.model_item.contenu = new_text
                self._update_bounding_box()
                self.update()
            proxy.setParentItem(None)
            proxy.deleteLater()
        editor.editingFinished.connect(finish_edit)
        # Pour perte de focus
        old_focus_out = editor.focusOutEvent
        def custom_focus_out(event):
            finish_edit()
            old_focus_out(event)
        editor.focusOutEvent = custom_focus_out
        # Empêcher propagation du double-clic
        event.accept()

    def set_underline(self, value):
        self.model_item.underline = value
        self.update() 