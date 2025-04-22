import os
import re
# Importer theme depuis le même répertoire utils
from . import theme
# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path

def load_stylesheet(relative_qss_files):
    """
    Charge et combine plusieurs fichiers QSS, en injectant les variables de thème.
    Utilise get_resource_path pour trouver les fichiers.

    Args:
        relative_qss_files (list): Une liste de chemins relatifs vers les fichiers .qss.

    Returns:
        str: La feuille de style QSS combinée et formatée.
    """
    combined_qss = ""
    
    # Charger toutes les constantes de theme.py dans un dictionnaire
    theme_vars = {key: value for key, value in theme.__dict__.items() 
                  if not key.startswith('__') and isinstance(value, str)}
    
    # Lire et combiner les fichiers
    for relative_filepath in relative_qss_files:
        # --- Obtenir le chemin absolu --- 
        absolute_filepath = get_resource_path(relative_filepath)
        print(f"DEBUG: Chargement QSS depuis: {absolute_filepath}") # Ajout debug
        try:
            # --- Lire depuis le chemin absolu --- 
            with open(absolute_filepath, 'r', encoding='utf-8') as f:
                combined_qss += f.read() + "\n" # Ajouter un saut de ligne entre fichiers
        except FileNotFoundError:
            print(f"Avertissement: Fichier QSS non trouvé: {absolute_filepath}")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier QSS {absolute_filepath}: {e}")
            
    # Remplacer les placeholders {{NOM_CONSTANTE}}
    def replace_placeholder(match):
        var_name = match.group(1) # Capturer le nom de la variable
        return theme_vars.get(var_name, f'{{{{UNDEFINED: {var_name}}}}})') # Retourner la valeur ou une note d'erreur

    # Utiliser une regex pour trouver les placeholders {{...}}
    formatted_qss = re.sub(r'\{\{(\w+)\}\}', replace_placeholder, combined_qss)
    
    return formatted_qss

print("utils/stylesheet_loader.py défini") 