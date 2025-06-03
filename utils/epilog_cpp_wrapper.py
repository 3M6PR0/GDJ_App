import ctypes
import platform
import os
import logging

# Configuration de logging spécifique pour ce module (pour débogage temporaire)
# Cela permet de voir les logs DEBUG de ce fichier même si la config globale est différente.
_module_logger = logging.getLogger(__name__)
if not _module_logger.handlers: # Ajouter un handler seulement si ce logger n'en a pas déjà
    _handler = logging.StreamHandler() # Par défaut vers sys.stderr, ou sys.stdout si disponible via la config globale de base
    _formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(lineno)d] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    _handler.setFormatter(_formatter)
    _module_logger.addHandler(_handler)
_module_logger.setLevel(logging.DEBUG) # Forcer le niveau DEBUG pour ce logger
# Fin de la configuration de logging spécifique pour débogage

logger = _module_logger # S'assurer que le reste du module utilise ce logger configuré

# Nom de la bibliothèque partagée (corrigé selon vos informations)
LIB_NAME_WINDOWS = "epilog_print_api_libcpp.dll"
LIB_NAME_LINUX = "libepilog-print-api.so" # Gardons celui-ci pour l'instant, à vérifier si différent aussi

# Chemin vers la bibliothèque C++ (corrigé avec la double mention du dossier)
# Cela suppose que la structure du dossier est GDJ_App/Others/epilog-print-api-release-latest/epilog-print-api-release-latest/cpp-library/
# Et que ce fichier (epilog_cpp_wrapper.py) est dans GDJ_App/utils/
# Correction: os.path.dirname appelé une fois de moins pour pointer vers la racine de GDJ_App
APP_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Remonte à GDJ_App
CPP_LIB_BASE_PATH = os.path.join(APP_ROOT_DIR, "Others", "epilog-print-api-release-latest", "epilog-print-api-release-latest", "cpp-library")

# Charger la bibliothèque
epilog_api_lib = None
lib_path = None

if platform.system() == "Windows":
    lib_path = os.path.join(CPP_LIB_BASE_PATH, "win-x64", LIB_NAME_WINDOWS)
    logger.info(f"Chemin calculé pour la DLL Windows: {lib_path}")
    if os.path.exists(lib_path):
        logger.info(f"Fichier DLL trouvé à: {lib_path}")
        try:
            epilog_api_lib = ctypes.CDLL(lib_path)
        except OSError as e:
            logger.error(f"Erreur lors du chargement de la DLL {LIB_NAME_WINDOWS} depuis {lib_path}: {e}")
    else:
        logger.error(f"Fichier DLL NON TROUVÉ à: {lib_path}")
elif platform.system() == "Linux":
    # Pour Linux, il faudra peut-être s'assurer que le dossier contenant .so est dans LD_LIBRARY_PATH
    # ou utiliser le chemin absolu.
    lib_path = os.path.join(CPP_LIB_BASE_PATH, "ubuntu-20.04", LIB_NAME_LINUX)
    logger.info(f"Chemin calculé pour la bibliothèque partagée Linux: {lib_path}")
    if os.path.exists(lib_path):
        logger.info(f"Fichier de bibliothèque partagée trouvé à: {lib_path}")
        try:
            epilog_api_lib = ctypes.CDLL(lib_path)
        except OSError as e:
            logger.error(f"Erreur lors du chargement de la bibliothèque partagée {LIB_NAME_LINUX} depuis {lib_path}: {e}")
    else:
        logger.error(f"Fichier de bibliothèque partagée NON TROUVÉ à: {lib_path}")
else:
    logger.error(f"Plateforme non supportée: {platform.system()}")

if epilog_api_lib:
    logger.info(f"Bibliothèque Epilog C++ chargée avec succès depuis: {lib_path}")
else:
    logger.error("Impossible de charger la bibliothèque Epilog C++. Les fonctionnalités d'impression via C++ API ne seront pas disponibles.")

def get_enum_name_from_value(enum_class, value, default_name="Unknown"):
    """
    Récupère le nom d'un membre d'une classe utilisée comme une énumération (style ctypes)
    à partir de sa valeur numérique.
    """
    for name in dir(enum_class):
        # Exclure les attributs privés/magiques et les méthodes
        if not name.startswith('_') and not callable(getattr(enum_class, name)):
            member_value = getattr(enum_class, name)
            # Les membres des énumérations ctypes (comme Success = 0) sont accessibles comme des entiers.
            if isinstance(member_value, int) and member_value == value:
                return name
    return f"{default_name} (value: {value})"

# --- Énumérations --- 
class EpilogMachine(ctypes.c_uint):
    Pro24 = 0
    Pro32 = 1
    Pro36 = 2
    Pro48 = 3
    Edge12 = 4
    Edge24 = 5
    Edge36 = 6
    Maker12 = 7
    Maker24 = 8
    Maker36 = 9
    G100_4x4 = 10
    G100_6x6 = 11
    G2 = 12
    Fusion32M2 = 13
    Fusion40M2 = 14
    Fusion32 = 15
    Fusion32Fibermark = 16
    Fusion40 = 17
    Fibermark24 = 18
    Fibermark24S2 = 19
    Zing16 = 20
    Zing24 = 21
    Helix24 = 22
    Mini18 = 23
    Mini24 = 24
    Ext36 = 25
    Unknown = 26

# RENOMMAGE de CApiResult (enum) en EpilogApiStatusCode
class EpilogApiStatusCode(ctypes.c_uint): # Était CApiResult
    Success = 0
    NullArgument = 1
    InvalidSvgData = 2
    PrnGenInitializationFailure = 3
    PrnGenRunFailure = 4
    PrnGenNotInitialized = 5
    PrnGenAlreadyCompleted = 6
    NetworkSendFailure = 7
    MachineCommunicationFailure = 8
    FileOpenFailure = 9
    InvalidSettingsJson = 10
    BufferTooSmall = 11
    UnknownError = 12

# --- Structures (à définir ensuite) ---
# typedef struct PrnGen PrnGen;
class PrnGen(ctypes.Structure):
    # Structure opaque, ctypes n'a pas besoin de connaître ses membres
    # On l'utilise comme un type de pointeur.
    pass

# Pointeurs vers les structures opaques
PrnGen_p = ctypes.POINTER(PrnGen)

# NOUVELLE STRUCTURE pour les résultats de prn_gen_get_result / prn_gen_run_until_complete
class ApiResultData(ctypes.Structure):
    _fields_ = [
        ("result", ctypes.POINTER(ctypes.c_ubyte)), # Pointeur vers les données du fichier
        ("result_size", ctypes.c_uint64),          # Taille des données
        ("error_message_ptr", ctypes.c_char_p)     # MODIFIÉ: Pointeur vers une chaîne d'erreur (NULL si succès)
    ]
ApiResultData_p = ctypes.POINTER(ApiResultData)

class CProgressReport(ctypes.Structure):
    _fields_ = [
        ("progress_type", ctypes.c_int), # ProgressType enum
        ("stage_name", ctypes.c_char_p),
        ("stage_json", ctypes.c_char_p),
        ("stage_has_progress", ctypes.c_bool),
        ("stage_progress", ctypes.c_float),
        ("stage_index", ctypes.c_uint64), # uintptr_t est généralement un entier non signé de la taille d'un pointeur
        ("stage_count", ctypes.c_uint64),
        ("total_progress", ctypes.c_float),
    ]

class CApiError(ctypes.Structure):
    _fields_ = [
        ("error", ctypes.c_char_p),
    ]

class PrintData(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_ubyte)),
        ("length", ctypes.c_uint64)
    ]

# --- Définition des prototypes des fonctions C --- 

# Fonction pour configurer argtypes et restype plus facilement
def setup_func(name, restype, argtypes):
    if epilog_api_lib:
        try:
            func = getattr(epilog_api_lib, name)
            func.restype = restype
            func.argtypes = argtypes
            return func
        except AttributeError:
            logger.critical(f"Fonction C '{name}' non trouvée dans la bibliothèque. L'API ne fonctionnera pas correctement.")
            return None
    return None

# prn_gen_new
# Retour à l'hypothèse la plus directe de la doc C++: 3 arguments, retourne PrnGen*
prn_gen_new = setup_func("prn_gen_new", PrnGen_p, [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint])

# free_prn_gen
free_prn_gen = setup_func("free_prn_gen", ctypes.c_bool, [PrnGen_p])

# prn_gen_add_font_data
prn_gen_add_font_data = setup_func("prn_gen_add_font_data", EpilogApiStatusCode, [PrnGen_p, ctypes.c_char_p, ctypes.c_uint64])

# prn_gen_run_chunk
# La doc C++ dit: [return: `bool`] Whether or not there is more work to do.
prn_gen_run_chunk = setup_func("prn_gen_run_chunk", ctypes.c_bool, [PrnGen_p])

# prn_gen_run_until_complete
# Retourne la structure ApiResultData*, pas un simple code.
# MODIFIÉ: Retourne la structure ApiResultData elle-même, pas un pointeur.
prn_gen_run_until_complete = setup_func("prn_gen_run_until_complete", ApiResultData, [PrnGen_p])

# prn_gen_request_abort
prn_gen_request_abort = setup_func("prn_gen_request_abort", EpilogApiStatusCode, [PrnGen_p])

# prn_gen_get_progress
prn_gen_get_progress = setup_func("prn_gen_get_progress", CProgressReport, [PrnGen_p])

# prn_gen_get_result
# Retourne la structure ApiResultData*, pas un simple code.
# MODIFIÉ: Retourne la structure ApiResultData elle-même, pas un pointeur.
prn_gen_get_result = setup_func("prn_gen_get_result", ApiResultData, [PrnGen_p])

# prn_gen_is_complete
# La doc C++ dit: [return: `bool`]
prn_gen_is_complete = setup_func("prn_gen_is_complete", ctypes.c_bool, [PrnGen_p])

# prn_gen_has_error
# La doc C++ dit: [return: `bool`]
prn_gen_has_error = setup_func("prn_gen_has_error", ctypes.c_bool, [PrnGen_p])

# prn_gen_was_aborted
# La doc C++ dit: [return: `bool`]
prn_gen_was_aborted = setup_func("prn_gen_was_aborted", ctypes.c_bool, [PrnGen_p])

# prn_gen_error_string
prn_gen_error_string = setup_func("prn_gen_error_string", ctypes.c_char_p, [PrnGen_p])

# prn_gen_send_file
# Signature C: bool prn_gen_send_file(EpilogMachine machine, const char *data, uintptr_t data_length, const char *ip_address);
# MODIFIÉ: La fonction C attend un pointeur direct vers les données et une longueur, pas une structure PrintData.
prn_gen_send_file = setup_func(
    "prn_gen_send_file", 
    ctypes.c_bool, 
    [ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint64, ctypes.c_char_p]
)

# free_c_api_result
# Prend un pointeur vers la structure ApiResultData
free_c_api_result = setup_func("free_c_api_result", ctypes.c_bool, [ApiResultData_p])

# free_c_api_error
free_c_api_error = setup_func("free_c_api_error", ctypes.c_bool, [ctypes.POINTER(CApiError)])

# free_cstring
free_cstring = setup_func("free_cstring", ctypes.c_bool, [ctypes.c_char_p])

# free_carray
free_carray = setup_func("free_carray", ctypes.c_bool, [ctypes.c_char_p, ctypes.c_uint64])

# api_version
api_version = setup_func("api_version", ctypes.c_char_p, [])

# free_c_progress_report (basé sur le header, semble manquer dans le README)
free_c_progress_report = setup_func("free_c_progress_report", EpilogApiStatusCode, [ctypes.POINTER(CProgressReport)])


# --- Fonctions Python wrapper (à implémenter) --- 

def get_api_version() -> str:
    if not api_version:
        logger.warning("API C non chargée, impossible d'obtenir la version.")
        return "API C non chargée"
    try:
        version_ptr = api_version()
        if version_ptr:
            version_str = ctypes.cast(version_ptr, ctypes.c_char_p).value
            # Selon le README, les C-strings retournées par l'API doivent être libérées avec free_cstring.
            # Cependant, pour api_version(), qui retourne const char*, il est plus sûr de supposer
            # que la chaîne est statique ou que sa durée de vie est gérée par la lib,
            # à moins que la doc ne spécifie clairement qu'elle doit être libérée par l'appelant.
            # if free_cstring and version_str: free_cstring(version_ptr) # Prudence ici.
            if version_str:
                return version_str.decode('utf-8')
            return "Version inconnue (pointeur nul)"
        return "Version inconnue (pointeur nul retourné par l'API)"
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à api_version: {e}")
        return "Erreur API"

def create_prn_generator(svg_data_str: str, settings_json_str: str, machine: EpilogMachine) -> tuple[PrnGen_p | None, bytes | None, bytes | None]:
    if not prn_gen_new:
        logger.error("Bibliothèque C Epilog non chargée, impossible de créer le générateur PRN.")
        return None, None, None

    # Convertir les chaînes Python en objets bytes. CES OBJETS DOIVENT RESTER EN VIE.
    svg_data_bytes = svg_data_str.encode('utf-8')
    settings_json_bytes = settings_json_str.encode('utf-8')

    logger.debug(f"create_prn_generator (3-arg direct): recu machine type={type(machine)}, representation={machine}")
    try:
        machine_val_for_c = int(machine)
        logger.debug(f"create_prn_generator (3-arg direct): machine_val_for_c={machine_val_for_c} (type: {type(machine_val_for_c)}) prête pour C.")
    except Exception as e_conv:
        logger.error(f"Erreur lors de la conversion de 'machine' (type: {type(machine)}, valeur: {machine}) en entier: {e_conv}")
        return None, None, None

    logger.info(f"Appel de prn_gen_new (3 args), attendant un PrnGen* direct.")
    logger.debug(f"  Avec SVG (début): {svg_data_str[:200]}...")
    logger.debug(f"  Avec Settings JSON (début): {settings_json_str[:200]}...")
    logger.debug(f"  Avec Machine enum value: {machine_val_for_c}")
    
    returned_gen_ptr = prn_gen_new(svg_data_bytes, settings_json_bytes, machine_val_for_c)
    
    if returned_gen_ptr:
        logger.info(f"prn_gen_new (3-arg direct) a retourné un pointeur: {returned_gen_ptr}")

        # Vérifier les erreurs immédiates en utilisant prn_gen_has_error et prn_gen_error_string
        if prn_gen_has_error and prn_gen_error_string and free_prn_gen: # S'assurer que free_prn_gen est aussi chargé
            try:
                has_error_flag = prn_gen_has_error(returned_gen_ptr)
                logger.info(f"  prn_gen_has_error(returned_gen_ptr) a retourné: {has_error_flag}")
                if has_error_flag:
                    error_c_str = prn_gen_error_string(returned_gen_ptr)
                    if error_c_str:
                        error_message_from_api = error_c_str.decode('utf-8', errors='ignore')
                        logger.warning(f"  Message d'erreur de prn_gen_error_string APRES prn_gen_has_error=true: '{error_message_from_api}'")
                    else:
                        logger.warning("  prn_gen_has_error est true, mais prn_gen_error_string a retourné NULL.")
                    
                    logger.warning(f"  Puisque prn_gen_has_error est true, le générateur {returned_gen_ptr} est considéré comme invalide et va être libéré.")
                    free_prn_gen(returned_gen_ptr) # Libérer le générateur défectueux
                    return None, None, None # Échec de création
            except Exception as e_check_err:
                logger.error(f"  Exception durant la vérification d'erreur avec prn_gen_has_error/prn_gen_error_string: {e_check_err}")
                logger.info(f"  Tentative de libération du générateur {returned_gen_ptr} suite à l'exception durant la vérification d'erreur.")
                free_prn_gen(returned_gen_ptr) # Libérer en cas d'erreur ici aussi
                return None, None, None # Échec de création
        elif not (prn_gen_has_error and prn_gen_error_string and free_prn_gen):
            logger.warning("  Les fonctions prn_gen_has_error, prn_gen_error_string ou free_prn_gen ne sont pas disponibles pour une vérification d'erreur complète et une libération.")

        # Si on arrive ici, soit prn_gen_has_error n'est pas dispo, soit il a retourné false.
        # Essayer de déréférencer pour voir si le pointeur est quelque peu valide
        try:
            _ = returned_gen_ptr.contents 
            logger.info(f"  L'accès à returned_gen_ptr.contents semble OK. Le pointeur est déréférençable.")
            # Succès: retourner le pointeur et les objets bytes pour les maintenir en vie
            return returned_gen_ptr, svg_data_bytes, settings_json_bytes
        except Exception as e_access_contents:
            logger.error(f"  Erreur lors de l'accès à returned_gen_ptr.contents: {e_access_contents}. Le pointeur retourné ({returned_gen_ptr}) est probablement invalide.")
            if free_prn_gen: # S'assurer que free_prn_gen est chargé
                 logger.info(f"  Tentative de libération du générateur potentiellement invalide {returned_gen_ptr} suite à l'échec de .contents...")
                 free_prn_gen(returned_gen_ptr)
            return None, None, None # Indiquer l'échec
    else:
        # prn_gen_new a retourné NULL
        logger.error(f"prn_gen_new (3-arg direct) a retourné NULL. Échec de création du PrnGen.")
        return None, None, None # Indiquer l'échec

def destroy_prn_generator(gen_ptr: PrnGen_p):
    if not free_prn_gen:
        logger.warning("API C non chargée, impossible de libérer PrnGen.")
        return
    if not gen_ptr: # Vérifier si gen_ptr lui-même est nul
        logger.warning("Tentative de libération d'un pointeur PrnGen nul.")
        return
    
    try:
        success = free_prn_gen(gen_ptr)
        if success:
            logger.info(f"PrnGen {gen_ptr} libéré avec succès (free_prn_gen a retourné true).")
        else:
            logger.error(f"Échec de la libération de PrnGen {gen_ptr} par l'API (free_prn_gen a retourné false).")
    except Exception as e:
        logger.error(f"Exception lors de la libération du PrnGen {gen_ptr}: {e}")

def generate_print_file_data(gen_ptr: PrnGen_p) -> bytes | None:
    _module_logger.debug(f"generate_print_file_data REÇU gen_ptr: {gen_ptr}")

    # Utiliser prn_gen_run_until_complete comme dans l'exemple C++
    if not all([prn_gen_run_until_complete, free_c_api_result]):
        _module_logger.error("API C non chargée ou fonctions manquantes (prn_gen_run_until_complete/free_c_api_result), impossible de générer les données.")
        return None
    if not gen_ptr:
        _module_logger.error("gen_ptr est nul dans generate_print_file_data.")
        return None

    _module_logger.info(f"Début de la génération des données avec prn_gen_run_until_complete pour gen_ptr: {gen_ptr}")
    
    returned_api_result_struct = None # Pour s'assurer qu'il est défini pour le bloc finally

    try:
        # Appel direct à prn_gen_run_until_complete
        # Elle retourne la structure directement maintenant
        returned_api_result_struct = prn_gen_run_until_complete(gen_ptr)
        
        _module_logger.debug(f"prn_gen_run_until_complete a retourné une STRUCTURE.")
        _module_logger.debug(f"  Structure.error_message_ptr: {returned_api_result_struct.error_message_ptr}")
        _module_logger.debug(f"  Structure.result_size: {returned_api_result_struct.result_size}")
        _module_logger.debug(f"  Structure.result (pointeur): {returned_api_result_struct.result}")

        # Vérifier si un message d'erreur est présent
        error_msg = None
        if returned_api_result_struct.error_message_ptr:
            try:
                error_msg = returned_api_result_struct.error_message_ptr.decode('utf-8')
                _module_logger.info(f"  Message d'erreur de l'API (via ApiResultData.error_message_ptr): '{error_msg}'")
            except Exception as e:
                _module_logger.error(f"  Impossible de décoder error_message_ptr: {e}")
                error_msg = "Erreur API non décodable"

        if error_msg and error_msg != "": # Vérifier si un message d'erreur non vide existe
            # Même si error_msg est "Print file generation not yet complete", on le logue comme une erreur ici.
            _module_logger.error(f"Échec de la génération des données PRN. Message d'erreur API: '{error_msg}'")
            return None # Échec
        
        # Si pas d'erreur, essayer de récupérer les données
        if returned_api_result_struct.result and returned_api_result_struct.result_size > 0:
            _module_logger.info(f"Succès apparent de la génération. Taille des données: {returned_api_result_struct.result_size} octets.")
            # Copier les données du pointeur vers un objet bytes Python
            # Attention: returned_api_result_struct.result est POINTER(c_ubyte)
            # Nous devons créer un buffer Python à partir de cela.
            
            # Convertir POINTER(c_ubyte) en un objet bytes Python
            # Cela crée une copie des données, ce qui est sûr.
            prn_data_bytes = ctypes.string_at(returned_api_result_struct.result, returned_api_result_struct.result_size)
            
            _module_logger.info(f"Données PRN copiées avec succès (taille: {len(prn_data_bytes)}).")
            return prn_data_bytes
        elif returned_api_result_struct.result_size == 0 and (not error_msg or error_msg == ""):
             _module_logger.warning("Génération des données PRN: Aucune erreur retournée, mais result_size est 0. Aucune donnée à retourner.")
             return None # Pas d'erreur explicite mais pas de données
        else:
            # Ce cas ne devrait pas être atteint si error_msg a été traité, mais par sécurité
            _module_logger.warning("Génération des données PRN: État inattendu après prn_gen_run_until_complete.")
            return None

    except Exception as e:
        _module_logger.error(f"Exception majeure inattendue dans generate_print_file_data: {e}", exc_info=True)
        # Tenter de vérifier si prn_gen_has_error et prn_gen_error_string donnent plus d'infos
        # Cela ne devrait pas être nécessaire si returned_api_result_struct.error_message_ptr est utilisé
        # Mais pour le débogage, cela peut être utile.
        try:
            if prn_gen_has_error and prn_gen_has_error(gen_ptr):
                c_error_str = prn_gen_error_string(gen_ptr)
                if c_error_str:
                    _module_logger.error(f"  Erreur supplémentaire via prn_gen_error_string: {c_error_str.decode('utf-8', errors='replace')}")
        except Exception as e_aux:
            _module_logger.error(f"  Exception lors de la tentative de récupération d'erreur auxiliaire: {e_aux}")
        return None
    finally:
        # Libérer la mémoire allouée par l'API C pour la structure CApiResult et ses membres.
        # Nous devons passer un POINTEUR à la structure à free_c_api_result.
        if returned_api_result_struct is not None and free_c_api_result:
            _module_logger.debug(f"  Appel de free_c_api_result avec POINTEUR vers la structure retournée.")
            # Utiliser ctypes.byref() pour passer un pointeur vers la structure qui a été retournée par valeur.
            if not free_c_api_result(ctypes.byref(returned_api_result_struct)):
                _module_logger.warning("  free_c_api_result a retourné false (échec de la libération).")
            else:
                _module_logger.info("  Mémoire du résultat API (prn_gen_run_until_complete) libérée avec free_c_api_result.")
        
        _module_logger.debug("Fin de generate_print_file_data.")

def send_print_data_to_laser(machine: EpilogMachine, print_data: bytes, ip_address_str: str) -> bool:
    if not prn_gen_send_file:
        logger.error("Bibliothèque C Epilog non chargée, impossible d'envoyer les données.")
        return False

    # Les données sont déjà en `bytes` Python. Nous avons besoin d'un pointeur vers ces données.
    # ctypes.create_string_buffer crée une copie modifiable, ce qui est sûr.
    # Ou, si print_data est déjà un buffer que l'on peut pointer directement (moins sûr sans copie) :
    # data_ptr = ctypes.cast(print_data, ctypes.POINTER(ctypes.c_ubyte))
    # Pour la sécurité, utilisons create_string_buffer qui alloue et copie.
    
    # Le buffer doit exister pendant l'appel à la fonction C.
    c_buffer = ctypes.create_string_buffer(print_data) # print_data est un objet bytes
    data_ptr = ctypes.cast(c_buffer, ctypes.POINTER(ctypes.c_ubyte))
    data_len = len(print_data)
    
    c_ip_address = ctypes.c_char_p(ip_address_str.encode('utf-8'))

    logger.debug(f"send_print_data_to_laser: recu machine type={type(machine)}, representation={machine}")
    try:
        machine_val_for_c = int(machine) 
        logger.debug(f"send_print_data_to_laser: machine_val_for_c={machine_val_for_c} (type: {type(machine_val_for_c)}) prête pour C.")
    except Exception as e_conv:
        logger.error(f"Erreur lors de la conversion de 'machine' (type: {type(machine)}, valeur: {machine}) en entier pour send_print_data_to_laser: {e_conv}")
        return False 

    logger.info(f"Appel de prn_gen_send_file avec machine={machine_val_for_c}, data_ptr={data_ptr}, data_len={data_len}, ip={ip_address_str}")
    result_bool = prn_gen_send_file(machine_val_for_c, data_ptr, data_len, c_ip_address)
    
    if result_bool:
        logger.info(f"prn_gen_send_file a réussi (retourné true) pour IP {ip_address_str}.")
        return True
    else:
        logger.error(f"prn_gen_send_file a échoué (retourné false) pour IP {ip_address_str}.")
        return False

# Gestionnaire de contexte pour PrnGen pour assurer la libération
class PrnGeneratorContext:
    def __init__(self, svg_content: str, settings_json_content: str, machine: EpilogMachine):
        self.svg_content = svg_content
        self.settings_json_content = settings_json_content
        self.machine = machine
        self.gen_ptr = None
        self.svg_data_bytes_ref = None       # Pour maintenir l'objet bytes en vie
        self.settings_json_bytes_ref = None  # Pour maintenir l'objet bytes en vie

    def __enter__(self) -> PrnGen_p | None:
        # create_prn_generator retourne maintenant un tuple
        self.gen_ptr, self.svg_data_bytes_ref, self.settings_json_bytes_ref = \
            create_prn_generator(self.svg_content, self.settings_json_content, self.machine)
        
        if self.gen_ptr:
            logger.info(f"PrnGeneratorContext: Générateur PrnGen créé avec succès: {self.gen_ptr}. Références aux données SVG/JSON conservées.")
        else:
            logger.error("PrnGeneratorContext: Échec de la création du générateur PrnGen.")
            # Les refs bytes seront None, ce qui est OK.
        return self.gen_ptr

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.gen_ptr:
            destroy_prn_generator(self.gen_ptr)
            logger.info("PrnGeneratorContext: Générateur PrnGen libéré.")
        self.gen_ptr = None
        self.svg_data_bytes_ref = None       # Relâcher la référence
        self.settings_json_bytes_ref = None  # Relâcher la référence


if __name__ == '__main__':
    if epilog_api_lib:
        print(f"Version de l'API Epilog (via C++): {get_api_version()}")
        # Test basique pour voir si on peut appeler une fonction simple
    else:
        print("Bibliothèque C++ non chargée, impossible de tester.") 