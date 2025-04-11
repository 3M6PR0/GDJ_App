from models.document import Document

class RapportTempsSup(Document):
    def __init__(self, title="Rapport Temps Sup", content="", heures=0):
        super().__init__(title, content)
        self.heures = heures

    def validate(self):
        """Valide que le nombre d'heures est supérieur à zéro."""
        return self.heures > 0
