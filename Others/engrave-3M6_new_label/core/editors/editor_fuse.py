from core.template import EditorTemplate

_presets = [
    None, [
        "Glass Fuse Temporised 250V - ",
        "Glass Fuse 250V Fast - ",
        "Class J Time-Delay Fuse 600Vac/300Vdc, Indication - ",
        "Class J High-Speed Fuse 600Vac/450Vdc - ",
        "Class L Time-Delay Fuse - ",
        "Type CC Time-Delay 600Vac/300Vdc - ",
        "Type J Time-Delay Fuse - ",
        "KLKR Series Fast-Acting Fuse - "
    ],
    [
        "CCMR",
        "GMC-",
        "GMA-",
        "LP-CC-",
        "JTD",
        "LPJ-??SP",
        "KLKR",
        "KLLU",
        "DFJ-"
    ]
]

class EditorFuse(EditorTemplate):
    def create_layout(self):
        _heads = ["Tags", "Description", "Part"]
        self.entry_tags, self.entry_desc, self.entry_part  = self._create_line_entry(
            _heads, self.on_add_fuse, self.on_rm_fuse, _presets)
        self._create_separator()
        self._create_text("")
        self._create_text("JTD?ID\t\t: Class J Time-Delay Fuses, Indication - ??A")
        self._create_text("KLLU???\t\t: Class L Time-Delay Fuses - ??A")
        self._create_text("DFJ-???\t\t: Class J High-Speed Fuse 600Vac/450Vdc - ??A")
        self._create_text("GMC-?\t\t: Glass Fuse 250V Temporised - ??A")
        self._create_text("GMA-?\t\t: Glass Fuse 250V Fast - ??A")
        self._create_text("LPJ-??SP\t: Type J Time-Delay Fuse - ??A")
        self._create_text("LP-CC-?\t\t: Type CC Time-Delay 600Vac/300Vdc - ??A")
        self._create_text("CCMR?\t\t: Type CC Time-delay - ??A")
        self._create_text("KLKR???\t\t: KLKR Series Fast-Acting Fuse - ??A")

    def on_add_fuse(self):
        if not self.callback_label():
            return
        self.callback_label().data.fuses.append({
            "tag": self.entry_tags.text(),
            "desc": self.entry_desc.text(),
            "part": self.entry_part.text()
        })
        self.callback_label().updated()
        self._root.update_display()

    def on_rm_fuse(self):
        if not self.callback_label():
            return
        if len(self.callback_label().data.fuses) > 0:
            self.callback_label().data.fuses = self.callback_label().data.fuses[:-1]
        self.callback_label().updated()
        self._root.update_display()
