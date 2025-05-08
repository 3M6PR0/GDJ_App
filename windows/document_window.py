# windows/document_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot
from ui.components.custom_titlebar import CustomTitleBar
from pages.documents_open.documents_open_page import DocumentsOpenPage
import logging
logger = logging.getLogger('GDJ_App')

class DocumentWindow(QWidget):
    request_main_action = pyqtSignal(str)
    def __init__(self, main_controller, initial_doc_type=None, initial_doc_data=None, parent=None):
        super().__init__(parent)
        self.main_controller = main_controller
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setObjectName("DocumentWindow")

        self.initial_doc_type = initial_doc_type
        self.initial_doc_data = initial_doc_data if initial_doc_data is not None else {}
        self.documents_open_page = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        window_title = f"Document - {self.initial_doc_type}" if self.initial_doc_type else "Document"
        self.title_bar = CustomTitleBar(self, title=window_title, icon_base_name="logo-gdj.png", show_menu_button_initially=True)
        main_layout.addWidget(self.title_bar)

        try:
            if hasattr(self.title_bar, 'new_document_requested'):
                 self.title_bar.new_document_requested.connect(self._handle_new_document_request)
                 logger.info("DocumentWindow: Connecté title_bar.new_document_requested -> _handle_new_document_request")
            else:
                 logger.warning("DocumentWindow: title_bar n'a pas le signal 'new_document_requested'.")
        except Exception as e_connect:
             logger.error(f"DocumentWindow: Erreur connexion new_document_requested: {e_connect}")

        separator_line = QFrame(self)
        separator_line.setObjectName("TitleSeparatorLine")
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Plain)
        separator_line.setFixedHeight(1)
        main_layout.addWidget(separator_line)

        try:
            logger.info(f"DocumentWindow: Instanciation de DocumentsOpenPage avec type='{self.initial_doc_type}' et data='{self.initial_doc_data}'")
            self.documents_open_page = DocumentsOpenPage(initial_doc_type=self.initial_doc_type, initial_doc_data=self.initial_doc_data)
            main_layout.addWidget(self.documents_open_page, 1)
        except Exception as e_page:
            logger.error(f"Erreur lors de l\'instanciation de DocumentsOpenPage: {e_page}", exc_info=True)
            error_label = QLabel(f"Erreur: Impossible de charger la page principale des documents.\n{e_page}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red;")
            main_layout.addWidget(error_label, 1)

        self.setLayout(main_layout)
        logger.info(f"DocumentWindow instance créée pour type: {self.initial_doc_type}")

        self.installEventFilter(self)

    def add_document_in_new_tab(self, doc_type: str, data: dict):
        """Relaye la demande d'ajout d'un nouvel onglet à la DocumentsOpenPage contenue."""
        if hasattr(self, 'documents_open_page') and self.documents_open_page and \
           hasattr(self.documents_open_page, 'add_new_document_to_tabs'):
            logger.info(f"DocumentWindow: Demande d'ajout d'onglet relayée à DocumentsOpenPage pour type='{doc_type}'.")
            self.documents_open_page.add_new_document_to_tabs(doc_type, data)
        else:
            if not hasattr(self, 'documents_open_page') or not self.documents_open_page:
                 logger.error("DocumentWindow: Référence interne à documents_open_page non trouvée.")
            elif not hasattr(self.documents_open_page, 'add_new_document_to_tabs'):
                 logger.error("DocumentWindow: La page documents_open_page n'a pas la méthode add_new_document_to_tabs.")
            else:
                 logger.error("DocumentWindow: Erreur inconnue lors de la tentative d'appel de add_new_document_to_tabs sur documents_open_page.")

    @pyqtSlot()
    def _handle_new_document_request(self):
        logger.info("DocumentWindow: Reçu new_document_requested de title_bar, émission de request_main_action('new_document').")
        self.request_main_action.emit('new_document')

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonPress:
            if self.title_bar.btn_file and self.title_bar.btn_file.isVisible():
                if not self.title_bar.geometry().contains(event.pos()):
                    self.title_bar.show_initial_state()
        
        return super().eventFilter(obj, event)

# Optionnel: pour tester cette fenêtre seule
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    # Le test seul ne fonctionnera plus directement sans MainController pour passer en argument
    # Mais le code de la classe est là.
    # app = QApplication(sys.argv)
    # # Besoin de simuler un main_controller pour le constructeur
    # class MockMainController: pass
    # controller = MockMainController()
    # window = DocumentWindow(main_controller=controller, initial_doc_type="Test Type", initial_doc_data={})
    # window.resize(800, 600)
    # window.show()
    # sys.exit(app.exec_())
    pass 