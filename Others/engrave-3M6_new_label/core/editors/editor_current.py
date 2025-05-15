from core.template import EditorTemplate


class EditorCurrent(EditorTemplate):
    def create_layout(self):
        _values_volts = [600, 480, 240, 120]
        self.entry_volts = self._create_entry("Volts", 120, self.update_data, presets=_values_volts)
        self.entry_amps = self._create_entry("Amps", 2, self.update_data)

    def set_data(self, lbl):
        if not lbl:
            return
        # Seems to call update_fields because of textChanged
        self.entry_volts.setText(str(lbl.data.volts))
        self.entry_amps.setText(str(lbl.data.amps))

    def update_data(self):
        if not self.callback_label():
            return
        self.callback_label().data.volts = self.entry_volts.text()
        self.callback_label().data.amps = self.entry_amps.text()
        self.callback_label().updated()
        self._root.update_display()