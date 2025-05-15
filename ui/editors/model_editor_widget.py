from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger('GDJ_App')

class ModelEditorWidget(QWidget):
    """
    Widget destiné à l'édition des Modèles Lamicoid.
    Un Modèle est basé sur une Disposition et permet de pré-remplir certains champs.
    Utilisera potentiellement QGraphicsView pour visualiser la disposition sous-jacente.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModelEditorWidget")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.placeholder_label = QLabel("Éditeur de Modèle Lamicoid (Placeholder)\nIci, on pourra choisir une Disposition, nommer le Modèle, et pré-remplir des zones.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("QLabel { font-size: 16px; color: #AAAAAA; border: 1px dashed #777777; padding: 20px; background-color: #F0F0F0; }") # Fond légèrement différent
        
        layout.addWidget(self.placeholder_label)
        
        logger.debug("ModelEditorWidget initialisé.")

    def load_model(self, model_data=None, base_disposition_data=None):
        """
        Chargera les données d'un modèle existant pour édition, 
        ou préparera l'éditeur pour un nouveau modèle basé sur une disposition.
        """
        if model_data:
            logger.info(f"Chargement des données du modèle: {model_data.get('name', 'N/A')}")
            # Logique de chargement du modèle
            self.placeholder_label.setText(f"Éditeur de Modèle Lamicoid\n(Simule chargement Modèle: {model_data.get('name')})\nBasé sur Disposition: {model_data.get('base_disposition_name', 'Inconnue')}")
        elif base_disposition_data:
            logger.info(f"Préparation de l'éditeur pour un nouveau modèle basé sur la disposition: {base_disposition_data.get('name', 'N/A')}")
            # Logique pour un nouveau modèle
            self.placeholder_label.setText(f"Éditeur de Modèle Lamicoid\nNouveau Modèle basé sur Disposition: {base_disposition_data.get('name', 'Inconnue')}")
        else:
            logger.warning("Chargement de l'éditeur de modèle sans données de modèle ni de disposition de base.")
            self.placeholder_label.setText("Éditeur de Modèle Lamicoid\n(Veuillez d'abord sélectionner ou créer une Disposition)")


    def get_model_data(self):
        """
        Récupérera les données du modèle actuellement édité.
        """
        logger.info("Récupération des données du modèle (simulation).")
        return {"name": "modele_simule", "base_disposition_name": "disp_standard", "prefilled_zones": {}} # Données simulées


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)
    main_win = QMainWindow()
    
    editor = ModelEditorWidget()
    main_win.setCentralWidget(editor)
    # Test différents scénarios de chargement
    # editor.load_model() # Sans rien
    editor.load_model(base_disposition_data={"name": "Ma Disposition de Base"}) # Nouveau modèle
    # editor.load_model(model_data={"name": "Mon Super Modèle", "base_disposition_name": "Disp Alpha"}) # Modèle existant
    
    main_win.setWindowTitle("Test ModelEditorWidget")
    main_win.resize(600, 400)
    main_win.show()
    sys.exit(app.exec_()) 