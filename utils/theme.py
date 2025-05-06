# utils/theme.py
import logging # Ajout pour le logger

# Initialisation du logger
logger = logging.getLogger('GDJ_App')

"""Configuration centralisée des thèmes de l'application."""

# --- Définitions Communes (Rayons, Paddings, etc.) ---
RADIUS_DEFAULT = "4px"
RADIUS_BOX = "6px"
RADIUS_CIRCLE = "50%" # Ou une valeur fixe
RADIUS_BADGE = "8px"
PADDING_SMALL = "4px"
PADDING_MEDIUM = "8px"
PADDING_LARGE = "15px"
BUTTON_HEIGHT_DEFAULT = "26px"
TITLE_HEIGHT = "25px"
COLOR_WHITE = "#ffffff"
COLOR_BLACK = "#000000"
COLOR_TRANSPARENT = "transparent"
# Accentuation (commune pour l'instant)
COLOR_ACCENT = "#0054b8"
COLOR_ACCENT_HOVER = "#0069d9"
COLOR_ACCENT_PRESSED = "#003d82"

# --- Thème Sombre (Dark) ---
DARK_THEME = {
    "COLOR_PRIMARY_DARKEST": "#2b2b2b",
    "COLOR_PRIMARY_DARK": "#313335",
    "COLOR_PRIMARY_MEDIUM": "#3c3f41",
    "COLOR_PRIMARY_LIGHT": "#4a4d4f",
    "COLOR_PRIMARY_LIGHTEST": "#5a5d5e",
    "COLOR_TEXT_PRIMARY": "#bbbbbb",
    "COLOR_TEXT_SECONDARY": "#808080",
    "COLOR_TEXT_INACTIVE": "#999999",
    "COLOR_TEXT_ON_ACCENT": "#ffffff",
    "COLOR_TEXT_ON_DARK_WIDGET": "#bbbbbb",
    "COLOR_ITEM_HOVER": "#45494d",
    "COLOR_ITEM_SELECTED": COLOR_ACCENT,
    "COLOR_SEARCH_BACKGROUND": "#353739",
    "COLOR_BADGE_BACKGROUND": "#6e7072",
    "COLOR_BADGE_TEXT": "#d0d0d0",
    "COLOR_BADGE_SELECTED_BACKGROUND": "#d5d5d5",
    "COLOR_BADGE_SELECTED_TEXT": "#333333",
    "COLOR_LOGO_BACKGROUND": "#1c6b9e",
    "COLOR_ACCENT": COLOR_ACCENT,
    "COLOR_ACCENT_HOVER": COLOR_ACCENT_HOVER,
    "COLOR_ACCENT_PRESSED": COLOR_ACCENT_PRESSED,
}

# --- Thème Clair (Light) --- BASED ON NUMERIC INVERSE OF DARK ---
LIGHT_THEME = {
    # Couleurs Primaires (Inversées)
    "COLOR_PRIMARY_DARKEST": "#ffffff",
    "COLOR_PRIMARY_DARK": "#f0f0f0",
    "COLOR_PRIMARY_MEDIUM": "#e0e0e0",
    "COLOR_PRIMARY_LIGHT": "#b5b2b0",
    "COLOR_PRIMARY_LIGHTEST": "#a5a2a1",
    # Couleurs de Texte (Inversées)
    "COLOR_TEXT_PRIMARY": "#444444",
    "COLOR_TEXT_SECONDARY": "#7f7f7f",
    "COLOR_TEXT_INACTIVE": "#666666",
    "COLOR_TEXT_ON_ACCENT": COLOR_BLACK,
    "COLOR_TEXT_ON_DARK_WIDGET": "#444444",
    # Couleurs Spécifiques (Inversées sauf exceptions)
    "COLOR_ITEM_HOVER": "#bab6b2",
    "COLOR_ITEM_SELECTED": COLOR_ACCENT,
    "COLOR_SEARCH_BACKGROUND": "#cac8c6",
    "COLOR_BADGE_BACKGROUND": "#918f8d",
    "COLOR_BADGE_TEXT": "#2f2f2f",
    "COLOR_BADGE_SELECTED_BACKGROUND": "#2a2a2a",
    "COLOR_BADGE_SELECTED_TEXT": "#cccccc",
    "COLOR_LOGO_BACKGROUND": "#1c6b9e",
    # Ajouter les couleurs d'accentuation (Non inversées)
    "COLOR_ACCENT": COLOR_ACCENT,
    "COLOR_ACCENT_HOVER": COLOR_ACCENT_HOVER,
    "COLOR_ACCENT_PRESSED": COLOR_ACCENT_PRESSED,
}

# --- Fonction pour obtenir le dictionnaire de thème --- 
def get_theme_vars(theme_name='Sombre'):
    """Retourne le dictionnaire de couleurs pour le thème demandé."""
    # --- Utiliser "Clair" pour le thème clair --- 
    if theme_name == 'Clair':
        return LIGHT_THEME.copy() 
    else: # Défaut sur sombre (pour "Sombre" ou toute autre valeur)
        return DARK_THEME.copy() 

logger.info(f"utils/theme.py défini avec thèmes DARK et LIGHT.") 