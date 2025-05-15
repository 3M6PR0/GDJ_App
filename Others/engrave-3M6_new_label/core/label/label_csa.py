from datetime import date
from core.static import get_res_item
from core.template import *
from core.xml_templates import *


class DataCSA(DataLabel):
    paths_logo = {
        "Jacmar": get_res_item("logo_jacmar.png"),
        "Automacad": get_res_item("logo_automacad.png"),
        "Systemes Ride": get_res_item("logo_systemesride.png"),
        "Cleaverbrooks": get_res_item("logo_cleaverbrooks.png")
    }
    def __init__(self):
        super().__init__()
        self.csa_path = get_res_item("logo_csa.png")
        self.path_img_com = self.paths_logo["Jacmar"]
        self.csa_code = "164355"
        self.volts = 600
        self.phases = "3 φ 3 Fils/Wires"
        self.hz = 60
        self.date = date.today().strftime("%Y-%m-%d")
        self.amps = 30
        self.temp = "0-40°C"
        self.panel_type = 12
        self.nref = "FAB1000"
        self.torque = ""
        self.scr = 100
        self.cus = False
        self.circuit_inputs = []
        self.circuit_outputs = []
        self.addV = True
        self.addA = True

class LabelCSA(Label):
    code = LabelCode.CSA
    def __init__(self):
        super().__init__()
        self.data = DataCSA()
        self._lbl_base_height = 78

    def get_svg(self, headers=True, final=False):
        if not self._changed and not final:
            return self._svg_str
        self._svg_str = ""
        self.data.h = self._lbl_base_height + self._text_spacing * max(len(self.data.circuit_inputs), len(self.data.circuit_outputs))
        if headers:
            self._svg_str += get_header(self.data.w + 2, self.data.h + 2)

        _dx = self.data.x
        _dy = self.data.y
        self._svg_str += get_csa_container(self.data.h, x=_dx, y=_dy, highlight=(self.highlight and not final))
        self._svg_str += get_logo_company(self.data.path_img_com, x=5.8+_dx, y=2+_dy)
        self._svg_str += get_logo_csa(self.data.csa_path, x=_dx, y=_dy)
        self._svg_str += get_csa_fields(self.data.csa_code, self.data.volts, self.data.phases,
                                        self.data.hz, self.data.date, self.data.amps, self.data.temp,
                                        self.data.panel_type, self.data.nref, self.data.torque, x=_dx, y=_dy)
        if self.data.cus:
            self._svg_str += get_csa_cus(x=_dx, y=_dy)
        self._svg_str += get_csa_scr(self.data.volts, self.data.scr, x=_dx, y=_dy)
        _endV = " V" if self.data.addV else ""
        _endA = " A" if self.data.addA else ""
        for i, ic in enumerate(self.data.circuit_inputs):
            _h = self._lbl_base_height + i * self._text_spacing
            _v: str = str(ic["volts"]) + _endV
            _a: str = str(ic["amps"]) + _endA
            self._svg_str += get_csa_input_circuit(ic["name"], _v, _a, _h, x=_dx, y=_dy)
        for i, oc in enumerate(self.data.circuit_outputs):
            _h = self._lbl_base_height + i * self._text_spacing
            _v: str = str(oc["volts"]) + _endV
            _a: str = str(oc["amps"]) + _endA
            self._svg_str += get_csa_output_circuit(oc["name"], _v, _a, _h, x=_dx, y=_dy)
        if headers:
            self._svg_str += get_footer()
        self._changed = False
        return self._svg_str
