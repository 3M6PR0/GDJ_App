import logging
import xml.sax.saxutils
from PyQt5.QtCore import Qt # Pour les flags d'alignement

logger = logging.getLogger(__name__) # Utiliser le nom du module courant pour le logger

# Constantes de conversion (peuvent être centralisées plus tard si nécessaire)
DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
    return (mm / INCH_TO_MM) * dpi

def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
    return (pixels / dpi) * INCH_TO_MM

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

    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}" height="{height_mm}" version="1.1" viewBox="0 0 {width_mm} {height_mm}">')
    svg_parts.append('  <g id="LamicoidContent">')

    # Éléments texte pour la gravure
    for item_data in editor_items:
        item_subtype = item_data.get('item_subtype')
        if item_subtype == 'text' or item_subtype == 'variable_text':
            item_pos_x_scene_px = item_data.get('pos_x', 0.0) 
            item_pos_y_scene_px = item_data.get('pos_y', 0.0)
            item_width_px = item_data.get('width', 10.0)
            item_height_px = item_data.get('height', 5.0)

            # Conversion des coordonnées du coin supérieur gauche de l'item (scène -> lamicoid)
            item_top_left_lamicoid_px_x = item_pos_x_scene_px + (lamicoid_width_px / 2.0)
            item_top_left_lamicoid_px_y = item_pos_y_scene_px + (lamicoid_height_px / 2.0)

            # Conversion en mm pour SVG (dimensions et position du coin sup-gauche)
            svg_item_x_base_mm = pixels_to_mm(item_top_left_lamicoid_px_x)
            svg_item_y_base_mm = pixels_to_mm(item_top_left_lamicoid_px_y)
            item_width_svg_mm = pixels_to_mm(item_width_px)
            item_height_svg_mm = pixels_to_mm(item_height_px)
            
            text_content = item_data.get('text_content', 'N/A')
            font_size_pt = item_data.get('font_size_pt', 10)
            font_size_mm = font_size_pt * (INCH_TO_MM / 72.0)
            font_family = item_data.get('font_family', 'Arial')
            
            style_parts = [
                f"font-size:{font_size_mm:.2f}mm;",
                f"font-family:'{xml.sax.saxutils.escape(font_family)}';",
                "fill:none;", # Style en ligne
                "stroke:blue;", # Style en ligne
                "stroke-width:0.1;" # Style en ligne
            ]
            if item_data.get('font_bold'): style_parts.append("font-weight:bold;")
            if item_data.get('font_italic'): style_parts.append("font-style:italic;")
            
            text_decoration_parts = []
            if item_data.get('font_underline'): text_decoration_parts.append("underline")
            # Ajoutez d'autres décorations si nécessaire (ex: line-through)
            if text_decoration_parts:
                style_parts.append(f"text-decoration:{' '.join(text_decoration_parts)};")
            else:
                style_parts.append("text-decoration:none;") # Assure qu'il n'y a pas de déco héritée
            
            style_attr = " ".join(style_parts)
            
            # Nettoyage du contenu texte : remplacer les sauts de ligne par des espaces, réduire les espaces multiples, et strip.
            cleaned_text_content = ' '.join(text_content.split()).strip()
            safe_text_content = xml.sax.saxutils.escape(cleaned_text_content)
            
            qt_alignment = item_data.get('text_alignment', Qt.AlignLeft | Qt.AlignVCenter) 
            
            # Détermination de text-anchor pour SVG
            text_anchor_svg = "start" # Défaut pour AlignLeft
            if qt_alignment & Qt.AlignRight: text_anchor_svg = "end"
            elif qt_alignment & Qt.AlignHCenter: text_anchor_svg = "middle"

            # Détermination de dominant-baseline pour SVG
            dominant_baseline_svg = "middle" # Défaut pour AlignVCenter
            # Note: Qt.AlignTop, AlignBottom, AlignVCenter affectent la position verticale DANS le rect.
            # dominant-baseline="middle" est un bon équivalent pour le centrage vertical.
            # Pour un alignement strict en haut/bas du *texte lui-même* (pas de son bounding box):
            if qt_alignment & Qt.AlignTop: dominant_baseline_svg = "text-before-edge"
            elif qt_alignment & Qt.AlignBottom: dominant_baseline_svg = "text-after-edge"
            # Qt.AlignVCenter est le plus courant avec text-anchor: middle et dominant-baseline: middle
            # si le texte doit être centré dans son bounding box.

            # Calcul des coordonnées x, y pour SVG en fonction de l'ancrage et de la baseline
            x_for_svg = svg_item_x_base_mm
            if text_anchor_svg == "middle":
                x_for_svg += item_width_svg_mm / 2.0
            elif text_anchor_svg == "end":
                x_for_svg += item_width_svg_mm

            y_for_svg = svg_item_y_base_mm
            if dominant_baseline_svg == "middle":
                y_for_svg += item_height_svg_mm / 2.0
            elif dominant_baseline_svg == "text-after-edge": # AlignBottom
                y_for_svg += item_height_svg_mm
            # Pour "text-before-edge" (AlignTop), y_for_svg reste svg_item_y_base_mm

            svg_parts.append(f'    <text x="{x_for_svg:.2f}" y="{y_for_svg:.2f}" text-anchor="{text_anchor_svg}" dominant-baseline="{dominant_baseline_svg}" style="{style_attr}">{safe_text_content}</text>')

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