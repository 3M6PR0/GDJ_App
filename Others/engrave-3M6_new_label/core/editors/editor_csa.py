from datetime import date
from core.label.label_csa import DataCSA
from core.static import get_key_from_value, open_dialog_filepath
from core.template import EditorTemplate


class EditorCSA(EditorTemplate):
    def create_layout(self):
        _values_volts = [600, 480, 240, 120]
        _values_phase = ["3 φ 3 Fils/Wires", "1 φ 2 Fils/Wires"]
        vals = DataCSA()
        logo_keys = [*list(vals.paths_logo.keys()), "Custom ..."]
        self.entry_logo = self._create_entry("Logo", logo_keys[0], self.update_data, presets=logo_keys)
        self.entry_nref = self._create_entry("NRef", vals.nref, self.update_data)
        self.entry_volt = self._create_entry("Volts", vals.volts, self.update_data, presets=_values_volts)
        self.entry_phase = self._create_entry("Phases", vals.phases, self.update_data, presets=_values_phase)
        self.entry_amps = self._create_entry("Amps", vals.amps, self.update_data)
        self.entry_hz = self._create_entry("Hz", vals.hz, self.update_data, presets=[60, 50])
        self.entry_panel_type = self._create_entry("Panel type", vals.panel_type, self.update_data, presets=[12, 4, "4X"])
        self.entry_scr = self._create_entry("SCR", vals.scr, self.update_data)
        self.entry_torque = self._create_entry("Torque", vals.torque, self.update_data)
        self.checkbox_csa = self._create_checkbox("CSA-CUS", self.update_data)
        self._create_separator()

        _in_heads = ["Input Circuit", "Volts", "Amps"]
        _in_presets =[["Circuit 1"], _values_volts, None]
        self.entry_in_circ, self.entry_in_volts, self.entry_in_amps = self._create_line_entry(
            _in_heads, self.on_add_in_circ, self.on_rm_in_circ,  presets=_in_presets)
        self._create_separator()

        _out_heads = ["Output Circuit", "Volts", "Amps"]
        _out_presets =[None, _values_volts, None]
        self.entry_out_circ, self.entry_out_volts, self.entry_out_amps = self._create_line_entry(
            _out_heads, self.on_add_out_circ, self.on_remove_out_circ, presets=_out_presets)
        self.checkbox_add_V = self._create_checkbox("Auto-add \'V\'", self.update_data, state=2)
        self.checkbox_add_A = self._create_checkbox("Auto-add \'A\'", self.update_data, state=2)

    def set_data(self, lbl):
        if not lbl:
            return
        self.entry_logo.setText(str(get_key_from_value(lbl.data.paths_logo, lbl.data.path_img_com)))
        self.entry_volt.setText(str(lbl.data.volts))
        self.entry_phase.setText(lbl.data.phases)
        self.entry_amps.setText(str(lbl.data.amps))
        self.entry_nref.setText(lbl.data.nref)
        self.entry_hz.setText(str(lbl.data.hz))
        self.entry_panel_type.setText(str(lbl.data.panel_type))
        self.entry_scr.setText(str(lbl.data.scr))
        self.entry_torque.setText(str(lbl.data.torque))
        self.checkbox_csa.setCheckState(2 if lbl.data.cus else 0)
        self.checkbox_add_V.setCheckState(2 if lbl.data.addV else 0)
        self.checkbox_add_A.setCheckState(2 if lbl.data.addA else 0)

    def update_data(self):
        if not self.callback_label():
            return
        if self.entry_logo.text() not in DataCSA.paths_logo.keys():
            _path = open_dialog_filepath()
            if _path:
                new_key = "Custom "+str(len(DataCSA.paths_logo.keys())-2)
                DataCSA.paths_logo[new_key] = _path
                self.entry_logo.addCustomItem(new_key)
                self.entry_logo.setText(new_key)
            else:
                self.entry_logo.setText("Jacmar")

        self.callback_label().data.cus = self.checkbox_csa.checkState() == 2
        self.callback_label().data.addV = self.checkbox_add_V.checkState() == 2
        self.callback_label().data.addA = self.checkbox_add_A.checkState() == 2
        self.callback_label().data.path_img_com = self.callback_label().data.paths_logo[self.entry_logo.text()]
        self.callback_label().data.volts = self.entry_volt.text()
        self.callback_label().data.phases = self.entry_phase.text()
        self.callback_label().data.amps = self.entry_amps.text()
        self.callback_label().data.nref = self.entry_nref.text()
        self.callback_label().data.hz = self.entry_hz.text()
        self.callback_label().data.panel_type = self.entry_panel_type.text()
        self.callback_label().data.torque = self.entry_torque.text()
        self.callback_label().data.scr = self.entry_scr.text()
        self.callback_label().data.date = date.today().strftime("%Y-%m-%d")
        self.callback_label().updated()
        self._root.update_display()

    def on_add_in_circ(self):
        if not self.callback_label():
            return
        self.callback_label().data.circuit_inputs.append({
            "name": self.entry_in_circ.text(),
            "volts": self.entry_in_volts.text(),
            "amps": self.entry_in_amps.text()
        })
        self.callback_label().updated()
        self._root.update_display()

    def on_add_out_circ(self):
        if not self.callback_label():
            return
        self.callback_label().data.circuit_outputs.append({
            "name": self.entry_out_circ.text(),
            "volts":self.entry_out_volts.text(),
            "amps": self.entry_out_amps.text()
        })
        self.callback_label().updated()
        self._root.update_display()

    def on_rm_in_circ(self):
        if not self.callback_label():
            return
        self.callback_label().data.circuit_inputs = self.callback_label().data.circuit_inputs[:-1]
        self.callback_label().updated()
        self._root.update_display()

    def on_remove_out_circ(self):
        if not self.callback_label():
            return
        self.callback_label().data.circuit_outputs = self.callback_label().data.circuit_outputs[:-1]
        self.callback_label().updated()
        self._root.update_display()




