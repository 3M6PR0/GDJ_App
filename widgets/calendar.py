from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QSizePolicy, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QRectF, QSize, QLocale

# --- AJOUT: DayCellWidget ---
class DayCellWidget(QWidget):
    clicked = pyqtSignal(QDate) # Signal émis lorsque la cellule est cliquée avec une date valide

    def __init__(self, date=None, is_current_month=True, is_today=False, is_selected=False, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True) # Important pour le dessin personnalisé et QSS
        self.setMinimumSize(30, 30) # Taille minimale pour la cellule
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._date = date
        self._is_current_month = is_current_month
        self._is_today = is_today
        self._is_selected = is_selected
        self._is_hovered = False

        self.day_label = QLabel(str(date.day()) if date else "", self)
        self.day_label.setAlignment(Qt.AlignCenter)
        
        # Layout interne pour centrer le label (pourrait être fait avec paintEvent aussi)
        cell_layout = QVBoxLayout(self)
        cell_layout.setContentsMargins(0,0,0,0)
        cell_layout.addWidget(self.day_label, 0, Qt.AlignCenter)
        self.setLayout(cell_layout)

    def set_data(self, date, is_current_month, is_today, is_selected):
        self._date = date
        self.day_label.setText(str(date.day()) if date else "")
        self._is_current_month = is_current_month
        self._is_today = is_today
        self._is_selected = is_selected
        self.update() # Redessiner

    def select(self, selected_status):
        self._is_selected = selected_status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        app = QApplication.instance()
        RADIUS = int((app.property("RADIUS_DEFAULT") or "3px")[:-2]) # Ex: "3px" -> 3

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5) # Pour une bordure nette

        # Couleurs par défaut (seront basées sur le thème plus tard)
        bg_color = QColor(app.property("COLOR_PRIMARY_MEDIUM") or "#353535")
        text_color = QColor(app.property("COLOR_TEXT_PRIMARY") or "#FFFFFF")
        accent_color = QColor(app.property("COLOR_ACCENT") or "#0078D4")
        hover_color = QColor(app.property("COLOR_ITEM_HOVER") or "#4A4A4A")
        today_outline_color = QColor(app.property("COLOR_ACCENT_LIGHT") or "#50A6F0")
        disabled_text_color = QColor(app.property("COLOR_TEXT_DISABLED") or "#808080")
        text_on_accent_color = QColor(app.property("COLOR_TEXT_ON_ACCENT") or text_color)

        current_text_color_name = disabled_text_color.name() if not self._is_current_month else text_color.name()
        current_bg = bg_color

        if self._is_selected and self._is_current_month: # Sélection prioritaire sur survol si mois courant
            current_bg = accent_color
            current_text_color_name = text_on_accent_color.name()
        elif self._is_hovered and self._is_current_month:
            current_bg = hover_color
        
        self.day_label.setStyleSheet(f"color: {current_text_color_name}; background: transparent;") # Fond transparent pour le label
        
        painter.setBrush(QBrush(current_bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, RADIUS, RADIUS)

        if self._is_today and self._is_current_month:
            pen = QPen(today_outline_color)
            pen.setWidth(1)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), RADIUS -1 if RADIUS > 0 else 0, RADIUS -1 if RADIUS > 0 else 0)

    def enterEvent(self, event):
        if self._is_current_month:
            self._is_hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._date and self._is_current_month:
            self.clicked.emit(self._date)
        super().mousePressEvent(event)
    
    def sizeHint(self):
        # Donner une indication de taille pour que les cellules ne soient pas trop petites
        return QSize(35, 35)
# --- Fin DayCellWidget ---

class Calendar(QWidget):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, initial_date=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("CustomCalendarView")

        if initial_date and initial_date.isValid():
            self._selected_date = initial_date
        else:
            self._selected_date = QDate.currentDate()
        
        self._displayed_month = self._selected_date.month()
        self._displayed_year = self._selected_date.year()
        self._first_day_of_week = Qt.Monday # Défaut Qt, sera écrasé par setFirstDayOfWeek si appelé

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._day_cells = []
        self._init_ui()
        # self._update_display() # Appel initial déplacé à la fin de _init_ui pour s'assurer que tout est prêt

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2,2,2,2)
        main_layout.setSpacing(3)

        nav_bar_widget = QWidget(self)
        self.nav_layout = QHBoxLayout(nav_bar_widget) # Sauvegarder pour accès potentiel
        self.nav_layout.setContentsMargins(5,2,5,2)
        self.nav_layout.setSpacing(0)
        self.month_year_label = QLabel(self)
        self.month_year_label.setObjectName("MonthYearLabel")
        self.month_year_label.setAlignment(Qt.AlignCenter)
        font = self.month_year_label.font()
        font.setBold(True)
        self.month_year_label.setFont(font)
        self.nav_layout.addWidget(self.month_year_label, 1)
        main_layout.addWidget(nav_bar_widget)

        week_header_widget = QWidget(self)
        week_header_widget.setObjectName("WeekHeaderWidget") # Nom pour référence
        self.week_header_layout = QHBoxLayout(week_header_widget) # Sauvegarder pour _update_week_header
        self.week_header_layout.setContentsMargins(5,2,5,2)
        self.week_header_layout.setSpacing(0)
        main_layout.addWidget(week_header_widget)
        self._update_week_header() # Appel initial pour construire l'en-tête

        self.days_grid_layout = QGridLayout()
        self.days_grid_layout.setContentsMargins(5,0,5,5)
        self.days_grid_layout.setSpacing(1)
        main_layout.addLayout(self.days_grid_layout, 1)
        for row in range(6):
            for col in range(7):
                cell = DayCellWidget(parent=self)
                cell.clicked.connect(self._on_day_cell_clicked)
                self.days_grid_layout.addWidget(cell, row, col)
                self._day_cells.append(cell)
        
        self._update_display() # Appel pour peupler la grille et le label mois/annee

    def _update_week_header(self):
        # Vider l'ancien layout d'en-tête
        while self.week_header_layout.count():
            child = self.week_header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        locale = QLocale(QLocale.French) # Pour s'assurer des noms de jours en français
        temp_days = []
        for i in range(7):
            day_offset = (self._first_day_of_week -1 + i) % 7 + 1 # Qt.Monday=1 .. Qt.Sunday=7
            temp_days.append(locale.dayName(day_offset, QLocale.ShortFormat).capitalize())

        for day_name_short in temp_days:
            day_label = QLabel(day_name_short, self)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            text_secondary_color = QColor(QApplication.instance().property("COLOR_TEXT_SECONDARY") or "#B0B0B0")
            day_label.setStyleSheet(f"color: {text_secondary_color.name()}; padding: 3px 0px;")
            self.week_header_layout.addWidget(day_label)

    def _update_display(self):
        locale = QLocale(QLocale.French)
        month_name = locale.monthName(self._displayed_month, QLocale.LongFormat).capitalize()
        self.month_year_label.setText(f"{month_name} {self._displayed_year}")
        self._populate_days_grid()

    def _populate_days_grid(self):
        first_day_of_month = QDate(self._displayed_year, self._displayed_month, 1)
        days_in_month = first_day_of_month.daysInMonth()
        
        # dayOfWeek(): 1=Lundi, ..., 7=Dimanche
        # self._first_day_of_week: Qt.Monday=1, ..., Qt.Sunday=7
        start_day_val = first_day_of_month.dayOfWeek() # 1-7
        
        # Décalage dans la grille (0-6)
        # Si self._first_day_of_week est Lundi (1), et le mois commence un Lundi (1), offset = 0
        # Si self._first_day_of_week est Dimanche (7), et le mois commence un Dimanche (7), offset = 0
        # Si self._first_day_of_week est Dimanche (7), et le mois commence un Lundi (1), offset = 1
        grid_start_offset = (start_day_val - self._first_day_of_week + 7) % 7

        current_day_num = 1
        today = QDate.currentDate()
        prev_month_date = first_day_of_month.addMonths(-1)
        days_in_prev_month = prev_month_date.daysInMonth()

        for i in range(len(self._day_cells)):
            row = i // 7
            col = i % 7
            cell = self._day_cells[i]
            if row * 7 + col < grid_start_offset:
                day_val = days_in_prev_month - (grid_start_offset - (row * 7 + col) - 1)
                date = QDate(prev_month_date.year(), prev_month_date.month(), day_val)
                cell.set_data(date, False, False, False)
            elif current_day_num <= days_in_month:
                date = QDate(self._displayed_year, self._displayed_month, current_day_num)
                is_today = (date == today)
                is_selected = (date == self._selected_date)
                cell.set_data(date, True, is_today, is_selected)
                current_day_num += 1
            else:
                next_month_day_num = (row * 7 + col) - days_in_month - grid_start_offset + 1
                next_month_date = first_day_of_month.addMonths(1)
                date = QDate(next_month_date.year(), next_month_date.month(), next_month_day_num)
                cell.set_data(date, False, False, False)
    
    def _on_day_cell_clicked(self, date):
        if date:
            self._selected_date = date
            self.dateSelected.emit(self._selected_date)
            self._populate_days_grid() 

    def setDate(self, date):
        if isinstance(date, QDate) and date.isValid():
            self._selected_date = date
            self._displayed_month = date.month()
            self._displayed_year = date.year()
            self._update_display()

    def selectedDate(self):
        return self._selected_date

    def setFirstDayOfWeek(self, day_of_week):
        if day_of_week in [Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday, Qt.Saturday, Qt.Sunday]:
            if self._first_day_of_week != day_of_week:
                self._first_day_of_week = day_of_week
                self._update_week_header() 
                self._update_display() # Pour que populate_days_grid utilise le nouvel offset
        else:
            print(f"Warning: Invalid day_of_week passed to setFirstDayOfWeek: {day_of_week}")

    # def setMinimumDate(self, date):
    #     # Logique à ajouter si besoin
    #     pass

    # def setMaximumDate(self, date):
    #     # Logique à ajouter si besoin
    #     pass

    # def paintEvent(self, event):
    #     pass # Plus besoin si les enfants couvrent tout et le style est via QSS/parent

    # def _populate_days_grid(self):
    #     # Logique pour calculer et afficher les jours
    #     pass

    # def _go_to_prev_month(self):
    #     self._displayed_month -= 1
    #     if self._displayed_month < 1:
    #         self._displayed_month = 12
    #         self._displayed_year -= 1
    #     self._update_display()

    # def _go_to_next_month(self):
    #     self._displayed_month += 1
    #     if self._displayed_month > 12:
    #         self._displayed_month = 1
    #         self._displayed_year += 1
    #     self._update_display()

    # def _populate_days_grid(self):
    #     # Logique pour calculer et afficher les jours
    #     pass

    # def set_selected_date(self, date):
    #     # Mettre à jour la date sélectionnée et l'affichage
    #     pass

    # etc. 