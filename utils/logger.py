import logging
import sys # Ajout pour stdout
import os  # Ajout pour getenv
from pathlib import Path # Ajout pour gestion chemin
import textwrap # Ajout pour le découpage des messages longs
from logging.handlers import RotatingFileHandler # AJOUT POUR ROTATION

# --- Configuration (Déplacé en haut pour clarté) ---
APP_LOGGER_NAME = 'GDJ_App' # Nom unique pour notre logger applicatif
LOG_FORMAT = "[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s" # Format: [Timestamp] [Fichier:Ligne] Message
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # Format du timestamp
MAX_MESSAGE_LINE_LENGTH = 1000 # Longueur max pour la partie message
CONTINUATION_PREFIX = "--> " # Préfixe pour les lignes de continuation

# Déterminer le chemin du fichier log dans APPDATA
try:
    APP_DATA_DIR = Path(os.getenv('APPDATA', '.')) / 'GDJ_App' # Fallback sur '.' si APPDATA n'est pas défini
    LOG_DIR = APP_DATA_DIR / 'logs'
    LOG_DIR.mkdir(parents=True, exist_ok=True) # Créer le répertoire s'il n'existe pas
    LOG_FILE_PATH = LOG_DIR / 'app.log'
except Exception as e:
    print(f"ERREUR CRITIQUE: Impossible de configurer le répertoire de logs : {e}")
    LOG_FILE_PATH = Path('app.log') # Fallback sur le répertoire courant

# --- Formatter Personnalisé --- 
class MultilineFormatter(logging.Formatter):
    """Formatter qui découpe les messages longs sur plusieurs lignes."""
    def format(self, record):
        # S'assurer que le message est formaté avec ses arguments
        record.message = record.getMessage()
        
        # Formater le préfixe (ex: "[timestamp] [file:line]")
        log_fmt_prefix_part = self._style._fmt.split('%(message)s')[0].strip()
        prefix_formatter = logging.Formatter(log_fmt_prefix_part, datefmt=self.datefmt)
        prefix = prefix_formatter.format(record)
        prefix_with_space = prefix + " "

        message_content = record.message # Le message utilisateur

        # Découper le message utilisateur
        wrapper = textwrap.TextWrapper(
            width=MAX_MESSAGE_LINE_LENGTH,
            initial_indent="", # Pas d'indentation initiale pour le message lui-même
            subsequent_indent=CONTINUATION_PREFIX, # Préfixe pour les lignes suivantes
            replace_whitespace=False,
            drop_whitespace=True,
            break_long_words=False,
            break_on_hyphens=True
        )
        wrapped_message_lines = wrapper.wrap(message_content)

        # Reconstruire les lignes de log finales
        formatted_lines = []
        if wrapped_message_lines:
            # Première ligne: préfixe normal + première ligne du message
            formatted_lines.append(prefix_with_space + wrapped_message_lines[0])
            
            # Lignes suivantes: indentation + ligne du message (qui contient déjà CONTINUATION_PREFIX)
            continuation_indent = " " * len(prefix_with_space)
            for line in wrapped_message_lines[1:]:
                formatted_lines.append(continuation_indent + line)
        else:
            # Gérer les messages vides ou très courts
            formatted_lines.append(prefix_with_space.rstrip() + message_content)

        return "\n".join(formatted_lines)
# ----------------------------

def setup_logger(level=logging.DEBUG):
    """Configure et retourne le logger principal de l'application ('{APP_LOGGER_NAME}').

    Ajoute un handler pour écrire dans la console (stdout) et un autre
    pour écrire dans un fichier log ('app.log' dans le dossier APPDATA/GDJ_App/logs).
    Utilise un format personnalisé incluant timestamp, nom de fichier:ligne et message,
    et découpe les messages longs sur plusieurs lignes.

    Args:
        level: Le niveau de logging minimum à capturer (par défaut: logging.DEBUG).

    Returns:
        L'instance du logger configuré.
    """
    # Utiliser le nom de logger applicatif défini globalement
    logger = logging.getLogger(APP_LOGGER_NAME)
    
    # Éviter d'ajouter plusieurs fois les handlers si la fonction est appelée plusieurs fois
    if logger.hasHandlers():
        # Optionnel: log si déjà configuré, mais de bas niveau pour éviter spam
        # logger.debug("Logger déjà configuré.") 
        return logger
        
    logger.setLevel(level)
    # --- Utiliser le MultilineFormatter --- 
    formatter = MultilineFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    # -------------------------------------

    # --- Handler pour la Console (stdout) ---
    # Modifier le handler existant pour utiliser sys.stdout explicitement
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # On pourrait définir un niveau différent si besoin:
    # console_handler.setLevel(logging.INFO) 

    # --- Handler pour le Fichier --- (Nouveau)
    try:
        # NOUVEAU: Utilisation de RotatingFileHandler
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH, 
            maxBytes=5*1024*1024,  # 5 MB par fichier
            backupCount=0,         # Conserver 0 fichiers de sauvegarde, app.log est vidé à la rotation
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        # On pourrait définir un niveau différent si besoin:
        # file_handler.setLevel(logging.DEBUG)
    except Exception as e:
        # Utiliser le print standard ici car le logger n'est peut-être pas encore fonctionnel
        print(f"ERREUR: Impossible de créer le handler de fichier log à {LOG_FILE_PATH}: {e}")
        file_handler = None # Pas de logging fichier en cas d'erreur

    # Ajouter les handlers au logger
    logger.addHandler(console_handler)
    if file_handler:
        logger.addHandler(file_handler)
        # Utiliser le logger pour confirmer la configuration réussie
        # (sera visible dans la console et le fichier si tout va bien)
        # logger.info(f"Logging configuré. Console activée. Fichier: {LOG_FILE_PATH}") # Déplacé après set propagate
    # else:
        # logger.warning("Logging configuré. Console activée. Logging fichier DÉSACTIVÉ (erreur).") # Déplacé après set propagate

    # --- EMPÊCHER LA PROPAGATION VERS LE LOGGER RACINE --- 
    logger.propagate = False
    # -----------------------------------------------------

    # --- Log de confirmation APRES avoir ajouté les handlers et défini la propagation ---
    if logger.hasHandlers(): # Vérifier à nouveau au cas où file_handler a échoué
        if file_handler:
            logger.info(f"Logger '{APP_LOGGER_NAME}' configuré. Handlers: Console, Fichier ({LOG_FILE_PATH}). Propagation désactivée. Multiline activé (max: {MAX_MESSAGE_LINE_LENGTH} chars).")
        else:
            logger.warning(f"Logger '{APP_LOGGER_NAME}' configuré. Handlers: Console SEULEMENT (Erreur Fichier). Propagation désactivée. Multiline activé (max: {MAX_MESSAGE_LINE_LENGTH} chars).")
    else:
        # Ce cas ne devrait pas arriver si console_handler a réussi
        print(f"AVERTISSEMENT CRITIQUE: Logger {APP_LOGGER_NAME} n'a AUCUN handler après configuration!") 
    # ------------------------------------------------------------------------------

    return logger

# Important: Exporter le nom du logger pour pouvoir le récupérer ailleurs
# (Cette ligne n'est pas nécessaire si on importe directement setup_logger)
# __all__ = ['setup_logger', 'APP_LOGGER_NAME'] 
