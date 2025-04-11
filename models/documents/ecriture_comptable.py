from models.document import Document

class EcritureComptable(Document):
    def __init__(self, title="Écriture Comptable", content="", operations=None):
        super().__init__(title, content)
        self.operations = operations if operations is not None else []

    def validate(self):
        """Valide que l'écriture comptable contient au moins une opération."""
        return len(self.operations) > 0
