from PyQt5.QtWidgets import QLayout

def _get_nested_attr(obj, attr_path, default=None):
    """Accède à un attribut imbriqué en utilisant une chaîne de caractères (ex: 'profile.nom').""" 
    attributes = attr_path.split('.')
    for attr in attributes:
        try:
            # Gérer les dictionnaires et les objets
            if isinstance(obj, dict):
                obj = obj.get(attr)
                if obj is None: return default
            else:
                obj = getattr(obj, attr)
        except (AttributeError, KeyError):
            return default
    return obj

def clear_layout(layout: QLayout):
    """Supprime tous les widgets d'un layout donné."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            # Gérer aussi les layouts imbriqués
            elif item.layout() is not None:
                clear_layout(item.layout())

print("utils/helpers.py defined.") 