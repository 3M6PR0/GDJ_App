import json
import os
import logging
import copy
from utils.paths import get_resource_path

logger = logging.getLogger(__name__)

class ConfigData:
    """
    Singleton class to load and provide read-only access to config_data.json.

    Loads data upon first instantiation and provides access via properties
    or methods.
    """
    _instance = None
    _initialized = False
    _config_file_path = "data/config_data.json" # Relative path within resources

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            logger.debug("Creating new ConfigData Singleton instance.")
        return cls._instance

    def __init__(self):
        """
        Initializes the Singleton instance by loading data only once.
        """
        if self._initialized:
            return
        
        self._data = {}
        self.__load_data()
        self._initialized = True
        logger.info(f"ConfigData Singleton initialized (Loaded from: {self._config_file_path}).")

    def __load_data(self):
        """
        Loads data from the JSON configuration file.
        Handles file not found and JSON decoding errors.
        """
        try:
            config_path_abs = get_resource_path(self._config_file_path)
            if os.path.exists(config_path_abs):
                with open(config_path_abs, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"Configuration data loaded successfully from {config_path_abs}")
            else:
                logger.error(f"Config file not found at resolved path: {config_path_abs}")
                self._data = {} # Ensure data is empty dict if file not found
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {config_path_abs}: {e}")
            self._data = {} # Ensure data is empty dict on decode error
        except Exception as e:
            logger.error(f"Failed to load or parse configuration data from {self._config_file_path}: {e}", exc_info=True)
            self._data = {} # Ensure data is empty dict on other errors

    @classmethod
    def get_instance(cls):
        """
        Returns the single instance of the ConfigData class.
        Creates it if it doesn't exist yet.
        """
        return cls() # Calls __new__ and __init__ (if not initialized)

    # --- Read-only accessors ---

    @property
    def document_types(self) -> list[str]:
        """
        Returns a list of document type names defined in the config.
        Returns an empty list if data is missing or loading failed.
        """
        return self._data.get("document_types", [])

    def get_fields_for_type(self, doc_type: str) -> list[str]:
        """
        Returns the list of field names for a specific document type.
        Returns an empty list if the type is not found or data is missing.
        """
        if not isinstance(doc_type, str):
            logger.warning(f"get_fields_for_type called with non-string type: {type(doc_type)}")
            return []
        return self._data.get("document_types", {}).get(doc_type, [])

    @property
    def all_data(self) -> dict:
        """
        Returns a deep copy of the entire loaded configuration data.
        Useful for debugging or accessing less common parts of the config.
        The returned dictionary is a copy, so modifying it won't affect
        the Singleton's internal state.
        """
        return copy.deepcopy(self._data)

    def get_top_level_key(self, key: str, default=None):
        """
        Safely gets a value from a top-level key in the config data.

        Args:
            key (str): The top-level key to retrieve.
            default: The value to return if the key is not found. Defaults to None.

        Returns:
            The value associated with the key, or the default value.
        """
        return self._data.get(key, default)

# Optional: Pre-instantiate on module load if desired,
# otherwise instantiation happens on first call to get_instance()
# config_instance = ConfigData.get_instance()

logger.info("models/config_data.py loaded.") 