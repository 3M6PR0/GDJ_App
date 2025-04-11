from models.document import Document

class RapportDepense(Document):
    def __init__(self, title="Rapport Dépense", content="", depenses=None):
        super().__init__(title, content)
        self.depenses = depenses if depenses is not None else []

    def validate(self):
        """Valide que le rapport contient au moins une dépense."""
        return len(self.depenses) > 0
