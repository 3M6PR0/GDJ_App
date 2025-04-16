# hooks/hook-update_helper.py
# Fichier hook personnalisé pour aider PyInstaller avec update_helper.py et pywin32

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, get_module_file_attribute

# Collecte les sous-modules importants (win32api, win32con, etc.)
hiddenimports = collect_submodules('win32')
# pywintypes est essentiel et parfois traité séparément
hiddenimports += collect_submodules('pywintypes')

# Collecte les DLLs associées à pywin32 et pywintypes
# Ceci est souvent la partie la plus délicate
binaries = collect_dynamic_libs('win32')
binaries += collect_dynamic_libs('pywintypes')

# Vérification (affichage dans les logs de PyInstaller)
print("-" * 20)
print(f"Hook pour update_helper: Imports cachés collectés : {hiddenimports}")
print(f"Hook pour update_helper: Binaires collectés : {binaries}")
print("-" * 20) 