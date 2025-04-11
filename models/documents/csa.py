from models.document import Document

class CSA(Document):
    def __init__(self, title="CSA", content="", details=None):
        super().__init__(title, content)
        self.details = details if details is not None else {}

    def validate(self):
        """Valide que des détails sont présents."""
        return bool(self.details)
