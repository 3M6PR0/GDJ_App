from core.template import *
from core.xml_templates import get_header, get_footer, get_current_label

class DataCurrent(DataLabel):
    def __init__(self):
        super().__init__()
        self.volts = 120
        self.amps = 2

class LabelCurrent(Label):
    code = LabelCode.CURRENT
    def __init__(self):
        super().__init__()
        self.data = DataCurrent()

    def get_svg(self, headers=True, final=False):
        if not self._changed and not final:
            return self._svg_str
        self._svg_str = ""
        if headers:
            self._svg_str += get_header(self.data.w + Label.margin, self.data.h + Label.margin)
        self._svg_str += get_current_label(self.data.h, amps=self.data.amps, volts=self.data.volts,
                                           x=self.data.x, y=self.data.y, highlight=(self.highlight and not final))
        if headers:
            self._svg_str += get_footer()
        self._changed = False
        return self._svg_str
