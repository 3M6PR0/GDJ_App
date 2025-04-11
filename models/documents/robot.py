from models.document import Document

class Robot(Document):
    def __init__(self, title="Robot", content="", config=None):
        super().__init__(title, content)
        self.config = config if config is not None else {}

    def validate(self):
        """Valide que la configuration du robot est renseignée."""
        return bool(self.config)
