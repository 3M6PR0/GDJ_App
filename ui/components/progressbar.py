# ui/components/progressbar.py
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QRectF, QSize
import sys

class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Valeurs de progression
        self._minimum = 0
        self._maximum = 100
        self._value = 0

        # Style (paramétrable plus tard)
        self._line_width = 12
        self._text_color = QColor(220, 220, 220)
        self._progress_color = QColor(52, 152, 219) # Bleu
        self._bg_color = QColor(70, 70, 70) # Gris foncé
        self._font_size = 30
        self._suffix = "%"

        # Taille suggérée
        self.setMinimumSize(self.minimumSizeHint())

    # --- Méthodes pour contrôler la barre ---
    def setRange(self, minimum, maximum):
        if maximum < minimum:
            maximum, minimum = minimum, maximum
        self._minimum = minimum
        self._maximum = maximum
        self.setValue(self._value) # Ré-appliquer la valeur pour le clamping

    def setValue(self, value):
        # Clamper la valeur entre min et max
        self._value = max(min(value, self._maximum), self._minimum)
        self.update() # Demander un redessin

    def value(self):
        return self._value

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    # --- Personnalisation (exemples) ---
    def setLineWidth(self, width):
        self._line_width = width
        self.update()

    def setProgressColor(self, color: QColor):
        self._progress_color = color
        self.update()
        
    def setTextColor(self, color: QColor):
        self._text_color = color
        self.update()
        
    # ... (ajouter setBgColor, setFontSize etc si besoin)

    # --- Dessin --- 
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()) # Rectangle du widget
        # Ajuster pour l'épaisseur de ligne pour ne pas couper le dessin
        padding = self._line_width / 2
        paint_rect = rect.adjusted(padding, padding, -padding, -padding)
        center_x = paint_rect.center().x()
        center_y = paint_rect.center().y()
        radius = min(paint_rect.width(), paint_rect.height()) / 2
        
        # Calculer l'angle de la progression
        value_range = self._maximum - self._minimum
        progress_ratio = 0
        if value_range > 0:
             progress_ratio = (self._value - self._minimum) / value_range
        
        span_angle = int(progress_ratio * 360 * 16) # Qt utilise 1/16 deg
        start_angle = 90 * 16 # Commencer en haut

        # 1. Dessiner l'arc de fond
        pen = QPen(self._bg_color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.RoundCap) # Bords arrondis
        painter.setPen(pen)
        # Dessine l'arc complet (360 * 16)
        painter.drawArc(paint_rect.toRect(), start_angle, 360 * 16)

        # 2. Dessiner l'arc de progression
        pen.setColor(self._progress_color)
        painter.setPen(pen)
        painter.drawArc(paint_rect.toRect(), start_angle, -span_angle) # Négatif pour sens horaire

        # 3. Dessiner le texte
        pen.setColor(self._text_color)
        painter.setPen(pen)
        font = painter.font()
        font.setPointSize(self._font_size)
        font.setBold(True)
        painter.setFont(font)
        
        # --- CORRECTION: Toujours calculer le pourcentage --- 
        percentage = 0
        if value_range > 0:
             # Calculer la proportion (0.0 à 1.0)
             progress_ratio = (self._value - self._minimum) / value_range
             percentage = int(progress_ratio * 100) # Convertir en 0-100
        elif self._value == self._minimum:
             percentage = 0 # Si min=max=valeur, pourcentage est 0
        else:
             percentage = 100 # Si min=max et valeur=max, pourcentage est 100 ? Ou erreur?
             # Pour être sûr, on peut juste mettre 0 ou 100 basé sur la valeur
             # percentage = 100 if self._value >= self._maximum else 0
             # Ou simplement 0 si range = 0
             percentage = 0
        
        text = f"{percentage}{self._suffix}"
        painter.drawText(paint_rect.toRect(), Qt.AlignCenter, text)

    # --- Taille suggérée --- 
    def sizeHint(self):
        # Retourner une taille raisonnable par défaut
        return QSize(150, 150) 

    def minimumSizeHint(self):
        # Une taille minimale plus petite
        return QSize(50, 50)

# Exemple d'utilisation (pour tester ce fichier seul)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout(window)
    
    progress_bar = CircularProgressBar()
    progress_bar.setValue(68) # Mettre une valeur pour voir
    
    layout.addWidget(progress_bar)
    window.resize(200, 200)
    window.show()
    
    # Exemple pour changer la valeur après un délai (nécessite QTimer)
    # from PyQt5.QtCore import QTimer
    # timer = QTimer()
    # timer.timeout.connect(lambda: progress_bar.setValue((progress_bar.value() + 5) % 101))
    # timer.start(500)
    
    sys.exit(app.exec_()) 