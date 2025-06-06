"""
Ce fichier définit le répertoire 'templates' comme un package Python.
Il rend les classes des pages de templates de documents accessibles.
"""
from .rapport_depense_page import RapportDepensePage
from .lamicoid_page import LamicoidPage

__all__ = [
    'RapportDepensePage',
    'LamicoidPage'
]

# Ce fichier définit le répertoire 'templates' comme un package Python.
# Il peut être laissé vide. 