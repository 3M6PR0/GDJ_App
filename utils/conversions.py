from PyQt5.QtGui import QGuiApplication

# Constante pour la conversion, basée sur la résolution standard de 96 DPI
PIXELS_PER_INCH = 96
MM_PER_INCH = 25.4

def mm_to_pixels(mm: float) -> float:
    """Convertit des millimètres en pixels."""
    return (mm / MM_PER_INCH) * PIXELS_PER_INCH

def pixels_to_mm(pixels: float) -> float:
    """Convertit des pixels en millimètres."""
    return (pixels / PIXELS_PER_INCH) * MM_PER_INCH 