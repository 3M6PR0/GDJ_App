import re
import shutil
from pathlib import Path
from typing import Optional

from models.config_data import ConfigData # Pour accéder aux codes GL

# Logger (supposons qu'un logger global est configuré et accessible si besoin)
# import logging
# logger = logging.getLogger('GDJ_App')

def sanitize_string_for_path(text: str, max_length: int = 50) -> str:
    """
    Nettoie une chaîne pour l'utiliser dans un nom de fichier ou de dossier.
    Remplace les espaces et caractères non alphanumériques par des underscores,
    supprime les underscores multiples et limite la longueur.
    """
    if not text: 
        return "inconnu"
    # Remplacer les caractères non alphanumériques (sauf . pour extensions) par _
    text = re.sub(r'[^a-zA-Z0-9_\.\-]', '_', str(text))
    # Remplacer les espaces par des underscores
    text = text.replace(' ', '_')
    # Supprimer les underscores consécutifs
    text = re.sub(r'_{2,}', '_', text)
    # Supprimer les underscores en début et fin de chaîne
    text = text.strip('_')
    # Tronquer à max_length si nécessaire
    if len(text) > max_length:
        text = text[:max_length]
        # S'assurer qu'on ne coupe pas au milieu d'une séquence d'échappement si c'était le cas
        # (moins pertinent ici après la sanitization, mais bonne pratique)
        text = text.rsplit('_', 1)[0] # Essayer de couper au dernier underscore
        if not text: # Si tout a été coupé
            text = str(text)[:max_length] # Couper brutalement
    if not text: # Si après tout ça, la chaîne est vide (ex: que des underscores supprimés)
        return "sanitized_empty"
    return text.lower()

def format_total_for_path(total: Optional[float]) -> str:
    """Formate un montant float en chaîne pour un nom de fichier (ex: 123.45 -> 123_45)."""
    if total is None:
        return "0_00"
    return f"{total:.2f}".replace('.', '_')

def get_gl_code_for_expense_type(expense_type_description: str) -> Optional[str]:
    """
    Récupère le code GL associé à une description de type de dépense depuis ConfigData.
    """
    if not expense_type_description:
        return None
    try:
        config = ConfigData.get_instance()
        # La structure attendue: config["documents"]["Global"][0]["codes_gl"]["depenses"]
        global_config_list = config.get_top_level_key("documents", {}).get("Global", [])
        if not global_config_list or not isinstance(global_config_list, list):
            # print("ConfigData: Section 'documents.Global' non trouvée ou mal formée.")
            return None
        
        codes_gl_section = global_config_list[0].get("codes_gl", {})
        depenses_codes_list = codes_gl_section.get("depenses", [])
        
        for code_info in depenses_codes_list:
            if isinstance(code_info, dict) and code_info.get("description") == expense_type_description:
                return str(code_info.get("code"))
        # print(f"ConfigData: Code GL non trouvé pour la description de dépense: {expense_type_description}")
        return None # Non trouvé
    except Exception as e:
        # print(f"Erreur lors de la récupération du code GL pour '{expense_type_description}': {e}")
        return None

def get_next_file_index(target_directory: Path, base_filename_no_ext: str, existing_stems_for_index: Optional[list[str]] = None) -> int:
    """
    Trouve le prochain index numérique disponible pour un fichier dans un dossier donné,
    en ignorant l'extension.
    Peut prendre une liste optionnelle de 'stems' existants pour l'indexation.
    Ex: si base_1.jpg, base_2.pdf existent, retourne 3.
    """
    max_index = 0
    processed_indices = set()

    if existing_stems_for_index is not None:
        # Utiliser la liste fournie de stems
        for name_part in existing_stems_for_index:
            if name_part.startswith(base_filename_no_ext + '_'):
                try:
                    index_str = name_part[len(base_filename_no_ext)+1:]
                    if index_str.isdigit():
                        processed_indices.add(int(index_str))
                except ValueError:
                    continue
    elif target_directory.is_dir():
        # Parcourir le dossier si aucune liste de stems n'est fournie
        for item in target_directory.iterdir():
            if item.is_file():
                name_part = item.stem # Nom du fichier sans extension
                if name_part.startswith(base_filename_no_ext + '_'):
                    try:
                        index_str = name_part[len(base_filename_no_ext)+1:]
                        if index_str.isdigit():
                            processed_indices.add(int(index_str))
                    except ValueError:
                        continue # Ne peut pas convertir en int, ignorer
    else:
        # Le dossier n'existe pas et pas de stems fournis, le premier index est 1
        return 1
    
    if not processed_indices:
        return 1
    else:
        return max(processed_indices) + 1 