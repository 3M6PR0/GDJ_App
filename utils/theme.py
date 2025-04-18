# config/theme.py

"""Configuration centralisée du thème de l'application."""

# --- Couleurs Primaires ---
COLOR_PRIMARY_DARKEST = "#2b2b2b"   # Fond principal des widgets
COLOR_PRIMARY_DARK = "#313335"      # Fond de la sidebar
COLOR_PRIMARY_MEDIUM = "#3c3f41"   # Fond des boîtes, boutons d'action
COLOR_PRIMARY_LIGHT = "#4a4d4f"    # Bordures fines
COLOR_PRIMARY_LIGHTEST = "#5a5d5e" # Bordures (ex: Recherche)

# --- Couleurs d'Accentuation ---
COLOR_ACCENT = "#0054b8"          # Bleu principal pour sélection, focus
COLOR_ACCENT_HOVER = "#0069d9"     # Légèrement plus clair pour hover sur accent
COLOR_ACCENT_PRESSED = "#003d82"    # Plus sombre pour clic sur accent

# --- Couleurs de Texte ---
COLOR_TEXT_PRIMARY = "#bbbbbb"     # Texte principal
COLOR_TEXT_SECONDARY = "#808080"  # Texte secondaire (chemins, labels formulaires)
COLOR_TEXT_INACTIVE = "#999999"   # Texte sidebar inactif
COLOR_TEXT_ON_ACCENT = "#ffffff"   # Texte sur fond d'accentuation (blanc)
COLOR_TEXT_ON_DARK_WIDGET = COLOR_TEXT_PRIMARY # Alias

# --- Couleurs Spécifiques (Exemples) ---
COLOR_ITEM_HOVER = "#45494d"
COLOR_ITEM_SELECTED = COLOR_ACCENT
COLOR_SEARCH_BACKGROUND = "#353739"
COLOR_BADGE_BACKGROUND = "#6e7072"
COLOR_BADGE_TEXT = "#d0d0d0"
COLOR_BADGE_SELECTED_BACKGROUND = "#d5d5d5"
COLOR_BADGE_SELECTED_TEXT = "#333333"
COLOR_LOGO_BACKGROUND = "#1c6b9e" # Spécifique au logo GDJ actuel
COLOR_WHITE = "#ffffff"
COLOR_TRANSPARENT = "transparent"

# --- Rayons (Border Radius) ---
RADIUS_DEFAULT = "4px"
RADIUS_BOX = "6px"
RADIUS_CIRCLE = "50%" # Ou une valeur fixe (ex: 12px) pour les petits boutons ronds
RADIUS_BADGE = "8px"

# --- Tailles / Padding (Exemples) ---
PADDING_SMALL = "4px"
PADDING_MEDIUM = "8px"
PADDING_LARGE = "15px"
BUTTON_HEIGHT_DEFAULT = "26px"
TITLE_HEIGHT = "25px"

# --- Polices (Définition Python - pour application facile) ---
# Note: Il est plus difficile d'utiliser des variables Python pour les polices DANS QSS.
# Il vaut mieux définir les styles de police directement dans QSS.
# On peut garder les objets QFont ici pour les appliquer via setFont() si besoin.
# from PyQt5.QtGui import QFont
# FONT_DEFAULT_FAMILY = "Segoe UI"
# FONT_DEFAULT_SIZE = 9
# FONT_DEFAULT = QFont(FONT_DEFAULT_FAMILY, FONT_DEFAULT_SIZE)
# FONT_SMALL = QFont(FONT_DEFAULT_FAMILY, FONT_DEFAULT_SIZE - 1)
# FONT_LARGE = QFont(FONT_DEFAULT_FAMILY, FONT_DEFAULT_SIZE + 1)
# FONT_BOLD = QFont(FONT_DEFAULT_FAMILY, FONT_DEFAULT_SIZE); FONT_BOLD.setBold(True)

# --- Styles QSS (Pré-formaté pour utilisation future) ---
# Option 1: Variables QSS (moins commun, nécessite préprocesseur ou formatage Python)
# qss_variables = f"""
#     * {{
#         primaryDarkest: {COLOR_PRIMARY_DARKEST};
#         accentColor: {COLOR_ACCENT};
#         /* ... etc ... */
#     }}
# """

# Option 2: Fonction pour charger et formater les QSS
# def load_and_format_qss(filepath):
#     with open(filepath, 'r') as f:
#         qss = f.read()
#     # Remplacer les placeholders (ex: {{COLOR_ACCENT}}) par les valeurs Python
#     qss = qss.replace('{{COLOR_ACCENT}}', COLOR_ACCENT)
#     qss = qss.replace('{{RADIUS_DEFAULT}}', RADIUS_DEFAULT)
#     # ... autres remplacements ...
#     return qss

print("config/theme.py défini") 