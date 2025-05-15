from core.static import solve_rect_position
from core.template import LabelCode, Label


class LabelManager:
    def __init__(self, labels, editors):
        self._labels = labels
        self._editors : dict = editors
        self._lbl_current = None
        self._lbl_code = LabelCode.CSA
        self._lbl_copied = None

    @property
    def active_editor(self):
        return self._editors[self._lbl_code]

    def current_label(self) -> Label:
        return self._lbl_current

    def add(self):
        self.active_editor.detach()
        _x = 10 if not bool(self._lbl_current) else self._lbl_current.x + 5
        _y = 10 if not bool(self._lbl_current) else self._lbl_current.y + 5
        self._lbl_current = self.active_editor.create_label()
        self._lbl_current.x = _x
        self._lbl_current.y = _y
        self.active_editor.attach(self._lbl_current)
        self._labels.add(self._lbl_current)

    def copy(self):
        if self._lbl_current:
            self._lbl_copied = self._lbl_current.copy()

    def paste(self):
        if not self._lbl_copied:
            return
        self._lbl_current = self._lbl_copied.copy()
        self._lbl_current.x += 5
        self._lbl_current.y += 5
        self._lbl_copied = self._lbl_current.copy()
        self.active_editor.detach()
        self._labels.add(self._lbl_current)
        self.select_label(self._lbl_current)

    def selected_delete(self):
        if not self._lbl_current:
            return
        self._labels.remove(self._lbl_current)
        self.active_editor.detach()
        self._lbl_current = None

    def select_label(self, lbl: Label):
        self._lbl_current = lbl
        self.active_editor.detach()
        if lbl is None:
            return
        if lbl.code is not self._lbl_code:
            self._lbl_code = lbl.code   # Changes active editor
            self.active_editor.bring_up()
            self.active_editor.detach()
        self.active_editor.attach(self._lbl_current)

    def set_editor_idx(self, editor_idx):
        # Called when the combobox is selected or when using self.active_editor.bring_up()
        if editor_idx == self._lbl_code:
            return
        if not self._lbl_current:
            self.active_editor.detach()
            self._lbl_code = editor_idx
            return
        if editor_idx == self._lbl_current.code:
            return
        self.active_editor.detach()
        self._lbl_code = editor_idx
        self.active_editor.detach()

    # MOVEMENT
    def label_at_pos(self, x, y):
        for l in self._labels:
            if l.within_bbox(x, y):
                return l

    def current_move(self, dx, dy):
        if self._lbl_current:
            bw = self._labels.width()
            bh = self._labels.height()
            solve_rect_position(self._lbl_current, self._labels, bw, bh, dx, dy, margin=2.0)

    def get_labels(self):
        return self._labels