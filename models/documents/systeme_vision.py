from models.document import Document

class SystemeVision(Document):
    def __init__(self, title="Système Vision", content="", vision_params=None):
        super().__init__(title, content)
        self.vision_params = vision_params if vision_params is not None else {}

    def validate(self):
        """Valide que les paramètres de vision sont renseignés."""
        return bool(self.vision_params)
