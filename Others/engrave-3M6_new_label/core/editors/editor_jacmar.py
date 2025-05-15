from datetime import date
from core.label.label_jacmar import DataJacmar # Assurez-vous que DataJacmar est importable
from core.template import EditorTemplate
from core.static import get_res_item # Au cas où, mais pas utilisé ici directement

class EditorJacmar(EditorTemplate):
    def create_layout(self):
        # Valeurs par défaut ou actuelles pour l'initialisation
        # Idéalement, celles-ci proviendraient de l'étiquette si elle est attachée,
        # ou de DataJacmar pour une nouvelle étiquette.
        # Pour l'instant, utilisons les valeurs par défaut de DataJacmar.
        vals = DataJacmar()

        self.entry_nref = self._create_entry("No. Ref:", vals.nref, self.update_data)
        # Le champ Date est supprimé, elle sera gérée automatiquement

    def set_data(self, lbl):
        # lbl est une instance de LabelJacmar
        if not lbl or not hasattr(lbl, 'data') or not isinstance(lbl.data, DataJacmar):
            return
        
        self.entry_nref.setText(str(lbl.data.nref))
        # La date n'est plus définie via un champ d'entrée

    def update_data(self):
        lbl_callback = self.callback_label()
        if not lbl_callback or not hasattr(lbl_callback, 'data') or not isinstance(lbl_callback.data, DataJacmar):
            return

        lbl_callback.data.nref = self.entry_nref.text()
        # La date est automatiquement mise à jour à la date du jour
        lbl_callback.data.date = date.today().strftime("%Y-%m-%d") 

        lbl_callback.updated() # Marquer l'étiquette comme modifiée
        if hasattr(self._root, 'update_display'): # s'assurer que root a update_display
            self._root.update_display() # Mettre à jour l'affichage principal 