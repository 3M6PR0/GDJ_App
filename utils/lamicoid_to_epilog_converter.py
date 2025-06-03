import logging
import xml.sax.saxutils
from PyQt5.QtCore import Qt # Pour les flags d'alignement

# Importer les utilitaires de conversion partagés
from .epilog_converter_utils import mm_to_pixels, pixels_to_mm, points_to_mm

logger = logging.getLogger(__name__) # Utiliser le nom du module courant pour le logger

# # Constantes de conversion (MAINTENANT DANS epilog_converter_utils.py)
# DEFAULT_DPI = 96.0
# INCH_TO_MM = 25.4

# def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
#     return (mm / INCH_TO_MM) * dpi

# def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
#     return (pixels / dpi) * INCH_TO_MM

# def points_to_mm(points: float) -> float:
#     return (points / 72.0) * INCH_TO_MM

def generate_svg_for_epilog(lamicoid_params: dict, editor_items: list) -> str:
    logger.debug(f"Début génération SVG. Params: {lamicoid_params}, Items: {len(editor_items)}")
    
    svg_parts = []
    width_mm = lamicoid_params.get('width_mm', 100.0)
    height_mm = lamicoid_params.get('height_mm', 50.0)
    corner_radius_mm = lamicoid_params.get('corner_radius_mm', 0.0)

    # Dimensions du Lamicoid en pixels (pour la conversion des positions des items)
    # Ces dimensions correspondent au viewBox du SVG.
    lamicoid_width_px = mm_to_pixels(width_mm)
    lamicoid_height_px = mm_to_pixels(height_mm)
    logger.debug(f"Dimensions Lamicoid pour SVG: width_mm={width_mm}, height_mm={height_mm}, radius_mm={corner_radius_mm}")
    logger.debug(f"Dimensions Lamicoid en pixels pour conversion interne: width_px={lamicoid_width_px}, height_px={lamicoid_height_px}")

    # Le viewBox définit l'espace de coordonnées en unités qui représentent des mm.
    # Les attributs width/height du SVG utilisent maintenant les valeurs mm (sans unité), comme le viewBox.
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" ' 
        f'width="{width_mm}mm" ' # On réessaye avec les unités mm explicites
        f'height="{height_mm}mm" ' # On réessaye avec les unités mm explicites
        f'version="1.1" viewBox="0 0 {width_mm} {height_mm}">'
    )
    svg_parts.append('  <g id="LamicoidContent">')

    # Éléments texte pour la gravure
    for item_data in editor_items:
        item_subtype = item_data.get('item_subtype')
        if item_subtype == 'text' or item_subtype == 'variable_text':
            item_pos_x_scene_px = item_data.get('pos_x', 0.0) 
            item_pos_y_scene_px = item_data.get('pos_y', 0.0)
            item_width_px = item_data.get('width', 10.0)
            item_height_px = item_data.get('height', 5.0)
            logger.debug(f"  Item texte brut: pos_scene_px=({item_pos_x_scene_px}, {item_pos_y_scene_px}), size_px=({item_width_px}, {item_height_px})")

            # Conversion des coordonnées du coin supérieur gauche de l'item (scène -> lamicoid)
            item_top_left_lamicoid_px_x = item_pos_x_scene_px + (lamicoid_width_px / 2.0)
            item_top_left_lamicoid_px_y = item_pos_y_scene_px + (lamicoid_height_px / 2.0)
            logger.debug(f"    Item TL converti (Lamicoid px): ({item_top_left_lamicoid_px_x}, {item_top_left_lamicoid_px_y})")

            # Conversion en mm pour SVG (dimensions et position du coin sup-gauche)
            # Ces valeurs de base sont pour le coin supérieur gauche du rectangle de l'item
            svg_item_x_base_mm = pixels_to_mm(item_top_left_lamicoid_px_x)
            svg_item_y_base_mm = pixels_to_mm(item_top_left_lamicoid_px_y)
            item_width_mm = pixels_to_mm(item_width_px)
            item_height_mm = pixels_to_mm(item_height_px)

            logger.debug(f"  Item SVG base (mm): x_base={svg_item_x_base_mm:.2f}, y_base={svg_item_y_base_mm:.2f}, w_mm={item_width_mm:.2f}, h_mm={item_height_mm:.2f}")

            font_family = item_data.get('font_family', 'Arial')
            font_size_pt = item_data.get('font_size_pt', 12)
            font_size_mm = points_to_mm(font_size_pt)
            
            # --- TEST TAILLE: Forcer une font-size plus petite (3mm) AVEC unité mm explicitement ---
            forced_font_size_mm_for_test = 3.0
            logger.warning(f"  TESTING FONT SIZE: Original font_size_mm={font_size_mm:.2f}mm, Forcée à {forced_font_size_mm_for_test:.2f}mm pour ce test.")
            current_font_size_for_style = forced_font_size_mm_for_test
            # --- FIN TEST TAILLE ---
            
            # Utiliser la taille de police (potentiellement forcée) pour le style
            style_parts = [f"font-size:{current_font_size_for_style:.2f}mm;", f"font-family:'{xml.sax.saxutils.escape(font_family)}';"]
            if item_data.get('font_bold'): style_parts.append("font-weight:bold;")
            if item_data.get('font_italic'): style_parts.append("font-style:italic;")
            # text-decoration:underline; n'est souvent pas bien géré pour la gravure, on le laisse de côté pour l'instant
            # ou s'assurer qu'il est bien 'none' si pas souligné
            style_parts.append("text-decoration:none;")


            style_parts.extend(["fill:none;", "stroke:blue;", "stroke-width:0.1;"]) # Styles pour la gravure
            
            style_attr = " ".join(style_parts)
            
            text_content_raw = item_data.get('text_content', '')
            text_lines = [line.strip() for line in text_content_raw.split('\n')]
            text_lines = [line for line in text_lines if line] # Filtrer les lignes vides

            if not text_lines:
                logger.warning(f"  Item texte {item_data.get('uuid', 'N/A')} n'a pas de contenu textuel après nettoyage, il sera ignoré.")
                continue

            num_lines = len(text_lines)
            line_height_em = 1.2 # Facteur d'interligne standard

            # Calcul des coordonnées SVG pour l'élément <text> parent
            # Le point (svg_x_final, svg_y_final) sera le point d'ancrage du bloc de texte.
            svg_x_final = 0.0
            svg_y_final = 0.0
            text_anchor = "start" # par défaut
            # dominant_baseline = "auto" # par défaut, ou "text-before-edge" ou "hanging"

            qt_alignment = item_data.get('text_alignment', Qt.AlignLeft | Qt.AlignTop) # Défaut à gauche et en haut

            # Alignement Horizontal
            if qt_alignment & Qt.AlignHCenter:
                text_anchor = "middle"
                svg_x_final = svg_item_x_base_mm + (item_width_mm / 2.0)
            elif qt_alignment & Qt.AlignRight:
                text_anchor = "end"
                svg_x_final = svg_item_x_base_mm + item_width_mm
            else: # Qt.AlignLeft ou par défaut
                text_anchor = "start"
                svg_x_final = svg_item_x_base_mm
            
            # # --- MODIFICATION POUR TEST: Forcer l'alignement vertical en HAUT --- (OBSOLÈTE ET SUPPRIMÉ)
            # dominant_baseline = "hanging" # Ou "text-before-edge". "hanging" est souvent plus simple pour le premier tspan.
            # svg_y_final = svg_item_y_base_mm # y du <text> est le haut du rectangle de l'item.
            # logger.debug(f"  ALIGNEMENT VERTICAL FORCÉ EN HAUT: dominant-baseline='{dominant_baseline}', y_text={svg_y_final:.2f}")
            # # --- FIN MODIFICATION POUR TEST ---

            logger.debug(f"  SVG Text attributes (avant calcul Y par ligne): x={svg_x_final:.2f}, anchor={text_anchor}")
            logger.debug(f"  Text lines ({num_lines}): {text_lines}")
            logger.debug(f"  Font size (pour style): {current_font_size_for_style:.2f}mm (unité explicite), Calculated line height factor: {line_height_em}")

            # Recalculer actual_line_height_mm avec la taille de police (potentiellement forcée) utilisée pour le style
            actual_line_height_mm = current_font_size_for_style * line_height_em 
            logger.debug(f"    Font size for calculation (actual): {current_font_size_for_style:.2f}mm, Actual line height: {actual_line_height_mm:.2f}mm")

            # Nouvelle logique pour le centrage vertical du bloc de texte
            # Chaque ligne aura dominant-baseline="middle"
            dominant_baseline = "middle" # Pour chaque ligne de texte

            # Calcul du Y pour la ligne centrale de la première ligne de texte,
            # de manière à ce que le bloc entier de texte soit centré verticalement dans item_height_mm.
            total_block_height_approx = num_lines * actual_line_height_mm # Hauteur approximative du bloc
            # Pour un meilleur centrage, on peut considérer la hauteur réelle d'une ligne et l'espacement
            # Mais pour dominant-baseline=middle, on centre la baseline de la ligne du milieu du bloc.

            y_center_of_item_box_mm = svg_item_y_base_mm + (item_height_mm / 2.0)
            # Le y de la première ligne (sa baseline centrale) :
            y_baseline_first_line_mm = y_center_of_item_box_mm - ((num_lines - 1) / 2.0) * actual_line_height_mm

            logger.debug(f"  Centrage vertical: y_center_of_item={y_center_of_item_box_mm:.2f}mm, y_baseline_first_line={y_baseline_first_line_mm:.2f}mm for {num_lines} lines")

            # current_y_mm_for_text_line = svg_y_final # Plus utilisé

            for i, line_content in enumerate(text_lines):
                safe_line_content = xml.sax.saxutils.escape(line_content)
                
                current_line_center_y_mm = y_baseline_first_line_mm + (i * actual_line_height_mm)

                # Chaque ligne est un élément <text> séparé
                svg_line_element = (
                    f'    <text x="{svg_x_final:.2f}" y="{current_line_center_y_mm:.2f}" '
                    f'text-anchor="{text_anchor}" dominant-baseline="{dominant_baseline}" style="{style_attr}">'
                    f'{safe_line_content}'
                    f'</text>'
                )
                svg_parts.append(svg_line_element)
                logger.debug(f"      Line {i}: content='{safe_line_content}', y_center={current_line_center_y_mm:.2f}mm, dominant-baseline='{dominant_baseline}'")

    # Chemin de découpe pour le contour du Lamicoid
    r = corner_radius_mm
    w = width_mm
    h = height_mm

    if r > 0.01 and r * 2 <= min(w, h): # Coins arrondis
        path_d = (
            f"M {r:.2f},{0} "
            f"L {w-r:.2f},{0} "
            f"A {r:.2f},{r:.2f} 0 0 1 {w:.2f},{r:.2f} "
            f"L {w:.2f},{h-r:.2f} "
            f"A {r:.2f},{r:.2f} 0 0 1 {w-r:.2f},{h:.2f} "
            f"L {r:.2f},{h:.2f} "
            f"A {r:.2f},{r:.2f} 0 0 1 {0},{h-r:.2f} "
            f"L {0},{r:.2f} "
            f"A {r:.2f},{r:.2f} 0 0 1 {r:.2f},{0} "
            "Z"
        )
        svg_parts.append(f'    <path d="{path_d}" fill="none" stroke="aqua" stroke-width="0.1"/>')
    else: # Rectangle simple
        svg_parts.append(f'    <rect x="0" y="0" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="aqua" stroke-width="0.1"/>')

    svg_parts.append("  </g>")
    svg_parts.append("</svg>")
    
    final_svg = "\\n".join(svg_parts)
    logger.debug(f"SVG généré:\\n{final_svg}")
    return final_svg

def generate_settings_json_for_custom_lamicoid(job_name: str, firmware_version: str, has_engrave_process: bool, has_cut_process: bool) -> dict:
    logger.debug(f"Génération JSON pour job: {job_name}, Gravure: {has_engrave_process}, Découpe: {has_cut_process}")
    
    processes = []
    if has_engrave_process:
        processes.append({
            "_of": "engrave_process", "name": "P1_Engrave_Custom_Text",
            "speed": 70, "power": 50, "resolution": 300, "dithering": "none",
            "engrave_direction": "down", "unidirectional": False, "precision_sync": False,
            "laser_type": "co2", "air_assist": False, "cycles": 1, "offset": 0,
            "filter": {"_of": "color_filter", "colors": ["blue"]}
        })
    
    if has_cut_process: # Le contour est toujours découpé
        processes.append({
            "_of": "vector_process", "name": "P2_Cut_Lamicoid_Outline",
            "speed": 10, "power": 90, "frequency": 50,
            "laser_type": "co2", "air_assist": False,
            "cycles": 1, "offset": 0, "beziers": True, 
            "vector_sorting": "inside_out",
            "filter": {"_of": "color_filter", "colors": ["aqua"], "color_filter_type": "stroke"}
        })

    settings_dict = {
        "job_name": job_name,
        "firmware_version": firmware_version, 
        "autofocus": "off", 
        "copies": 1,
        "processes": processes
    }
    logger.info(f"Settings JSON générés: {settings_dict}")
    return settings_dict 