import logging
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (QWidget)

logger = logging.getLogger(__name__)



class ChatBotUI(QWidget):


    def __init__(self, parent=None, usdviewApi=None):
        super().__init__(parent)
        self.initUI()
        self.usdviewApi = usdviewApi
        self.setWindowTitle("🤖 USDChat")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        width, height = (
            670,
            screen_size.height() - 100,
        )
        self.setMinimumWidth(width)
        self.resize(width, height)

    def initUI(self):
        self.webView = QWebEngineView(self)
        self.webView.load(QUrl("http://localhost:3000"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.webView)
        self.setLayout(layout)