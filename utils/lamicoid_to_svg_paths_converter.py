import logging
from PyQt5.QtGui import QFont, QPainterPath, QTransform, QFontMetricsF
from PyQt5.QtCore import Qt, QPointF, QRectF
import xml.sax.saxutils

from .epilog_converter_utils import mm_to_pixels, pixels_to_mm, points_to_mm

logger = logging.getLogger(__name__)

# # Temporaire, en attendant de les mettre dans epilog_converter_utils.py
# # DEFAULT_DPI = 96.0
# # INCH_TO_MM = 25.4
# # def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
# #     return (mm / INCH_TO_MM) * dpi
# # def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
# #     return (pixels / dpi) * INCH_TO_MM
# # def points_to_mm(points: float) -> float:
# #     return (points / 72.0) * INCH_TO_MM
# # À ENLEVER QUAND DÉPLACÉ -> C'est fait, on peut supprimer ces lignes commentées.


def qpainterpath_to_svg_path_data(path: QPainterPath, transform: QTransform = QTransform()) -> str:
    """
    Convertit un QPainterPath en une chaîne de données de chemin SVG (attribut 'd').
    Applique une transformation optionnelle au chemin avant la conversion.
    Les coordonnées dans le QPainterPath SONT CENSÉES ÊTRE EN PIXELS QT.
    La transformation fournie doit les convertir en unités SVG finales (mm).
    """
    svg_path_parts = []
    # Obtenir les polygones SANS appliquer la transformation ici.
    polygons_orig = path.toSubpathPolygons() 
    logger.debug(f"Path original ({path}) converti en {len(polygons_orig)} polygone(s) avant transformation explicite.")

    for i, polygon_orig in enumerate(polygons_orig):
        logger.debug(f"  Polygone original #{i}: {polygon_orig}")
        if polygon_orig.isEmpty():
            logger.debug(f"    Polygone original #{i} est vide, ignoré.")
            continue
        
        # Transformer le polygone point par point
        polygon_transformed = transform.map(polygon_orig)

        if polygon_transformed.isEmpty():
            logger.debug(f"    Polygone #{i} transformé est vide, ignoré.")
            continue

        # Log du premier point avant et après transformation pour diagnostic
        if i == 0 and not polygon_orig.isEmpty():
            orig_pt = polygon_orig.at(0)
            trans_pt = polygon_transformed.at(0)
            logger.debug(f"    Polygone #0, Point #0: Orig({orig_pt.x():.3f}, {orig_pt.y():.3f})px -> Transformed({trans_pt.x():.3f}, {trans_pt.y():.3f})mm")

        start_point_transformed = polygon_transformed.at(0)
        svg_path_parts.append(f"M {start_point_transformed.x():.3f} {start_point_transformed.y():.3f}")
        
        for j in range(1, polygon_transformed.size()):
            point_transformed = polygon_transformed.at(j)
            svg_path_parts.append(f"L {point_transformed.x():.3f} {point_transformed.y():.3f}")
        
    return " ".join(svg_path_parts)


def generate_svg_with_text_as_paths(lamicoid_params: dict, editor_items: list) -> str:
    logger.info("Début génération SVG avec texte converti en chemins.")
    
    svg_parts = []
    lamicoid_width_mm = lamicoid_params.get('width_mm', 100.0)
    lamicoid_height_mm = lamicoid_params.get('height_mm', 50.0)
    corner_radius_mm = lamicoid_params.get('corner_radius_mm', 0.0)

    # Conversion pour le viewBox et les dimensions globales.
    # Le système de coordonnées interne du QPainterPath sera en pixels Qt (basé sur 96 DPI par défaut).
    # La conversion finale en mm pour le SVG se fera au moment de générer la chaîne de chemin.
    
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{lamicoid_width_mm}mm" height="{lamicoid_height_mm}mm" '
        f'version="1.1" viewBox="0 0 {lamicoid_width_mm} {lamicoid_height_mm}">'
    )
    svg_parts.append('  <g id="LamicoidContent_ConvertedText">')

    # Conversion des dimensions du lamicoid en pixels (utilisé pour positionner les items)
    lamicoid_width_px = mm_to_pixels(lamicoid_width_mm)
    lamicoid_height_px = mm_to_pixels(lamicoid_height_mm)

    for item_data in editor_items:
        item_subtype = item_data.get('item_subtype')
        if item_subtype == 'text' or item_subtype == 'variable_text':
            # text_content_raw = item_data.get('text_content', '') # Remplacé par la version corrigée ci-dessous
            # text_lines = [line.strip() for line in text_content_raw.split('\n')] # Remplacé
            # text_lines = [line for line in text_lines if line] # Remplacé

            # --- DÉBUT DE LA SECTION CORRIGÉE ET AMÉLIORÉE ---
            text_content_raw = item_data.get('text_content', '')
            cleaned_lines = [line.strip() for line in text_content_raw.split('\n')]
            text_lines = [line for line in cleaned_lines if line]

            if not text_lines:
                logger.debug(f"  Item texte {item_data.get('uuid', 'N/A')} vide, ignoré.")
                continue
            
            logger.debug(f"Traitement item: {text_lines}")

            font_family = item_data.get('font_family', 'Arial')
            font_size_pt = item_data.get('font_size_pt', 12)
            is_bold = item_data.get('font_bold', False)
            is_italic = item_data.get('font_italic', False)
            qt_alignment = item_data.get('text_alignment', Qt.AlignLeft | Qt.AlignTop)

            item_pos_x_scene_px = item_data.get('pos_x', 0.0)
            item_pos_y_scene_px = item_data.get('pos_y', 0.0)
            item_width_scene_px = item_data.get('width', 10.0)
            item_height_scene_px = item_data.get('height', 5.0)
            item_rect_scene = QRectF(item_pos_x_scene_px, item_pos_y_scene_px,
                                     item_width_scene_px, item_height_scene_px)

            font = QFont(font_family, -1)
            font.setPointSizeF(float(font_size_pt))
            font.setBold(is_bold)
            font.setItalic(is_italic)

            fm = QFontMetricsF(font)
            actual_line_spacing_px = fm.lineSpacing()

            num_lines = len(text_lines) # Définition de num_lines ICI
            block_total_height_px = (num_lines - 1) * actual_line_spacing_px + fm.height()

            start_y_px = item_rect_scene.y()
            if qt_alignment & Qt.AlignVCenter:
                start_y_px += (item_rect_scene.height() - block_total_height_px) / 2.0
            elif qt_alignment & Qt.AlignBottom:
                start_y_px += item_rect_scene.height() - block_total_height_px
            
            first_line_baseline_y_px = start_y_px + fm.ascent()

            logger.debug(f"  Font: {font.family()} {font.pointSizeF()}pt, Bold: {font.bold()}, Italic: {font.italic()}")
            logger.debug(f"  Metrics: fm.height={fm.height():.2f}px, fm.lineSpacing={fm.lineSpacing():.2f}px, fm.ascent={fm.ascent():.2f}px")
            logger.debug(f"  Block: num_lines={num_lines}, block_total_height_px={block_total_height_px:.2f}px")
            logger.debug(f"  Vertical Align: item_rect_top={item_rect_scene.y():.2f}, start_y_for_block_top={start_y_px:.2f}, first_line_baseline_y={first_line_baseline_y_px:.2f}px")
            # --- FIN DE LA SECTION CORRIGÉE ET AMÉLIORÉE (avant la boucle sur text_lines) ---
            
            # La boucle for i, line_text ... reste structurellement la même mais utilise les variables ci-dessus
            for i, line_text in enumerate(text_lines):
                current_line_baseline_y_px = first_line_baseline_y_px + (i * actual_line_spacing_px)
                line_width_px = fm.horizontalAdvance(line_text)
                
                current_line_start_x_px = item_rect_scene.x()
                if qt_alignment & Qt.AlignHCenter:
                    current_line_start_x_px += (item_rect_scene.width() - line_width_px) / 2.0
                elif qt_alignment & Qt.AlignRight:
                    current_line_start_x_px += item_rect_scene.width() - line_width_px
                
                logger.debug(f"    Ligne {i}: '{line_text}', width={line_width_px:.2f}px, baseline_x={current_line_start_x_px:.2f}px, baseline_y={current_line_baseline_y_px:.2f}px")

                line_path = QPainterPath()
                line_path.addText(QPointF(current_line_start_x_px, current_line_baseline_y_px), font, line_text)
                
                transform_scene_to_svg = QTransform()
                
                # 1. Mise à l'échelle de pixels vers mm
                scale_factor = pixels_to_mm(1.0) 
                transform_scene_to_svg.scale(scale_factor, scale_factor)
                
                # 2. Translation pour passer de l'origine au centre de la scène (maintenant en mm)
                # à une origine en haut à gauche du Lamicoid (en mm).
                # Les arguments de translate sont maintenant relatifs au système de coordonnées mis à l'échelle (en mm).
                # Donc, nous utilisons lamicoid_width_px / 2.0 et lamicoid_height_px / 2.0
                # car ce sont les offsets dans le système de coordonnées *avant* la mise à l'échelle qui, 
                # après avoir été multipliés par scale_factor (ce que fait .translate() sur ses args ici), 
                # produiront le bon décalage en mm.
                transform_scene_to_svg.translate(lamicoid_width_px / 2.0, lamicoid_height_px / 2.0)
                                
                svg_d_attribute = qpainterpath_to_svg_path_data(line_path, transform_scene_to_svg)
                logger.debug(f"    Ligne '{line_text}': svg_d_attribute généré: '{svg_d_attribute}'")

                if svg_d_attribute:
                    style_attr = "fill:none; stroke:blue; stroke-width:0.1mm;"
                    svg_parts.append(f'    <path d="{svg_d_attribute}" style="{style_attr}" />')
                else:
                    logger.debug(f"  Chemin SVG vide pour la ligne: '{line_text}', ignoré.")


    # Chemin de découpe du Lamicoid (identique à l'autre fonction)
    r = corner_radius_mm
    w = lamicoid_width_mm
    h = lamicoid_height_mm
    if r > 0.01 and r * 2 <= min(w, h):
        path_d_cut = (
            f"M {r:.3f},{0} L {w-r:.3f},{0} A {r:.3f},{r:.3f} 0 0 1 {w:.3f},{r:.3f} "
            f"L {w:.3f},{h-r:.3f} A {r:.3f},{r:.3f} 0 0 1 {w-r:.3f},{h:.3f} "
            f"L {r:.3f},{h:.3f} A {r:.3f},{r:.3f} 0 0 1 {0},{h-r:.3f} "
            f"L {0},{r:.3f} A {r:.3f},{r:.3f} 0 0 1 {r:.3f},{0} Z"
        )
        svg_parts.append(f'    <path d="{path_d_cut}" fill="none" stroke="aqua" stroke-width="0.1mm"/>')
    else:
        svg_parts.append(f'    <rect x="0" y="0" width="{w:.3f}" height="{h:.3f}" fill="none" stroke="aqua" stroke-width="0.1mm"/>')

    svg_parts.append("  </g>")
    svg_parts.append("</svg>")
    
    final_svg = "\n".join(svg_parts)
    logger.debug(f"SVG (texte en chemins) généré:\n{final_svg}")
    return final_svg 