import os
import re
# Importer le module theme pour les constantes communes et la fonction
from . import theme 
from .theme import get_theme_vars
# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

def load_stylesheet(relative_qss_files, theme_name='Sombre'):
    """
    Charge et combine plusieurs fichiers QSS, en injectant les variables du thème spécifié.
    Utilise get_resource_path pour trouver les fichiers.

    Args:
        relative_qss_files (list): Liste de chemins relatifs vers les fichiers .qss.
        theme_name (str): Nom du thème à appliquer ('Clair' ou 'Sombre').

    Returns:
        str: La feuille de style QSS combinée et formatée.
    """
    combined_qss = ""
    
    # --- Obtenir le bon dictionnaire de couleurs --- 
    theme_colors = get_theme_vars(theme_name)
    # --- Ajouter les constantes communes (Rayons, Paddings, etc.) --- 
    # Récupérer toutes les variables globales en majuscules du module theme
    common_vars = {key: value for key, value in theme.__dict__.items() 
                   if not key.startswith('__') and key.isupper() 
                   and key not in ['DARK_THEME', 'LIGHT_THEME']} # Exclure les dicts de thèmes eux-mêmes
                   
    # Fusionner les deux dictionnaires (couleurs spécifiques + communes)
    all_theme_vars = {**theme_colors, **common_vars}
    
    # Lire et combiner les fichiers
    for relative_filepath in relative_qss_files:
        absolute_filepath = get_resource_path(relative_filepath)
        print(f"DEBUG: Chargement QSS depuis: {absolute_filepath} pour thème '{theme_name}'")
        try:
            with open(absolute_filepath, 'r', encoding='utf-8') as f:
                combined_qss += f.read() + "\n"
        except FileNotFoundError:
            print(f"Avertissement: Fichier QSS non trouvé: {absolute_filepath}")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier QSS {absolute_filepath}: {e}")
            
    # Remplacer les placeholders {{NOM_VARIABLE}}
    def replace_placeholder(match):
        var_name = match.group(1)
        # Utiliser le dictionnaire fusionné
        return all_theme_vars.get(var_name, f'{{{{UNDEFINED: {var_name}}}}})') # Note: Correction quote manquante

    formatted_qss = re.sub(r'\{\{(\w+)\}\}', replace_placeholder, combined_qss)
    
    return formatted_qss

print("utils/stylesheet_loader.py défini avec gestion de theme_name") 