import logging

logger = logging.getLogger(__name__)

DEFAULT_DPI = 96.0
INCH_TO_MM = 25.4

def mm_to_pixels(mm: float, dpi: float = DEFAULT_DPI) -> float:
    """Convertit des millimètres en pixels en fonction d'une résolution DPI."""
    return (mm / INCH_TO_MM) * dpi

def pixels_to_mm(pixels: float, dpi: float = DEFAULT_DPI) -> float:
    """Convertit des pixels en millimètres en fonction d'une résolution DPI."""
    return (pixels / dpi) * INCH_TO_MM

def points_to_mm(points: float) -> float:
    """Convertit des points typographiques (1/72 de pouce) en millimètres."""
    return (points / 72.0) * INCH_TO_MM 