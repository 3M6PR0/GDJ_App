# controllers/about/about_readme_controller.py # <- Nouveau nom
# Contient la logique pour charger et afficher le fichier README.md.

import os
import re
import markdown
from PyQt5.QtCore import QObject
# Récupérer la couleur d'accentuation depuis une source centrale si possible,
# sinon la définir ici ou la passer en argument.
# Supposons qu'elle est accessible via une constante ou config
try:
    # Tentative d'importer depuis config.py à la racine
    import sys
    # Ajouter la racine du projet au path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from config import ACCENT_COLOR # Supposons que ACCENT_COLOR est défini dans config.py
except ImportError:
    print("Avertissement: Impossible d'importer ACCENT_COLOR depuis config.py. Utilisation d'une couleur par défaut.")
    ACCENT_COLOR = "#0054b8" # Couleur par défaut si l'import échoue

# Import de la vue correspondante (ajuster si nécessaire)
# from pages.about.about_readme_page import AboutReadmePage

README_PATH = "README.md" # Chemin relatif depuis la racine du projet

class AboutReadmeController(QObject):
    def __init__(self, view: 'QWidget', version_str: str = "?.?.?", parent=None):
        super().__init__(parent)
        self.view = view
        self.version_str = version_str # Stocker la version
        self.load_and_process_readme()

    def load_and_process_readme(self):
        """Charge, traite (badge) et convertit le README en HTML."""
        html_content = "<p>Chargement...</p>"
        try:
            # Construire le chemin absolu
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            readme_full_path = os.path.join(script_dir, README_PATH)
            
            if os.path.exists(readme_full_path):
                with open(readme_full_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                # Utiliser une table HTML pour simuler le badge (comme dans welcome_page)
                badge_html = f'''<table style="display: inline-block; border-collapse: collapse; border-spacing: 0; line-height: 1.2; font-size: 8pt; font-weight: bold; vertical-align: middle; border-radius: 4px; overflow: hidden;">\
<tr>\
<td style="background-color: #555; color: white; padding: 3px 6px;">Version</td>\
<td style="background-color: {ACCENT_COLOR}; color: white; padding: 3px 6px;">{self.version_str}</td>\
</tr>\
</table>'''
                
                # Remplacer la ligne du badge Markdown par le HTML simulé
                badge_line_pattern = r'^\s*\[!\[Version\]\(https://img\.shields\.io/badge/Version-.*\)\]\(\)\s*$\n'
                markdown_content_with_badge = re.sub(badge_line_pattern, badge_html + '\n\n', markdown_content, flags=re.MULTILINE)
                
                # Convertir le markdown (qui contient maintenant notre HTML) en HTML final
                html_content = markdown.markdown(markdown_content_with_badge, extensions=['fenced_code', 'tables', 'nl2br'])

            else:
                html_content = f"<p style='color: red;'>Fichier non trouvé: {readme_full_path}</p>"
        except ImportError as ie:
             html_content = f"<p style='color: red;'>Erreur d'importation : {ie}. La bibliothèque 'markdown' ou 're' est-elle installée?</p>"
             print(f"Erreur Import: {ie}")
        except Exception as e:
            html_content = f"<p style='color: red;'>Erreur lors du chargement ou traitement de README.md: {e}</p>"
            print(f"Erreur README processing: {e}")
        
        # Passer le HTML final à la vue
        if hasattr(self.view, 'set_content'):
            self.view.set_content(html_content)
        else:
            print("ERREUR: La vue AboutReadmePage n'a pas de méthode set_content")

    print("AboutReadmeController initialized and processing README") # Debug 