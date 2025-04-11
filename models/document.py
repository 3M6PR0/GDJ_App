class Document:
    def __init__(self, title="Document", content=""):
        self.title = title
        self.content = content

    def save(self, filepath):
        """Sauvegarde le contenu dans un fichier."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.content)

    def load(self, filepath):
        """Charge le contenu depuis un fichier."""
        with open(filepath, "r", encoding="utf-8") as f:
            self.content = f.read()

    def validate(self):
        """Méthode à surcharger par les sous-classes."""
        raise NotImplementedError("La méthode validate doit être implémentée dans la sous-classe.")
