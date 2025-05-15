from datetime import date
from core.static import get_res_item
from core.template import Label, DataLabel, LabelCode
from core.xml_templates import get_header, get_footer, get_jacmar_container, get_jacmar_fields, get_logo_company

class DataJacmar(DataLabel):
    def __init__(self):
        super().__init__()
        # Le logo Jacmar est nécessaire
        self.path_img_jacmar = get_res_item("logo_jacmar.png") 
        self.date = date.today().strftime("%Y-%m-%d")
        self.nref = "FAB1000"
        # Définir une largeur et hauteur par défaut pour cette étiquette
        self.w = 110 # largeur similaire à CSA
        self.h = 40  # hauteur initiale, sera ajustée

class LabelJacmar(Label):
    code = LabelCode.JACMAR

    def __init__(self):
        super().__init__()
        self.data = DataJacmar()
        # Hauteur de base pour les champs après le logo
        # Le logo Jacmar via get_logo_company a une dy_max de 22 par défaut
        self._logo_height = 22 
        self._padding_after_logo = 5
        # MODIFIÉ: Les champs Date et NRef sont maintenant sur une seule ligne
        self._fields_height = 6 # Hauteur approximative pour une ligne de texte avec __style2
        self._padding_bottom = 2 # MODIFIÉ: Réduction du padding en bas
        self._lbl_base_height = self._logo_height + self._padding_after_logo + self._fields_height + self._padding_bottom

    def get_svg(self, headers=True, final=False):
        if not self._changed and not final:
            return self._svg_str
        
        self._svg_str = ""
        # Ajuster la hauteur de l'étiquette dynamiquement si nécessaire (pas pour l'instant car contenu fixe)
        self.data.h = self._lbl_base_height

        if headers:
            # +2 pour la bordure/marge de l'highlighter
            self._svg_str += get_header(self.data.w + 2, self.data.h + 2)

        _dx = self.data.x
        _dy = self.data.y

        # Conteneur (bordure + highlight)
        self._svg_str += get_jacmar_container(self.data.h, width=self.data.w, x=_dx, y=_dy, highlight=(self.highlight and not final))
        
        # Logo Jacmar
        # get_logo_company(image_path, x=0.0, y=0.0, dx_max=80, dy_max=22, stick="W")
        # Nous voulons le logo centré horizontalement et en haut.
        logo_x_offset = (self.data.w - 80) / 2 # Supposant que dx_max pour le logo est 80
        self._svg_str += get_logo_company(self.data.path_img_jacmar, x=_dx + logo_x_offset, y=_dy + 2) # +2 pour un petit padding haut

        # Champs Date et NRef
        # Positionner les champs sous le logo
        fields_y_start = self._logo_height + self._padding_after_logo + 2 # +2 pour correspondre au padding haut du logo
        self._svg_str += get_jacmar_fields(self.data.date, self.data.nref, x=_dx, y=_dy + fields_y_start)

        if headers:
            self._svg_str += get_footer()
        
        self._changed = False
        return self._svg_str 