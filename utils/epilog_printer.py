import os
import json
import tempfile
# import subprocess # Plus nécessaire
import platform
import logging

from PyQt5.QtWidgets import QInputDialog, QMessageBox, QWidget, QFileDialog # Ajout de QFileDialog
from PyQt5.QtGui import QIcon

# Importations depuis le wrapper C++
from .epilog_cpp_wrapper import (
    EpilogMachine, 
    PrnGeneratorContext, 
    generate_print_file_data, # On pourrait l'appeler via le contexte mais direct c'est bien aussi
    send_print_data_to_laser,
    get_api_version as get_cpp_api_version, # Renommer pour éviter conflit si une autre func s'appelle pareil
    prn_gen_error_string # Implied import for prn_gen_error_string
)

logger = logging.getLogger(__name__)

# Dictionnaire pour mapper les noms de modèles conviviaux aux enums EpilogMachine
# Ceci devra être complété avec les modèles exacts que vous utilisez
# et comment ils correspondent aux noms dans l'enum EpilogMachine.
# Les clés doivent être en minuscules pour une comparaison insensible à la casse.
EPILOG_MODEL_TO_ENUM_MAP = {
    "fusionpro24": EpilogMachine.Pro24,
    "fusionpro32": EpilogMachine.Pro32,
    "fusionpro36": EpilogMachine.Pro36,
    "fusionpro48": EpilogMachine.Pro48,
    "fusionedge12": EpilogMachine.Edge12,
    "fusionedge24": EpilogMachine.Edge24,
    "fusionedge36": EpilogMachine.Edge36,
    "fusionmaker12": EpilogMachine.Maker12,
    "fusionmaker24": EpilogMachine.Maker24, # Ajouté pour le test
    "fusionmaker36": EpilogMachine.Maker36,
    "g100_4x4": EpilogMachine.G100_4x4,
    "g100_6x6": EpilogMachine.G100_6x6,
    "g2": EpilogMachine.G2,
    "fusion32m2": EpilogMachine.Fusion32M2, # Notez la casse/nom
    "fusion40m2": EpilogMachine.Fusion40M2,
    "fusion32": EpilogMachine.Fusion32,
    "fusion32fibermark": EpilogMachine.Fusion32Fibermark,
    "fusion40": EpilogMachine.Fusion40,
    "fibermark24": EpilogMachine.Fibermark24,
    "fibermark24s2": EpilogMachine.Fibermark24S2,
    "zing16": EpilogMachine.Zing16,
    "zing24": EpilogMachine.Zing24,
    "helix24": EpilogMachine.Helix24,
    "mini18": EpilogMachine.Mini18,
    "mini24": EpilogMachine.Mini24,
    "ext36": EpilogMachine.Ext36,
    # Ajoutez d'autres modèles ici au besoin, par exemple:
    # "fusion pro 48": EpilogMachine.Pro48, # Exemple d'alias plus convivial
}

def get_epilog_machine_enum(model_name_str: str) -> EpilogMachine | None:
    """Tente de trouver l'enum EpilogMachine correspondant à un nom de modèle."""
    if not model_name_str:
        return None
    # Recherche insensible à la casse
    model_key = model_name_str.lower().replace(" ", "").replace("_", "") # Normaliser un peu
    
    # Essayer une correspondance directe normalisée
    if model_key in EPILOG_MODEL_TO_ENUM_MAP:
        return EPILOG_MODEL_TO_ENUM_MAP[model_key]

    # Essayer de faire correspondre avec les noms d'attributs de l'enum (moins robuste)
    for member_name, member_value in EpilogMachine.__members__.items():
        if member_name.lower() == model_key:
            return member_value
            
    logger.warning(f"Modèle Epilog inconnu ou non mappé : {model_name_str}. Clé normalisée: {model_key}")
    return None

# def get_epilog_runner_command() -> str: # Plus nécessaire
#     """Détermine le nom de la commande pour Epilog PrintAPI Runner en fonction de l'OS."""
#     if platform.system() == "Windows":
#         return "epilog-print-api-runner.exe"
#     return "epilog-print-api-runner"

def send_lamicoid_to_epilog(
    svg_content: str,
    machine_model_name: str, # ex: "fusionmaker24"
    laser_ip_address: str,
    material_thickness_mm: float | None = None, # Pourrait être utilisé dans le JSON à l'avenir
    test_settings: dict | None = None # Pour passer des paramètres spécifiques pour le test
):
    logger.info(f"Début de send_lamicoid_to_epilog pour machine {machine_model_name} à {laser_ip_address}")
    logger.debug(f"SVG reçu (premiers 200 chars): {svg_content[:200]}...")

    epilog_machine_enum = EPILOG_MODEL_TO_ENUM_MAP.get(machine_model_name.lower().replace(" ", ""))
    if epilog_machine_enum is None:
        logger.error(f"Modèle de machine Epilog inconnu: {machine_model_name}")
        # Afficher les clés disponibles pour aider au débogage
        available_keys = ", ".join(EPILOG_MODEL_TO_ENUM_MAP.keys())
        logger.error(f"Modèles connus (clés pour EPILOG_MODEL_TO_ENUM_MAP): {available_keys}")
        return False, "Modèle de machine Epilog inconnu"

    # Configuration JSON avec le sous-objet cut_through_settings
    laser_settings_dict = {
        "job_name": "TestCercleEngrave",
        "firmware_version": "1.0.9.0",
        "autofocus": "off",
        "copies": 1,
        "processes": [
            {
                "_of": "vector_process",
                "name": "EngraveCircleProcess",
                "filter": { 
                    "_of": "color_filter",
                    "colors": ["black"]
                },
                "cycles": 1,
                "speed": 100.0,
                "power": 25.0,
                "frequency": 100.0,
                "laser_type": "co2",
                "vector_sorting": "off",
                "air_assist": False,
                "beziers": True,
                "offset": 0.0
            }
        ]
    }
    
    if test_settings: # Permettre de surcharger pour des tests spécifiques si besoin
        logger.info(f"Utilisation des paramètres de test fournis: {test_settings}")
        laser_settings_dict.update(test_settings)

    try:
        settings_json_str = json.dumps(laser_settings_dict)
        logger.debug(f"JSON de configuration généré (premiers 300 chars): {settings_json_str[:300]}...")
    except Exception as e:
        logger.error(f"Erreur lors de la sérialisation JSON des paramètres: {e}")
        return False, "Erreur de sérialisation JSON"

    # Utilisation du gestionnaire de contexte pour PrnGen
    with PrnGeneratorContext(svg_content, settings_json_str, epilog_machine_enum) as gen_ptr:
        if not gen_ptr:
            logger.error("Impossible de créer le générateur de fichier d'impression Epilog (gen_ptr est nul après contexte).")
            return False, "Échec création PrnGen"

        logger.info(f"Générateur PrnGen créé: {gen_ptr}. Tentative de génération des données du fichier d'impression...")
        
        # Étape 2: Générer les données du fichier d'impression.
        print_file_data_bytes = generate_print_file_data(gen_ptr)

        if print_file_data_bytes is None:
            logger.error("Échec de la génération des données du fichier d'impression (print_file_data_bytes est None).")
            # Essayer d'obtenir un message d'erreur de l'API si le gen_ptr est toujours considéré comme "bon"
            if prn_gen_error_string and gen_ptr: # Vérifier si la fonction et le ptr sont valides
                error_c_str = prn_gen_error_string(gen_ptr)
                if error_c_str:
                    error_message_from_api = error_c_str.decode('utf-8', errors='ignore')
                    logger.error(f"  Message d'erreur de l'API (via prn_gen_error_string après échec de generate_print_file_data): '{error_message_from_api}'")
                    # La doc indique que la chaîne de prn_gen_error_string est possédée par le générateur.
                    return False, f"Échec génération données PRN: {error_message_from_api}"
            return False, "Échec génération données PRN"

        logger.info(f"Données du fichier d'impression générées avec succès ({len(print_file_data_bytes)} octets).")
        if len(print_file_data_bytes) == 0:
            logger.warning("Les données du fichier d'impression générées sont vides (0 octets). Le laser pourrait ne rien faire.")
            # C'est un succès de génération, mais peut-être pas le résultat attendu. On continue l'envoi.

        # Étape 3: Envoyer les données au laser.
        logger.info(f"Tentative d'envoi des données ({len(print_file_data_bytes)} octets) au laser {machine_model_name} à {laser_ip_address}...")
        success_send = send_print_data_to_laser(epilog_machine_enum, print_file_data_bytes, laser_ip_address)

        if success_send:
            logger.info("Données envoyées avec succès au laser Epilog.")
            return True, "Données envoyées avec succès."
        else:
            logger.error("Échec de l'envoi des données au laser Epilog.")
            # Essayer d'obtenir un message d'erreur de l'API.
            # Note: prn_gen_send_file ne prend pas de PrnGen_p, donc on ne peut pas utiliser prn_gen_error_string ici.
            # Il faudrait une fonction d'erreur globale ou spécifique à l'envoi si elle existe.
            # Pour l'instant, on se contente du booléen de retour.
            return False, "Échec de l'envoi au laser"

    # Le PrnGen est automatiquement libéré ici grâce au __exit__ du PrnGeneratorContext
    logger.info("Fin de send_lamicoid_to_epilog (après le bloc 'with').")
    return False, "Terminé (sortie inattendue après 'with' si aucun retour avant)"

# Retrait de la section __main__ pour l'instant, car les tests directs nécessitent plus de configuration.
# if __name__ == '__main__':
#     # ... (ancien code de test)
#     print("Ce module est destiné à être importé et utilisé avec une QApplication existante.")

