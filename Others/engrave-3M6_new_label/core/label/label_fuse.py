from core.template import *
from core.xml_templates import get_header, get_fuse_container, get_fuse_line, get_footer

class DataFuse(DataLabel):
    def __init__(self):
        super().__init__()
        self.fuses = []

class LabelFuse(Label):
    code = LabelCode.FUSE
    def __init__(self):
        super().__init__()
        self.data = DataFuse()

    def get_svg(self, headers=True, final=False):
        if not self._changed and not final:
            return self._svg_str
        self.data.h = self._lbl_base_height + self._text_spacing * len(self.data.fuses)
        self._svg_str = ""
        if headers:
            self._svg_str += get_header(self.data.w + Label.margin, self.data.h + Label.margin)
        self._svg_str += get_fuse_container(self.data.h, x=self.data.x, y=self.data.y, highlight=(self.highlight and not final))
        for i, line in enumerate(self.data.fuses):
            self._svg_str += get_fuse_line(line["tag"], line["desc"], line["part"], 18 + i * self._text_spacing, x=self.data.x, y=self.data.y)
        if headers:
            self._svg_str += get_footer()
        self._changed = False
        return self._svg_str
