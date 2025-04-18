# uninstall_gdj.py
# Désinstalleur personnalisé pour GDJ

import sys
import os
import shutil
import winreg
import time
import traceback

# --- Configuration (DOIT correspondre à GDJ_Installation_UI.py) ---
APP_NAME = "GDJ"
APP_ID = "GDJApp" # ID unique utilisé pour la clé de registre
REG_UNINSTALL_PATH = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_ID}"

# --- Logging ---
log_dir = os.environ.get("TEMP", os.getcwd())
log_file_path = os.path.join(log_dir, "gdj_uninstaller_log.txt")

def log_message(message):
    try:
        with open(log_file_path, "a", encoding='utf-8') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"ERREUR LOGGING UNINSTALLER: {e}")

# --- Fonctions de désinstallation ---

def get_install_location():
    """Lit le chemin d'installation depuis le registre (HKCU)."""
    log_message(f"Lecture du registre: HKCU\\{REG_UNINSTALL_PATH}")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_UNINSTALL_PATH, 0, winreg.KEY_READ) as key:
            install_location, reg_type = winreg.QueryValueEx(key, "InstallLocation")
            if reg_type == winreg.REG_SZ:
                log_message(f"InstallLocation trouvé: {install_location}")
                return install_location
            else:
                log_message("Erreur: Type de registre incorrect pour InstallLocation.")
                return None
    except FileNotFoundError:
        log_message("Erreur: Clé de registre de désinstallation non trouvée.")
        return None
    except Exception as e:
        log_message(f"Erreur lecture registre: {e}\n{traceback.format_exc()}")
        return None

def remove_installation_directory(install_dir):
    """Supprime le dossier d'installation."""
    if not install_dir or not os.path.isdir(install_dir):
        log_message(f"Erreur: Dossier d'installation invalide ou introuvable: {install_dir}")
        return False
    log_message(f"Tentative de suppression du dossier: {install_dir}")
    try:
        shutil.rmtree(install_dir)
        # Vérifier si la suppression a réussi (le dossier ne doit plus exister)
        time.sleep(0.5) # Donner un peu de temps au système
        if not os.path.exists(install_dir):
            log_message("Suppression du dossier d'installation réussie.")
            return True
        else:
            log_message("Erreur: Le dossier d'installation existe toujours après la tentative de suppression.")
            return False
    except PermissionError:
        log_message(f"Erreur de permission lors de la suppression de {install_dir}. Des fichiers sont peut-être en cours d'utilisation.")
        return False
    except Exception as e:
        log_message(f"Erreur lors de la suppression du dossier {install_dir}: {e}\n{traceback.format_exc()}")
        return False

def remove_shortcuts():
    """Supprime les raccourcis Bureau et Menu Démarrer."""
    log_message("Tentative de suppression des raccourcis...")
    try:
        import winshell
        winshell_available = True
    except ImportError:
        winshell_available = False
        log_message("Avertissement: winshell non trouvé. Impossible de supprimer les raccourcis.")

    if not winshell_available:
        return False

    shortcut_name = f"{APP_NAME}.lnk"
    deleted_count = 0
    errors = []

    # Raccourci Bureau
    desktop_path = winshell.desktop()
    desktop_shortcut = os.path.join(desktop_path, shortcut_name)
    if os.path.exists(desktop_shortcut):
        log_message(f"Suppression du raccourci Bureau: {desktop_shortcut}")
        try:
            os.remove(desktop_shortcut)
            deleted_count += 1
        except Exception as e:
            log_message(f"Erreur suppression raccourci bureau: {e}")
            errors.append(f"Bureau: {e}")

    # Raccourci Menu Démarrer
    start_menu_path = winshell.programs()
    start_menu_folder = os.path.join(start_menu_path, APP_NAME)
    start_menu_shortcut = os.path.join(start_menu_folder, shortcut_name)
    if os.path.exists(start_menu_shortcut):
        log_message(f"Suppression du raccourci Menu Démarrer: {start_menu_shortcut}")
        try:
            os.remove(start_menu_shortcut)
            # Essayer de supprimer le dossier du menu démarrer s'il est vide
            try:
                if not os.listdir(start_menu_folder):
                    log_message(f"Suppression du dossier Menu Démarrer vide: {start_menu_folder}")
                    os.rmdir(start_menu_folder)
            except Exception as e_rmdir:
                log_message(f"Avertissement: Impossible de supprimer le dossier Menu Démarrer vide: {e_rmdir}")
            deleted_count += 1
        except Exception as e:
            log_message(f"Erreur suppression raccourci menu démarrer: {e}")
            errors.append(f"Menu Démarrer: {e}")
    elif os.path.isdir(start_menu_folder):
         # Essayer de supprimer le dossier même si le raccourci n'y est plus
         try:
            if not os.listdir(start_menu_folder):
                log_message(f"Suppression du dossier Menu Démarrer vide (sans raccourci trouvé): {start_menu_folder}")
                os.rmdir(start_menu_folder)
         except Exception as e_rmdir:
             log_message(f"Avertissement: Impossible de supprimer le dossier Menu Démarrer vide: {e_rmdir}")


    if errors:
        log_message(f"Suppression des raccourcis terminée avec {len(errors)} erreur(s).")
        return False
    elif deleted_count > 0:
        log_message("Suppression des raccourcis réussie.")
        return True
    else:
        log_message("Aucun raccourci GDJ trouvé à supprimer.")
        return True # Pas une erreur si rien n'a été trouvé

def remove_registry_key():
    """Supprime la clé de désinstallation du registre (HKCU)."""
    log_message(f"Tentative de suppression de la clé de registre: HKCU\\{REG_UNINSTALL_PATH}")
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_UNINSTALL_PATH)
        log_message("Suppression de la clé de registre réussie.")
        return True
    except FileNotFoundError:
        log_message("Avertissement: Clé de registre non trouvée, peut-être déjà supprimée.")
        return True # Pas une erreur si elle n'existe pas
    except Exception as e:
        log_message(f"Erreur lors de la suppression de la clé de registre: {e}\n{traceback.format_exc()}")
        return False

# --- Exécution Principale ---
if __name__ == "__main__":
    log_message("--- DÉBUT Désinstalleur GDJ ---")
    print("Désinstallation de GDJ en cours...")
    print(f"Log détaillé dans: {log_file_path}")

    all_successful = True

    # 1. Obtenir le chemin d'installation
    install_dir = get_install_location()
    if not install_dir:
        print("ERREUR: Impossible de trouver les informations d'installation.")
        all_successful = False
    else:
        # 2. Supprimer le dossier d'installation
        print(f"Suppression du dossier : {install_dir}")
        if not remove_installation_directory(install_dir):
            print("ERREUR: Échec de la suppression du dossier d'installation (voir log).")
            all_successful = False
        else:
            print("Dossier d'installation supprimé.")

    # 3. Supprimer les raccourcis
    print("Suppression des raccourcis...")
    if not remove_shortcuts():
        print("Avertissement: Problème lors de la suppression des raccourcis (voir log).")
        # Ne pas marquer comme échec critique pour l'instant
        # all_successful = False
    else:
        print("Raccourcis supprimés (ou non trouvés).")

    # 4. Supprimer la clé de registre
    print("Nettoyage du registre...")
    if not remove_registry_key():
        print("ERREUR: Échec de la suppression de la clé de registre (voir log).")
        all_successful = False
    else:
        print("Registre nettoyé.")

    # Fin
    log_message("--- FIN Désinstalleur GDJ ---")
    if all_successful:
        print("\nDésinstallation de GDJ terminée avec succès.")
    else:
        print("\nDésinstallation de GDJ terminée avec des erreurs. Veuillez consulter le log.")

    # Garder la fenêtre ouverte pour voir les messages
    input("\nAppuyez sur Entrée pour quitter...") 