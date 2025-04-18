import os
import re
# Importer theme depuis le même répertoire utils
from . import theme

def load_stylesheet(qss_files):
    # Réécriture complète pour s'assurer qu'il n'y a pas de caractères cachés
    """
    Charge et combine plusieurs fichiers QSS, en injectant les variables de thème.

    Args:
        qss_files (list): Une liste de chemins vers les fichiers .qss à charger.

    Returns:
        str: La feuille de style QSS combinée et formatée.
    """
    combined_qss = ""
    
    # Charger toutes les constantes de theme.py dans un dictionnaire
    theme_vars = {key: value for key, value in theme.__dict__.items() 
                  if not key.startswith('__') and isinstance(value, str)}
    
    # Lire et combiner les fichiers
    for filepath in qss_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                combined_qss += f.read() + "\n" # Ajouter un saut de ligne entre fichiers
        except FileNotFoundError:
            print(f"Avertissement: Fichier QSS non trouvé: {filepath}")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier QSS {filepath}: {e}")
            
    # Remplacer les placeholders {{NOM_CONSTANTE}}
    def replace_placeholder(match):
        var_name = match.group(1) # Capturer le nom de la variable
        return theme_vars.get(var_name, f'{{{{UNDEFINED: {var_name}}}}})') # Retourner la valeur ou une note d'erreur

    # Utiliser une regex pour trouver les placeholders {{...}}
    formatted_qss = re.sub(r'\{\{(\w+)\}\}', replace_placeholder, combined_qss)
    
    return formatted_qss

print("utils/stylesheet_loader.py défini") 