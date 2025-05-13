# windows/document_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTabWidget, QMessageBox
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot as Slot
from ui.components.custom_titlebar import CustomTitleBar
from pages.documents_open.documents_open_page import DocumentsOpenPage
from PyQt5.QtWidgets import QApplication
import logging
logger = logging.getLogger('GDJ_App')

class DocumentWindow(QWidget):
    request_main_action = pyqtSignal(str, QWidget)
    def __init__(self, main_controller, initial_doc_type=None, initial_doc_data=None, parent=None):
        super().__init__(parent)
        self.main_controller = main_controller
        self._closed_due_to_last_tab = False
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
            
            if hasattr(self.title_bar, 'close_active_document_requested'):
                self.title_bar.close_active_document_requested.connect(self.close_active_document_tab)
                logger.info("DocumentWindow: Connecté title_bar.close_active_document_requested -> close_active_document_tab")
            else:
                logger.warning("DocumentWindow: title_bar n'a pas le signal 'close_active_document_requested'.")

            if hasattr(self.title_bar, 'close_all_documents_requested'):
                self.title_bar.close_all_documents_requested.connect(self.close_all_document_tabs)
                logger.info("DocumentWindow: Connecté title_bar.close_all_documents_requested -> close_all_document_tabs")
            else:
                logger.warning("DocumentWindow: title_bar n'a pas le signal 'close_all_documents_requested'.")

            if hasattr(self.title_bar, 'close_window_requested'):
                self.title_bar.close_window_requested.connect(self.close)
                logger.info("DocumentWindow: Connecté title_bar.close_window_requested -> close")
            else:
                logger.warning("DocumentWindow: title_bar n'a pas le signal 'close_window_requested'.")

            if hasattr(self.title_bar, 'settings_requested'):
                self.title_bar.settings_requested.connect(self._handle_settings_request)
                logger.info("DocumentWindow: Connecté title_bar.settings_requested -> _handle_settings_request")
            else:
                logger.warning("DocumentWindow: title_bar n'a pas le signal 'settings_requested'.")

        except Exception as e_connect:
             logger.error(f"DocumentWindow: Erreur connexion signaux title_bar: {e_connect}")

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
            if hasattr(self.documents_open_page, 'tab_closed_signal'):
                self.documents_open_page.tab_closed_signal.connect(self._handle_tab_closed)
                logger.info("DocumentWindow: Connecté documents_open_page.tab_closed_signal -> _handle_tab_closed")
            else:
                logger.warning("DocumentWindow: documents_open_page n'a pas le signal 'tab_closed_signal'.")
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

    @Slot()
    def _handle_new_document_request(self):
        logger.info("DocumentWindow: Reçu new_document_requested de title_bar, émission de request_main_action('new_document', self).")
        self.request_main_action.emit('new_document', self)

    @Slot()
    def _handle_settings_request(self):
        logger.info("DocumentWindow: Reçu settings_requested de title_bar, émission de request_main_action('settings', self).")
        self.request_main_action.emit('settings', self)

    @Slot()
    def close_active_document_tab(self):
        """Ferme l'onglet de document actif dans cette fenêtre."""
        if hasattr(self, 'documents_open_page') and self.documents_open_page:
            logger.info("DocumentWindow: Demande de fermeture de l'onglet actif.")
            self.documents_open_page.close_current_tab()
        else:
            logger.warning("DocumentWindow: documents_open_page non disponible pour fermer l'onglet actif.")

    @Slot()
    def close_all_document_tabs(self):
        """Ferme tous les onglets de document dans cette fenêtre."""
        if hasattr(self, 'documents_open_page') and self.documents_open_page:
            logger.info("DocumentWindow: Demande de fermeture de tous les onglets.")
            self.documents_open_page.close_all_tabs()
        else:
            logger.warning("DocumentWindow: documents_open_page non disponible pour fermer tous les onglets.")

    @Slot(int)
    def _handle_tab_closed(self, remaining_tabs):
        logger.info(f"DocumentWindow: Reçu tab_closed_signal. Onglets restants: {remaining_tabs}")
        if remaining_tabs == 0:
            logger.info("DocumentWindow: Dernier onglet fermé, préparation pour afficher WelcomeWindow...")
            self._closed_due_to_last_tab = True
            
            if self.main_controller and hasattr(self.main_controller, 'request_welcome_after_close'):
                self.main_controller.request_welcome_after_close(self)
            
            # --- EMPÊCHER QT DE QUITTER SI C'EST LA DERNIÈRE FENÊTRE LOGIQUE ---
            app = QApplication.instance() # S'assurer que QApplication est importé au début du fichier
            if app and self.main_controller and hasattr(self.main_controller, 'open_document_windows') and len(self.main_controller.open_document_windows) == 1: # Si c'est la dernière DocumentWindow
                logger.debug("DocumentWindow: Temporairement quitOnLastWindowClosed = False avant de fermer.")
                app.setQuitOnLastWindowClosed(False)
            # ----------------------------------------------------------------------
                 
            self.close()

    # --- NOUVELLE MÉTHODE POUR OBTENIR LE DOCUMENT ACTIF ---
    def get_active_document(self):
        """Retourne l'objet document (par exemple, RapportDepense) de l'onglet actif.
        Appelle la méthode correspondante sur la page documents_open_page.
        """
        if hasattr(self, 'documents_open_page') and self.documents_open_page and \
           hasattr(self.documents_open_page, 'get_active_document_object'):
            return self.documents_open_page.get_active_document_object()
        else:
            if not hasattr(self, 'documents_open_page') or not self.documents_open_page:
                logger.warning("DocumentWindow: documents_open_page n'est pas initialisée.")
            elif not hasattr(self.documents_open_page, 'get_active_document_object'):
                logger.warning("DocumentWindow: documents_open_page n'a pas la méthode 'get_active_document_object'.")
            return None
    # --------------------------------------------------------

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonPress:
            if self.title_bar.btn_file and self.title_bar.btn_file.isVisible():
                if not self.title_bar.geometry().contains(event.pos()):
                    self.title_bar.show_initial_state()
        
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        logger.debug(f"DocumentWindow closeEvent received. Closed due to last tab: {self._closed_due_to_last_tab}")
        if not self._closed_due_to_last_tab:
            if self.main_controller and hasattr(self.main_controller, 'open_document_windows') and len(self.main_controller.open_document_windows) <= 1:
                 logger.info("DocumentWindow closeEvent: Fermeture par 'X' de la (potentiellement) dernière DocumentWindow. Acceptation, QApplication devrait gérer.")
                 event.accept()
            else:
                 logger.debug("DocumentWindow closeEvent: Fermeture par 'X', mais d'autres fenêtres existent. Acceptation.")
                 event.accept()
        else:
            logger.debug("DocumentWindow closeEvent: Fermeture initiée par la fermeture du dernier onglet. Acceptation.")
            event.accept()
            logger.debug("DocumentWindow closeEvent: Calling self.deleteLater() as it was closed due to last tab.")
            self.deleteLater()

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