from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate, QStyle
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import pyqtSlot as Slot, Qt
from utils.signals import signals
from utils.theme import get_theme_vars # Importer seulement ce qui existe
from utils import theme as theme_module # Importer le module entier pour les constantes

# --- Délégué Personnalisé (Interne au module) --- 
class _StyledComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_vars = {}
        self.update_theme_vars() # Charger au démarrage
        signals.theme_changed_signal.connect(self.update_theme_vars)

    @Slot(str)
    def update_theme_vars(self, theme_name=None):
        """Met à jour les variables de thème utilisées par le délégué."""
        if theme_name is None:
            theme_name = 'Sombre' 
        
        theme_colors = get_theme_vars(theme_name)
        common_vars = {key: value for key, value in theme_module.__dict__.items() 
                       if not key.startswith('__') and key.isupper() 
                       and key not in ['DARK_THEME', 'LIGHT_THEME']}
        self._theme_vars = {**theme_colors, **common_vars}
        if self.parent() and hasattr(self.parent(), 'update'):
            self.parent().update()

    def paint(self, painter, option, index):
        # --- Contrôle total du dessin --- 
        painter.save()
        
        text = index.data(Qt.DisplayRole) # Texte à afficher
        
        # Déterminer les couleurs en fonction de l'état
        # bg_color_str = self._theme_vars.get('COLOR_PRIMARY_MEDIUM', '#ffffff') 
        text_color_str = self._theme_vars.get('COLOR_TEXT_PRIMARY', '#000000')
        
        is_selected = option.state & QStyle.State_Selected
        is_hovered = option.state & QStyle.State_MouseOver 

        if is_selected or is_hovered:
            # bg_color_str = self._theme_vars.get('COLOR_ITEM_SELECTED', '#0054b8')
            text_color_str = self._theme_vars.get('COLOR_TEXT_ON_ACCENT', '#ffffff')
            
        # --- TEST : FORCER FOND JAUNE PARTOUT --- 
        background_color = QColor(Qt.yellow)
        # ---------------------------------------
        text_color = QColor(text_color_str)
        
        # 1. Dessiner le fond
        painter.fillRect(option.rect, background_color)
        
        # 2. Dessiner le texte
        painter.setPen(text_color)
        # Ajouter un peu de padding pour le texte
        text_rect = option.rect.adjusted(5, 0, -5, 0) # Ajuster H seulement
        alignment = Qt.AlignVCenter | Qt.AlignLeft # Ou autre alignement?
        painter.drawText(text_rect, alignment, str(text)) # S'assurer que text est str
        
        painter.restore()
        # --- Ne PAS appeler super().paint() ---
        # super().paint(painter, option, index)

# --- Composant ComboBox Personnalisé --- 
class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Optionnel: Définir un nom d'objet si on veut le cibler en plus du nom de classe
        # self.setObjectName("StyledComboBoxComponent")
        
        # --- COMMENTER l'application du délégué --- 
        # self.view().setItemDelegate(_StyledComboBoxDelegate(self.view()))
        pass

    # Ajouter d'autres méthodes ou propriétés spécifiques si nécessaire

print("ui/components/styled_combobox.py defined") 