from weasyprint import HTML, CSS
# from weasyprint.fonts import FontConfiguration # Ancienne importation incorrecte
from weasyprint.text.fonts import FontConfiguration # Importation corrigée
from typing import TYPE_CHECKING, List
import os

# --- AJOUT DE L'IMPORTATION POUR CONFIG_DATA ---
from models.config_data import ConfigData
# --------------------------------------------

# --- Importation conditionnelle pour éviter les dépendances circulaires ---
if TYPE_CHECKING:
    from models.document import Document # Classe de base hypothétique
    from models.documents.rapport_depense.rapport_depense import RapportDepense
    from models.documents.rapport_depense.deplacement import Deplacement
    from models.documents.rapport_depense.repas import Repas
    from models.documents.rapport_depense.depense import Depense

class DocumentPDFPrinter:
    """Gère la génération de PDF pour différents types de documents en utilisant HTML et WeasyPrint."""

    def _get_base_css(self) -> str:
        """Retourne les styles CSS de base pour le document."""
        # Styles CSS pour la facture. Peuvent être étendus.
        return """
            @page {
                size: A4;
                margin: 1.5cm;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10pt;
                }
            }
            body {
                font-family: 'Arial', sans-serif; /* Utiliser une police commune */
                font-size: 10pt;
                color: #333;
            }
            .header-container {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 20px;
                border-bottom: 2px solid #007bff; /* Couleur bleue Jacmar */
                padding-bottom: 10px;
            }
            .header-container img.logo {
                max-height: 70px; /* Ajuster selon la taille du logo */
                max-width: 250px; /* Ajuster */
            }
            .header-container .title {
                text-align: right;
            }
            .header-container h1 {
                color: #007bff; /* Couleur bleue Jacmar */
                margin: 0;
                font-size: 24pt;
                font-weight: bold;
            }
            .header-container .user-info p {
                margin: 2px 0;
                font-size: 9pt;
                text-align: right;
            }
            .rapport-info-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 25px;
            }
            .rapport-info-table th, .rapport-info-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                font-size: 9pt;
            }
            .rapport-info-table th {
                background-color: #f2f2f2; /* Fond gris clair pour les en-têtes de tableau d'info */
                width: 30%;
                font-weight: bold;
            }
            .section-title {
                font-size: 16pt;
                color: #0056b3; /* Bleu plus foncé */
                margin-top: 20px;
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid #0056b3;
            }
            table.data-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 7.5pt; /* MODIFIÉ: 8pt -> 7.5pt. Taille de police plus petite pour les tableaux de données */
                table-layout: fixed; /* Force les largeurs de colonnes à être respectées */
            }
            table.data-table th, table.data-table td {
                border: 1px solid #ccc;
                padding: 4px; /* Léger ajustement du padding */
                text-align: center; /* MODIFIÉ: left -> center */
                word-wrap: break-word; /* Permet au texte de wrapper */
                overflow-wrap: break-word; /* Alternative moderne pour word-wrap */
                vertical-align: middle; /* MODIFIÉ: top -> middle */
            }
            table.data-table th {
                background-color: #e9ecef; /* Fond gris très clair pour les en-têtes de tableau de données */
                font-weight: bold;
                padding-top: 8px;
                padding-bottom: 8px;
            }
            table.data-table td.montant {
                text-align: right; /* Les données des montants restent à droite */
            }
            table.data-table th.montant {
                text-align: center; /* Les en-têtes des colonnes de montants sont maintenant centrés */
            }
            table.data-table td.date-cell {
                white-space: nowrap; /* Empêche le retour à la ligne pour les dates */
                padding-left: 6px; /* Augmentation du padding gauche */
                padding-right: 6px; /* Augmentation du padding droit */
            }
            .totals-section {
                margin-top: 30px;
                padding-top: 15px;
                border-top: 2px solid #007bff;
            }
            .totals-section table {
                width: 40%; /* Tableau des totaux moins large */
                float: right; /* Aligner à droite */
                border-collapse: collapse;
            }
            .totals-section th, .totals-section td {
                padding: 8px;
                text-align: right;
                font-size: 10pt;
            }
            .totals-section th {
                text-align: right;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            .totals-section td.grand-total {
                font-weight: bold;
                font-size: 12pt;
                color: #007bff;
            }
            .footer {
                text-align: center;
                font-size: 8pt;
                color: #777;
                margin-top: 30px;
                padding-top: 10px;
                border-top: 1px solid #eee;
            }
            /* Empêcher la coupure des lignes de tableau au milieu */
            table.data-table tr {
                page-break-inside: avoid;
            }
        """

    def _generate_header_html(self, rapport: 'RapportDepense') -> str:
        """Génère le HTML pour l'en-tête du document (logo, titre, infos utilisateur)."""
        logo_path = os.path.abspath("resources/images/logo-jacmar.png")
        # Vérifier si le logo existe, sinon ne pas l'inclure ou mettre un placeholder
        logo_img_html = f'<img src="file:///{logo_path}" alt="Logo Jacmar" class="logo">' if os.path.exists(logo_path) else '<p>Logo non trouvé</p>'
        
        user_info_html = f"""
            <div class="user-info">
                <p>{rapport.prenom_employe} {rapport.nom_employe.upper()}</p>
                <p>Département: {rapport.departement}</p>
                <p>Emplacement: {rapport.emplacement}</p>
            </div>
        """
        return f"""
            <div class="header-container">
                <div>{logo_img_html}</div>
                <div class="title">
                    <h1>Rapport de Dépenses</h1>
                    {user_info_html}
                </div>
            </div>
        """

    def _generate_rapport_info_table_html(self, rapport: 'RapportDepense') -> str:
        """Génère le HTML pour le tableau d'informations générales du rapport."""
        # Accès sécurisé aux dates de soumission, qui peuvent être None
        date_soumission_str = rapport.date_soumission.strftime('%d/%m/%Y') if hasattr(rapport, 'date_soumission') and rapport.date_soumission else 'N/A'
        statut_str = rapport.statut if hasattr(rapport, 'statut') else 'N/A'

        return f"""
            <table class="rapport-info-table">
                <tr><th>Mois du Rapport:</th><td>{rapport.date_rapport.strftime('%B %Y')}</td></tr>
                <tr><th>Soumis le:</th><td>{date_soumission_str}</td></tr>
                <tr><th>Statut:</th><td>{statut_str}</td></tr>
            </table>
        """

    def _generate_deplacements_html(self, rapport: 'RapportDepense') -> str:
        deplacements = rapport.deplacements
        if not deplacements: return ""

        total_kilometrage = 0
        for item in deplacements:
            if hasattr(item, 'kilometrage') and item.kilometrage is not None:
                total_kilometrage += item.kilometrage

        config = ConfigData.get_instance()

        # Récupérer le taux de remboursement depuis ConfigData
        taux_remboursement_km_str = "0.50" # Valeur par défaut
        try:
            rapport_depense_config = config.get_top_level_key("documents", {}).get("rapport_depense", [])
            if rapport_depense_config and isinstance(rapport_depense_config, list) and len(rapport_depense_config) > 0:
                taux_val = rapport_depense_config[0].get("Taux_remboursement", 0.50)
                taux_remboursement_km_str = f"{float(taux_val):.2f}"
        except Exception as e:
            print(f"Erreur lors de la récupération du taux de remboursement depuis ConfigData: {e}. Utilisation de la valeur par défaut.")

        # Récupérer le nom du plafond de déplacement depuis l'objet RapportDepense
        nom_plafond_deplacement = getattr(rapport, 'plafond_deplacement', None)
        plafond_deplacement_valeur_str = "N/A"

        if nom_plafond_deplacement:
            try:
                jacmar_config = config.get_top_level_key("jacmar", {})
                plafonds_liste = jacmar_config.get("plafond_deplacement", [])
                if plafonds_liste and isinstance(plafonds_liste, list) and len(plafonds_liste) > 0:
                    plafonds_dict = plafonds_liste[0] # Le premier élément est le dictionnaire des plafonds
                    if isinstance(plafonds_dict, dict) and nom_plafond_deplacement in plafonds_dict:
                        valeur_plafond = plafonds_dict[nom_plafond_deplacement]
                        plafond_deplacement_valeur_str = f"{float(valeur_plafond):.2f} $"
                    else:
                        print(f"Le nom de plafond '{nom_plafond_deplacement}' n'a pas été trouvé dans la configuration des plafonds.")
                else:
                    print("La liste plafond_deplacement est vide ou mal configurée dans ConfigData.")
            except Exception as e:
                print(f"Erreur lors de la récupération de la valeur du plafond de déplacement '{nom_plafond_deplacement}' depuis ConfigData: {e}.")
        else:
            print("Aucun nom de plafond de déplacement défini dans l'objet RapportDepense.")

        # Informations au-dessus du tableau, sur une ligne horizontale
        deplacement_info_html = f"""
            <div style="margin-bottom: 10px; font-size: 9pt; display: flex; justify-content: space-around; align-items: center; border: 1px solid #eee; padding: 5px; background-color: #f9f9f9;">
                <span style="margin-right: 15px;"><strong>Distance totale:</strong> {total_kilometrage} km</span>
                <span style="margin-right: 15px;"><strong>Taux remboursement:</strong> {taux_remboursement_km_str} $ / km</span>
                <span><strong>Plafond déplacement:</strong> {plafond_deplacement_valeur_str}</span>
            </div>
        """

        rows_html = ""
        for item in deplacements: # Utiliser la variable locale deplacements
            date_str = item.date.strftime('%d/%m/%y') if hasattr(item, 'date') and item.date else ''
            client_str = item.client if hasattr(item, 'client') else ''
            ville_str = item.ville if hasattr(item, 'ville') else ''
            num_cmd_str = item.numero_commande if hasattr(item, 'numero_commande') and item.numero_commande else '-'
            km_str = f"{item.kilometrage} km" if hasattr(item, 'kilometrage') and item.kilometrage is not None else '0 km'
            
            montant_remb_str = f"{item.montant:.2f} $" if hasattr(item, 'montant') and item.montant is not None else '0.00 $'

            rows_html += f"""
                <tr>
                    <td class="date-cell">{date_str}</td>
                    <td>{client_str}</td>
                    <td>{ville_str}</td>
                    <td>{num_cmd_str}</td>
                    <td class="montant">{km_str}</td>
                    <td class="montant">{montant_remb_str}</td>
                </tr>
            """
        
        # Largeurs de colonnes pour les déplacements (maintenant 6 colonnes)
        # Date (10%), Client (24%), Ville (23%), N° Commande (17%), Kilométrage (13%), Montant (13%) = 100%
        colgroup_html = """
            <colgroup>
                <col style="width: 10%;"> <!-- Date -->
                <col style="width: 24%;"> <!-- Client -->
                <col style="width: 23%;"> <!-- Ville -->
                <col style="width: 17%;"> <!-- N° Commande -->
                <col style="width: 13%;"> <!-- Kilométrage -->
                <col style="width: 13%;"> <!-- Montant -->
            </colgroup>
        """
        return f"""
            <h2 class="section-title">Déplacements</h2>
            {deplacement_info_html}
            <table class="data-table">
                {colgroup_html}
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Client</th>
                        <th>Ville</th>
                        <th>N° Commande</th>
                        <th class="montant">Kilométrage</th>
                        <th class="montant">Montant</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        """

    def _generate_repas_html(self, repas_list: List['Repas']) -> str:
        if not repas_list: return ""
        rows_html = ""
        for item in repas_list:
            date_str = item.date.strftime('%d/%m/%y') if hasattr(item, 'date') and item.date else ''
            resto_str = item.restaurant if hasattr(item, 'restaurant') else ''
            client_str = item.client if hasattr(item, 'client') else ''
            num_cmd_str = item.numero_commande if hasattr(item, 'numero_commande') and item.numero_commande else '-'
            
            refacturer_text = "Oui" if hasattr(item, 'refacturer') and item.refacturer else "Non"
            # payeur_text = "Oui" if hasattr(item, 'payeur') and item.payeur else "Non" # Ancienne version
            payeur_display_text = "Emp." if hasattr(item, 'payeur') and item.payeur else "Jac."

            total_avant_taxes_str = f"{item.totale_avant_taxes:.2f} $" if hasattr(item, 'totale_avant_taxes') and item.totale_avant_taxes is not None else '0.00 $'
            pourboire_str = f"{item.pourboire:.2f} $" if hasattr(item, 'pourboire') and item.pourboire is not None else '0.00 $'
            tps_str = f"{item.tps:.2f} $" if hasattr(item, 'tps') and item.tps is not None else '0.00 $'
            tvq_str = f"{item.tvq:.2f} $" if hasattr(item, 'tvq') and item.tvq is not None else '0.00 $'
            tvh_str = f"{item.tvh:.2f} $" if hasattr(item, 'tvh') and item.tvh is not None else '0.00 $'
            total_apres_taxes_str = f"{item.totale_apres_taxes:.2f} $" if hasattr(item, 'totale_apres_taxes') and item.totale_apres_taxes is not None else '0.00 $'
            # montant_employe_str = f"{item.employe:.2f} $" if hasattr(item, 'employe') and item.employe is not None else '0.00 $' # Supprimé

            rows_html += f"""
                <tr>
                    <td class="date-cell">{date_str}</td>
                    <td>{resto_str}</td>
                    <td>{client_str}</td>
                    <td>{num_cmd_str}</td>
                    <td>{refacturer_text}</td>
                    <td>{payeur_display_text}</td>
                    <td class="montant">{total_avant_taxes_str}</td>
                    <td class="montant">{pourboire_str}</td>
                    <td class="montant">{tps_str}</td>
                    <td class="montant">{tvq_str}</td>
                    <td class="montant">{tvh_str}</td>
                    <td class="montant">{total_apres_taxes_str}</td>
                </tr>
            """
        # Largeurs de colonnes pour les repas (maintenant 12 colonnes)
        # Total = 100%
        colgroup_html = """
            <colgroup>
                <col style="width: 10%;">  <!-- Date MODIFIED-->
                <col style="width: 11%;"> <!-- Restaurant MODIFIED-->
                <col style="width: 11%;"> <!-- Client MODIFIED-->
                <col style="width: 7%;">  <!-- N° Cmd -->
                <col style="width: 7%;">  <!-- Refacturer -->
                <col style="width: 7%;">  <!-- Payeur -->
                <col style="width: 8%;">  <!-- Total av. Tx -->
                <col style="width: 8%;">  <!-- Pourboire -->
                <col style="width: 7%;">  <!-- TPS MODIFIED-->
                <col style="width: 8%;">  <!-- TVQ -->
                <col style="width: 8%;">  <!-- TVH -->
                <col style="width: 8%;">  <!-- Total ap. Tx -->
            </colgroup>
        """
        return f"""
            <h2 class="section-title">Repas</h2>
            <table class="data-table">
                {colgroup_html}
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Restaurant</th>
                        <th>Client</th>
                        <th>N° Cmd</th>
                        <th>Refacturer</th>
                        <th>Payeur</th>
                        <th class="montant">Tot. av. tx.</th>
                        <th class="montant">Pourb.</th>
                        <th class="montant">TPS</th>
                        <th class="montant">TVQ</th>
                        <th class="montant">TVH</th>
                        <th class="montant">Tot. ap. tx.</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        """

    def _generate_depenses_diverses_html(self, depenses_list: List['Depense']) -> str:
        if not depenses_list: return ""
        rows_html = ""
        for item in depenses_list:
            date_str = item.date.strftime('%d/%m/%y') if hasattr(item, 'date') and item.date else ''
            type_depense_str = item.type_depense if hasattr(item, 'type_depense') else ''
            desc_str = item.description if hasattr(item, 'description') else ''
            fournisseur_str = item.fournisseur if hasattr(item, 'fournisseur') else ''
            # payeur_text = "Oui" if hasattr(item, 'payeur') and item.payeur else "Non" # Ancienne version
            payeur_display_text = "Emp." if hasattr(item, 'payeur') and item.payeur else "Jac."

            total_avant_taxes_str = f"{item.totale_avant_taxes:.2f} $" if hasattr(item, 'totale_avant_taxes') and item.totale_avant_taxes is not None else '0.00 $'
            tps_str = f"{item.tps:.2f} $" if hasattr(item, 'tps') and item.tps is not None else '0.00 $'
            tvq_str = f"{item.tvq:.2f} $" if hasattr(item, 'tvq') and item.tvq is not None else '0.00 $'
            tvh_str = f"{item.tvh:.2f} $" if hasattr(item, 'tvh') and item.tvh is not None else '0.00 $'
            total_apres_taxes_str = f"{item.totale_apres_taxes:.2f} $" if hasattr(item, 'totale_apres_taxes') and item.totale_apres_taxes is not None else '0.00 $'

            rows_html += f"""
                <tr>
                    <td class="date-cell">{date_str}</td>
                    <td>{type_depense_str}</td>
                    <td>{desc_str}</td>
                    <td>{fournisseur_str}</td>
                    <td>{payeur_display_text}</td>
                    <td class="montant">{total_avant_taxes_str}</td>
                    <td class="montant">{tps_str}</td>
                    <td class="montant">{tvq_str}</td>
                    <td class="montant">{tvh_str}</td>
                    <td class="montant">{total_apres_taxes_str}</td>
                </tr>
            """
        # Largeurs de colonnes pour les dépenses diverses (maintenant 10 colonnes)
        colgroup_html = """
            <colgroup>
                <col style="width: 10%;"> <!-- Date -->
                <col style="width: 12%;"> <!-- Type -->
                <col style="width: 18%;"> <!-- Description -->
                <col style="width: 12%;"> <!-- Fournisseur -->
                <col style="width: 7%;">  <!-- Payeur -->
                <col style="width: 8%;">  <!-- Tot. av. tx. -->
                <col style="width: 8%;">  <!-- TPS -->
                <col style="width: 8%;">  <!-- TVQ -->
                <col style="width: 8%;">  <!-- TVH -->
                <col style="width: 9%;">  <!-- Tot. ap. tx. -->
            </colgroup>
        """
        return f"""
            <h2 class="section-title">Dépenses Diverses</h2>
            <table class="data-table">
                {colgroup_html}
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Description</th>
                        <th>Fournisseur</th>
                        <th>Payeur</th>
                        <th class="montant">Tot. av. tx.</th>
                        <th class="montant">TPS</th>
                        <th class="montant">TVQ</th>
                        <th class="montant">TVH</th>
                        <th class="montant">Tot. ap. tx.</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        """

    def _generate_totaux_html(self, rapport: 'RapportDepense') -> str:
        total_deplacements = 0.0
        if hasattr(rapport, 'deplacements') and rapport.deplacements:
            for deplacement in rapport.deplacements:
                if hasattr(deplacement, 'montant') and deplacement.montant is not None:
                    total_deplacements += deplacement.montant

        total_repas = 0.0
        if hasattr(rapport, 'repas') and rapport.repas:
            for repas_item in rapport.repas:
                # Sommer la totale_apres_taxes si payeur est True (Employé)
                if (hasattr(repas_item, 'payeur') and
                    repas_item.payeur and
                    hasattr(repas_item, 'totale_apres_taxes') and
                    repas_item.totale_apres_taxes is not None):
                    total_repas += repas_item.totale_apres_taxes
        
        total_depenses_diverses = 0.0
        if hasattr(rapport, 'depenses_diverses') and rapport.depenses_diverses:
            for depense_item in rapport.depenses_diverses:
                # Sommer la totale_apres_taxes si payeur est True (Employé)
                if (hasattr(depense_item, 'payeur') and
                    depense_item.payeur and
                    hasattr(depense_item, 'totale_apres_taxes') and
                    depense_item.totale_apres_taxes is not None):
                    total_depenses_diverses += depense_item.totale_apres_taxes

        grand_total_remboursement = total_deplacements + total_repas + total_depenses_diverses

        return f"""
            <div class="totals-section">
                <table>
                    <tr><th>Total Déplacements:</th><td class="montant">{total_deplacements:.2f} $</td></tr>
                    <tr><th>Total Repas:</th><td class="montant">{total_repas:.2f} $</td></tr>
                    <tr><th>Total Dépenses Diverses:</th><td class="montant">{total_depenses_diverses:.2f} $</td></tr>
                    <tr><th>GRAND TOTAL:</th><td class="grand-total montant">{grand_total_remboursement:.2f} $</td></tr>
                </table>
            </div>
        """
    
    def _generate_footer_html(self) -> str:
        return f"""
            <div class="footer">
                <p>Rapport généré par l'application GDJ.</p>
            </div>
        """

    def _generate_rapport_depense_html(self, rapport: 'RapportDepense') -> str:
        """Construit la chaîne HTML complète pour un rapport de dépenses."""
        
        html_content = "<html><head><meta charset='UTF-8'><title>Rapport de Dépenses</title>"
        html_content += f"<style>{self._get_base_css()}</style></head><body>"
        
        html_content += self._generate_header_html(rapport)
        html_content += self._generate_rapport_info_table_html(rapport)
        html_content += self._generate_deplacements_html(rapport)
        html_content += self._generate_repas_html(rapport.repas)
        html_content += self._generate_depenses_diverses_html(rapport.depenses_diverses)
        html_content += self._generate_totaux_html(rapport)
        html_content += self._generate_footer_html()
        
        html_content += "</body></html>"
        return html_content

    def generate(self, document, output_path: str):
        """
        Génère un PDF pour le document fourni en utilisant WeasyPrint.
        Détecte le type de document et appelle la méthode de génération HTML appropriée.
        """
        # --- Importations réelles ici pour éviter les dépendances circulaires au niveau du module ---
        from models.documents.rapport_depense.rapport_depense import RapportDepense
        # from models.documents.autre_type.autre_type import AutreTypeDocument # Pour le futur

        html_string = ""
        if isinstance(document, RapportDepense):
            html_string = self._generate_rapport_depense_html(document)
        # elif isinstance(document, AutreTypeDocument):
        #     html_string = self._generate_autre_type_html(document) # À implémenter
        else:
            print(f"Type de document non supporté pour la génération PDF HTML: {type(document).__name__}")
            return

        if not html_string:
            print("Aucun contenu HTML généré.")
            return

        try:
            # Configuration des polices pour WeasyPrint (si nécessaire, par exemple pour des polices non standard)
            # font_config = FontConfiguration() # Commenté pour l'instant car non utilisé activement
            
            # Générer le PDF depuis la chaîne HTML
            # La CSS de base est déjà incluse dans html_string via _generate_rapport_depense_html
            # Si font_config était utilisé, il faudrait le passer ici ou à CSS() si on avait des CSS externes.
            html_doc = HTML(string=html_string, base_url=os.path.dirname(os.path.abspath(__file__)))
            html_doc.write_pdf(output_path) # Potentiellement ajouter font_config=font_config ici si utilisé

            print(f"PDF généré avec succès (via HTML) : {output_path}")

        except Exception as e:
            print(f"Erreur lors de la génération du PDF avec WeasyPrint : {e}")
            import traceback
            traceback.print_exc()

# --- Suppression des anciennes méthodes FPDF ---
# _set_default_font
# _add_header_footer (FPDF)
# _add_rapport_info_table (FPDF)
# _add_table_header
# _add_table_row
# _add_section_title
# _add_deplacements_section (FPDF)
# _add_repas_section (FPDF)
# _add_depenses_diverses_section (FPDF)
# _add_totaux_section (FPDF)
# _generate_rapport_depense_pdf (FPDF) 