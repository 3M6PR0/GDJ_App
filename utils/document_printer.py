from fpdf import FPDF
from typing import TYPE_CHECKING, List
import os # Ajout pour la gestion des chemins

# --- Importation conditionnelle pour éviter les dépendances circulaires lors de la vérification des types ---
if TYPE_CHECKING:
    from models.document import Document # Classe de base hypothétique
    from models.documents.rapport_depense.rapport_depense import RapportDepense
    from models.documents.rapport_depense.deplacement import Deplacement
    from models.documents.rapport_depense.repas import Repas
    from models.documents.rapport_depense.depense import Depense
    # from models.documents.autre_type.autre_type import AutreTypeDocument # Pour le futur

class DocumentPDFPrinter:
    """Gère la génération de PDF pour différents types de documents."""

    def __init__(self):
        self.col_widths = [] # Sera défini dans chaque méthode de section de tableau

    def _set_default_font(self, pdf: FPDF, style="", size=10):
        # Utiliser Arial. Si FPDF2 la trouve comme police système TTF, support Unicode amélioré.
        # Sinon, il utilisera la police "core" Helvetica (encodage cp1252 par défaut, qui inclut €).
        pdf.set_font("Arial", style, size)

    def _add_header_footer(self, pdf: FPDF, rapport: 'RapportDepense'):
        # En-tête personnalisé (peut être appelé par add_page ou manuellement)
        # Pour l'instant, nous le construisons directement après add_page
        pass

    def _add_rapport_info_table(self, pdf: FPDF, rapport: 'RapportDepense'):
        """Ajoute un tableau avec les informations générales du rapport et de l'employé."""
        line_height = 7
        # self._set_default_font(pdf, "B") # La police sera définie ci-dessous avec la taille
        
        # Cadre autour des informations
        start_x = pdf.get_x()
        start_y = pdf.get_y()

        info_data = [
            ("Employé:", f"{rapport.prenom_employe} {rapport.nom_employe}"),
            ("Département:", rapport.departement),
            ("Emplacement:", rapport.emplacement),
            ("Superviseur:", rapport.superviseur),
            ("Date du Rapport:", rapport.date_rapport.strftime("%d/%m/%Y")),
            ("Plafond Déplacement:", rapport.plafond_deplacement),
        ]

        # Calcul de la largeur des colonnes
        # Max width for labels to align values
        # temp_label_widths = [pdf.get_string_width(label) for label, value in info_data]
        # max_label_width = max(temp_label_widths) + 2 # Add some padding

        # Pour une disposition en deux colonnes de paires label/valeur
        # La largeur totale disponible est pdf.w - pdf.l_margin - pdf.r_margin
        available_width = pdf.w - pdf.l_margin - pdf.r_margin
        label_col_width = 45 # Fixe pour les étiquettes
        value_col_width = available_width - label_col_width - 5 # Le reste pour la valeur, avec un petit espace

        for label, value in info_data:
            current_x = pdf.get_x()
            current_y = pdf.get_y()
            pdf.set_font("Arial", "B", 9)
            pdf.cell(label_col_width, line_height, txt=label, border=0, ln=0, align="L")
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(value_col_width, line_height, txt=str(value), border=0, ln=1, align="L") # Utiliser multi_cell pour les valeurs longues
            if pdf.get_y() > current_y + line_height : # Si multi_cell a fait un saut de ligne interne
                 pdf.ln(line_height/2) # Espace supplémentaire
        
        # Dessiner un cadre autour du bloc d'informations
        # end_y = pdf.get_y()
        # pdf.rect(start_x, start_y, available_width, end_y - start_y)
        pdf.ln(5)


    def _add_table_header(self, pdf: FPDF, headers: List[str], col_widths: List[float]):
        self._set_default_font(pdf, "B", 9)
        pdf.set_fill_color(220, 220, 220) # Gris clair pour l'en-tête
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 7, header, border=1, ln=0, align="C", fill=True)
        pdf.ln()

    def _add_table_row(self, pdf: FPDF, data: List[str], col_widths: List[float], line_height=6):
        self._set_default_font(pdf, "", 7) # Police par défaut pour les lignes, taille ajustée
        
        # 1. Calculer la hauteur nécessaire pour la ligne
        num_lines_per_cell = []
        for i, item_data in enumerate(data):
            try:
                lines = pdf.get_num_lines(str(item_data), col_widths[i])
                num_lines_per_cell.append(lines)
            except Exception as e:
                print(f"Avertissement: pdf.get_num_lines a échoué: {e}. Hauteur de ligne fixe.")
                num_lines_per_cell.append(1)

        max_lines = max(num_lines_per_cell) if num_lines_per_cell else 1
        calculated_line_height = max_lines * line_height

        # 2. Sauvegarder la position Y actuelle et X de départ de la ligne
        initial_x = pdf.get_x() # X au début de la ligne (souvent marge gauche)
        current_y = pdf.get_y()

        # 3. Dessiner le texte de chaque cellule avec multi_cell (sans bordure)
        # Et en même temps, dessiner les bordures avec pdf.rect()
        current_x_pos = initial_x
        for i, item_data in enumerate(data):
            # Positionner le curseur pour cette cellule
            pdf.set_xy(current_x_pos, current_y)
            
            # Dessiner le texte avec multi_cell
            pdf.multi_cell(w=col_widths[i], 
                           h=line_height, # Hauteur de chaque ligne DANS la cellule
                           txt=str(item_data), 
                           border=0,      # PAS de bordure par multi_cell
                           align='L', 
                           ln=0,          # Important: ne pas faire de saut de ligne automatique APRÈS la cellule
                           max_line_height=line_height,
                           fill=False)     # S'assurer que le fond n'est pas rempli par multi_cell

            # Dessiner la bordure pour CETTE cellule avec la hauteur calculée pour toute la ligne
            pdf.rect(current_x_pos, current_y, col_widths[i], calculated_line_height)

            # Mettre à jour current_x_pos pour la prochaine cellule
            current_x_pos += col_widths[i]
        
        # 4. Avancer le curseur Y pour la prochaine ligne du tableau
        # Se positionner au début de la ligne suivante (marge gauche) et à la bonne hauteur
        pdf.set_xy(initial_x, current_y + calculated_line_height)


    def _add_section_title(self, pdf: FPDF, title: str):
        pdf.ln(5) # Espace avant le titre de section
        self._set_default_font(pdf, "B", 12)
        pdf.set_fill_color(200, 220, 255) # Couleur de fond pour le titre de section
        pdf.cell(0, 8, title, border=1, ln=1, align="L", fill=True)
        pdf.ln(2) # Petit espace après le titre de section

    def _add_deplacements_section(self, pdf: FPDF, deplacements: List['Deplacement']):
        if not deplacements: return
        self._add_section_title(pdf, "Déplacements")
        
        headers = ["Date", "Client", "Ville", "N° Comm.", "Km", "Montant (€)"]
        # Définir les largeurs des colonnes (ajuster selon le contenu)
        # Page width A4 = 210mm. Margins default 10mm left/right. Usable width = 190mm
        total_width = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [total_width * 0.15, total_width * 0.25, total_width * 0.20, total_width * 0.15, total_width * 0.10, total_width * 0.15]
        self.col_widths = col_widths # Sauvegarder pour les lignes

        self._add_table_header(pdf, headers, self.col_widths)
        total_deplacements = 0.0
        pdf.set_font("Arial", "", 8)
        for dep in deplacements:
            data = [
                dep.date.strftime("%d/%m/%Y"),
                dep.client,
                dep.ville,
                dep.numero_commande,
                f"{dep.kilometrage:.2f}",
                f"{dep.montant:.2f}"
            ]
            self._add_table_row(pdf, data, self.col_widths)
            total_deplacements += dep.montant
        
        # Ligne de total pour la section
        pdf.set_font("Arial", "B", 8)
        pdf.cell(sum(col_widths[:-1]), 6, "Total Déplacements", border=1, align="R")
        pdf.cell(col_widths[-1], 6, f"{total_deplacements:.2f} €", border=1, ln=1, align="R")
        return total_deplacements

    def _add_repas_section(self, pdf: FPDF, repas_list: List['Repas']):
        if not repas_list: return
        self._add_section_title(pdf, "Repas")
        
        headers = [
            "Date", "Description", "Restaurant", "Client", "N° Cmd", 
            "Réf.?", "Payé Empl.",
            "Total Fact.(€)", "Pourboire(€)", "TPS(€)", "TVQ/TVH(€)", "Montant Remb.(€)"
        ]
        
        total_width = pdf.w - pdf.l_margin - pdf.r_margin
        # Ajustement des largeurs pour 12 colonnes - cela sera serré
        col_widths = [
            total_width * 0.07, # Date
            total_width * 0.15, # Description
            total_width * 0.10, # Restaurant
            total_width * 0.10, # Client
            total_width * 0.07, # N° Cmd
            total_width * 0.05, # Réf.?
            total_width * 0.07, # Payé Empl. (payeur)
            total_width * 0.09, # Total Fact.
            total_width * 0.08, # Pourboire
            total_width * 0.07, # TPS
            total_width * 0.08, # TVQ/TVH
            total_width * 0.07  # Montant Remb. (employe)
        ]
        # Recalculer pour s'assurer que la somme est proche de total_width si nécessaire, ou ajuster manuellement.
        # Pour l'instant, on fait confiance à cette répartition.

        self.col_widths = col_widths

        self._add_table_header(pdf, headers, self.col_widths)
        total_repas_employe_rembourser = 0.0
        pdf.set_font("Arial", "", 7) # Taille de police plus petite pour plus de colonnes

        for rep in repas_list:
            payeur_str = "Oui" if rep.payeur else "Non" # Si l'employé a payé initialement
            refacturer_str = "Oui" if rep.refacturer else "Non"
            
            # Pour TVQ/TVH, on peut les sommer si une seule est présente, ou afficher celle qui est non-nulle.
            tvq_tvh_str = ""
            if rep.tvq > 0 and rep.tvh > 0:
                tvq_tvh_str = f"{rep.tvq:.2f}/{rep.tvh:.2f}" # Les deux? Rare.
            elif rep.tvq > 0:
                tvq_tvh_str = f"{rep.tvq:.2f}"
            elif rep.tvh > 0:
                tvq_tvh_str = f"{rep.tvh:.2f}"
            else:
                tvq_tvh_str = "0.00"

            data = [
                rep.date.strftime("%d/%m/%y"), # Date plus courte
                rep.description,
                rep.restaurant,
                rep.client,
                rep.numero_commande,
                refacturer_str,
                payeur_str,
                f"{rep.totale_apres_taxes:.2f}",
                f"{rep.pourboire:.2f}",
                f"{rep.tps:.2f}",
                tvq_tvh_str,
                f"{rep.employe:.2f}" # Montant à rembourser à l'employé
            ]
            self._add_table_row(pdf, data, self.col_widths, line_height=5) # line_height réduite
            
            # Le montant à rembourser est directement rep.employe
            total_repas_employe_rembourser += rep.employe
        
        pdf.set_font("Arial", "B", 8)
        # Total pour la section
        # Identifier la colonne du montant à rembourser (la dernière)
        desc_total_width = sum(col_widths[:-1])
        montant_col_width = col_widths[-1]

        pdf.cell(desc_total_width, 6, "Total Repas à Rembourser (Employé)", border="T", align="R") # Bordure Top seulement
        pdf.cell(montant_col_width, 6, f"{total_repas_employe_rembourser:.2f} €", border="T", ln=1, align="R")
        return total_repas_employe_rembourser

    def _add_depenses_diverses_section(self, pdf: FPDF, depenses_list: List['Depense']):
        if not depenses_list: return
        self._add_section_title(pdf, "Dépenses Diverses")
        
        headers = [
            "Date", "Type", "Description", "Fournisseur", "Payé Empl.?",
            "Total Fact.(€)", "TPS(€)", "TVQ/TVH(€)", "Montant Remb.(€)"
        ]
        total_width = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [
            total_width * 0.10, # Date
            total_width * 0.12, # Type
            total_width * 0.23, # Description
            total_width * 0.15, # Fournisseur
            total_width * 0.10, # Payé Empl.?
            total_width * 0.10, # Total Fact.
            total_width * 0.07, # TPS
            total_width * 0.06, # TVQ/TVH
            total_width * 0.07  # Montant Remb.
        ]
        self.col_widths = col_widths

        self._add_table_header(pdf, headers, self.col_widths)
        total_depenses_diverses_employe_rembourser = 0.0
        pdf.set_font("Arial", "", 7) # Taille de police plus petite

        for dep in depenses_list:
            payeur_str = "Oui" if dep.payeur else "Non"
            
            tvq_tvh_str = ""
            if dep.tvq > 0 and dep.tvh > 0:
                tvq_tvh_str = f"{dep.tvq:.2f}/{dep.tvh:.2f}"
            elif dep.tvq > 0:
                tvq_tvh_str = f"{dep.tvq:.2f}"
            elif dep.tvh > 0:
                tvq_tvh_str = f"{dep.tvh:.2f}"
            else:
                tvq_tvh_str = "0.00"

            data = [
                dep.date.strftime("%d/%m/%y"), # Date plus courte
                dep.type_depense,
                dep.description,
                dep.fournisseur,
                payeur_str,
                f"{dep.totale_apres_taxes:.2f}",
                f"{dep.tps:.2f}",
                tvq_tvh_str,
                f"{dep.employe:.2f}" # Montant à rembourser à l'employé
            ]
            self._add_table_row(pdf, data, self.col_widths, line_height=5) # line_height réduite
            
            total_depenses_diverses_employe_rembourser += dep.employe

        pdf.set_font("Arial", "B", 8)
        desc_total_width = sum(col_widths[:-1])
        montant_col_width = col_widths[-1]

        pdf.cell(desc_total_width, 6, "Total Dépenses Diverses à Rembourser (Employé)", border="T", align="R")
        pdf.cell(montant_col_width, 6, f"{total_depenses_diverses_employe_rembourser:.2f} €", border="T", ln=1, align="R")
        return total_depenses_diverses_employe_rembourser

    def _add_totaux_section(self, pdf: FPDF, total_deplacements: float, total_repas: float, total_divers: float):
        self._add_section_title(pdf, "Totaux à Rembourser")
        
        grand_total = total_deplacements + total_repas + total_divers
        
        line_height = 8
        col_width_desc = (pdf.w - pdf.l_margin - pdf.r_margin) * 0.75
        col_width_montant = (pdf.w - pdf.l_margin - pdf.r_margin) * 0.25

        pdf.set_font("Arial", "", 10)
        pdf.cell(col_width_desc, line_height, "Total Déplacements:", border="T L B", align="R")
        pdf.cell(col_width_montant, line_height, f"{total_deplacements:.2f} €", border="T R B", ln=1, align="R")
        
        pdf.cell(col_width_desc, line_height, "Total Repas (part Employé):", border="L B", align="R")
        pdf.cell(col_width_montant, line_height, f"{total_repas:.2f} €", border="R B", ln=1, align="R")

        pdf.cell(col_width_desc, line_height, "Total Dépenses Diverses (part Employé):", border="L B", align="R")
        pdf.cell(col_width_montant, line_height, f"{total_divers:.2f} €", border="R B", ln=1, align="R")

        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(col_width_desc, line_height + 2, "MONTANT TOTAL À REMBOURSER:", border=1, align="R", fill=True)
        pdf.cell(col_width_montant, line_height + 2, f"{grand_total:.2f} €", border=1, ln=1, align="R", fill=True)


    def generate(self, document, output_path: str): # L'annotation de type pour 'document' sera ajoutée après les imports réels
        """
        Génère un PDF pour le document fourni.
        Détecte le type de document et appelle la méthode de génération appropriée.
        """
        # --- Importations réelles ici pour l'exécution ---
        # Ceci est fait pour éviter les importations circulaires au niveau du module
        # si DocumentPDFPrinter est importé dans les modules de documents eux-mêmes.
        from models.document import Document # Assurez-vous que cette classe de base existe et est pertinente
        from models.documents.rapport_depense.rapport_depense import RapportDepense
        # from models.documents.autre_type.autre_type import AutreTypeDocument # Pour le futur

        if isinstance(document, RapportDepense):
            self._generate_rapport_depense_pdf(document, output_path)
        # elif isinstance(document, AutreTypeDocument):
        #     self._generate_autre_type_pdf(document, output_path)
        else:
            # Tenter d'obtenir le nom de la classe de manière sûre
            doc_type_name = type(document).__name__ if hasattr(type(document), '__name__') else str(type(document))
            raise ValueError(f"Type de document non supporté pour l'impression PDF: {doc_type_name}")

    def _generate_rapport_depense_pdf(self, rapport: 'RapportDepense', output_path: str):
        """Génère un PDF style facture pour un objet RapportDepense."""
        pdf = FPDF()
        
        # --- Ajout explicite des polices Arial standards de Windows ---
        # FPDF2 utilisera ces fichiers TTF, qui devraient supporter l'Euro.
        # Les chemins sont typiques pour Windows; ajuster si nécessaire pour d'autres OS.
        # FPDF2 cherche aussi dans des répertoires de polices système connus.
        # Le nom de la police ("Arial") doit correspondre à celui utilisé dans set_font().
        font_path_regular = "C:/Windows/Fonts/arial.ttf"
        font_path_bold = "C:/Windows/Fonts/arialbd.ttf"
        font_path_italic = "C:/Windows/Fonts/ariali.ttf"
        font_path_bold_italic = "C:/Windows/Fonts/arialbi.ttf"

        try:
            # Le paramètre 'uni=True' est obsolète dans FPDF2 >= 2.5.2 (UTF-8 est par défaut pour les TTF)
            # mais ne nuit pas. FPDF2 s'attend à ce que les TTF soient encodées en UTF-8.
            pdf.add_font("Arial", "", font_path_regular)
            pdf.add_font("Arial", "B", font_path_bold)
            pdf.add_font("Arial", "I", font_path_italic)
            pdf.add_font("Arial", "BI", font_path_bold_italic)
            print("Polices Arial TTF ajoutées avec succès.")
        except Exception as e_font:
            print(f"AVERTISSEMENT: Impossible d'ajouter les polices Arial TTF depuis C:/Windows/Fonts/: {e_font}.")
            print("FPDF utilisera les polices 'core' par défaut, le symbole € pourrait manquer ou être incorrect.")
            # Si l'ajout échoue, on continue, FPDF utilisera ses polices de base (Helvetica etc.)

        # pdf.set_auto_page_break(auto=True, margin=15) # Marge du bas pour le pied de page
        pdf.add_page()
        
        # --- En-tête avec Logo et Titre ---
        logo_path = "resources/images/logo-jacmar.png"
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=10, y=8, w=30) # Ajuster w et h selon le logo
        else:
            print(f"Attention: Logo non trouvé à {logo_path}")

        page_width = pdf.w - pdf.l_margin - pdf.r_margin
        
        pdf.set_font("Arial", "B", 18) # Utiliser Arial pour le titre aussi
        pdf.set_xy(0, 15) # Positionner le titre un peu plus bas
        pdf.cell(page_width, 10, "Remboursement de dépenses", 0, 1, "C")
        pdf.ln(10) # Espace après le titre principal
        
        # --- Informations du rapport et de l'employé ---
        self._add_rapport_info_table(pdf, rapport) # Nouvelle méthode pour ce bloc

        # --- Sections des dépenses ---
        # Les totaux partiels sont retournés par chaque méthode de section
        total_deplacements = self._add_deplacements_section(pdf, rapport.deplacements) or 0.0
        total_repas = self._add_repas_section(pdf, rapport.repas) or 0.0
        total_depenses_diverses = self._add_depenses_diverses_section(pdf, rapport.depenses_diverses) or 0.0
        
        # --- Section des Totaux ---
        self._add_totaux_section(pdf, total_deplacements, total_repas, total_depenses_diverses)

        try:
            pdf.output(output_path, "F")
            print(f"Le PDF du rapport de dépense a été généré : {output_path}")
        except Exception as e:
            print(f"Erreur lors de la génération du PDF : {e}")
            # import traceback
            # traceback.print_exc() # Pour plus de détails sur l'erreur
            raise # Remonter l'erreur pour que l'appelant soit informé

    # def _generate_autre_type_pdf(self, autre_doc: 'AutreTypeDocument', output_path: str):
    #     # Logique pour un autre type de document
    #     pass 