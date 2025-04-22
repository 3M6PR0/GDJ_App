# controllers/about/about_readme_controller.py # <- Nouveau nom
# Contient la logique pour charger et afficher le fichier README.md.

import os
import re
import markdown
from PyQt5.QtCore import QObject

# --- Import de la fonction utilitaire --- 
from utils.paths import get_resource_path 

# Import de la vue correspondante (ajuster si nécessaire)
# from pages.about.about_readme_page import AboutReadmePage

# --- Constante pour le chemin relatif --- 
README_PATH = "README.md"

class AboutReadmeController(QObject):
    def __init__(self, view: 'QWidget', version_str: str = "?.?.?", parent=None):
        super().__init__(parent)
        self.view = view
        self.version_str = version_str
        self.load_and_process_readme()

    def load_and_process_readme(self):
        """Charge README via get_resource_path, injecte badge, et convertit."""
        html_content = "<p>Chargement...</p>"
        try:
            # --- Charger le README en utilisant get_resource_path --- 
            readme_full_path = get_resource_path(README_PATH)
            print(f"DEBUG: Chemin README calculé: {readme_full_path}") # Ajout debug
            if os.path.exists(readme_full_path):
                with open(readme_full_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                # --- "Tricher" : Définir les couleurs en dur ici ---
                accent_color = "#0054b8"  # Valeur de ACCENT_COLOR
                primary_dark_color = "#313335" # Valeur de COLOR_PRIMARY_DARK
                
                # --- Préparer le HTML du badge AVEC STYLES EN LIGNE et couleurs en dur ---
                badge_html = f'''<table style="display: inline-block; border-collapse: collapse; border-spacing: 0; line-height: 1.2; font-size: 8pt; font-weight: bold; vertical-align: middle; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
<tr>
<td style="background-color: {primary_dark_color}; color: white; padding: 3px 6px;">Version</td>
<td style="background-color: {accent_color}; color: white; padding: 3px 6px;">{self.version_str}</td>
</tr>
</table>'''
                
                # --- Remplacer le placeholder Markdown ---
                badge_line_pattern = r'^\s*\[!\[Version\]\(https://img\.shields\.io/badge/Version-.*\)\]\(\)\s*$\n'
                markdown_content_with_badge = re.sub(badge_line_pattern, badge_html + '\n\n', markdown_content, flags=re.MULTILINE)
                
                # --- Convertir Markdown en HTML ---
                html_content = markdown.markdown(markdown_content_with_badge, extensions=['fenced_code', 'tables', 'nl2br'])

            else:
                html_content = f"<p style='color: red;'>Fichier non trouvé: {readme_full_path}</p>"
        
        except ImportError as ie:
             html_content = f"<p style='color: red;'>Erreur d'importation : {ie}. La bibliothèque 'markdown' ou 're' est-elle installée?</p>"
             print(f"Erreur Import: {ie}")
        except Exception as e:
            html_content = f"<p style='color: red;'>Erreur lors du chargement ou traitement de README.md: {e}</p>"
            print(f"Erreur README processing: {e}")
        
        # Passer le HTML final (badge avec styles en ligne) à la vue
        if hasattr(self.view, 'set_content'):
            self.view.set_content(html_content)
        else:
            print("ERREUR: La vue AboutReadmePage n'a pas de méthode set_content")

    print("AboutReadmeController initialized and processing README") # Debug 