import logging
import threading

from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDockWidget, QPushButton, QSizePolicy

from USDChat.views import chat_widget

logging.basicConfig(level=logging.INFO)


active_chat_ui_instance = None


class USDViewAPIManager:
    __instance = None
    __lock = threading.Lock()
    __initialized_event = threading.Event()  # New line

    @staticmethod
    def getInstance():
        with USDViewAPIManager.__lock:
            if USDViewAPIManager.__instance is None:
                raise Exception("usdviewApi not initialized yet")
            return USDViewAPIManager.__instance

    @staticmethod
    def setInstance(usdviewApi):
        with USDViewAPIManager.__lock:
            if USDViewAPIManager.__instance is None:
                USDViewAPIManager.__instance = usdviewApi
                USDViewAPIManager.__initialized_event.set()  # New line
            else:
                raise Exception("usdviewApi already initialized")


def onStartup(usdviewApi):
    load_chat_widget(usdviewApi)


class USDChatPluginContainer(PluginContainer):
    def registerPlugins(self, plugRegistry, usdviewApi):
        # Initialize the singleton here
        USDViewAPIManager.setInstance(usdviewApi)
        self._load_chat_widget = plugRegistry.registerCommandPlugin(
            "USDChatPluginContainer.load_chat_widget",
            "Load Chat Widget",
            load_chat_widget,  # Use partial here
        )
        onStartup(usdviewApi)

    def configureView(self, plugRegistry, plugUIBuilder):
        # Create or find the USDChat menu
        usdchat_menu = plugUIBuilder.findOrCreateMenu("🤖 USDChat")
        # Add the command plugin to the menu
        usdchat_menu.addItem(self._load_chat_widget)


class CollapsibleDockWidget(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.toggle_button = QPushButton("🤖 USDChat")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.clicked.connect(self.toggle_content)
        self.setTitleBarWidget(self.toggle_button)
        self._content_visible = True
        self._preferred_size = None  # Store the preferred size

    def toggle_content(self):
        self._content_visible = not self._content_visible
        self.widget().setVisible(self._content_visible)
        if self._content_visible:
            self.toggle_button.setText("🤖 USDChat")
            self.toggle_button.setFont(
                QFont("Sans-serif", 12)
            )  # Resetting to a standard font size
            if self._preferred_size:
                self.widget().resize(self._preferred_size)  # Restore the preferred size
        else:
            self.toggle_button.setText("🤖")
            self.toggle_button.setFont(QFont("Sans-serif", 35))
            self._preferred_size = self.widget().size()


def load_chat_widget(usdviewApi=None):
    global active_chat_ui_instance

    if usdviewApi is None:
        usdviewApi = USDViewAPIManager.getInstance()

    if active_chat_ui_instance is None or not active_chat_ui_instance.isVisible():
        active_chat_ui_instance = chat_widget.ChatBotUI(
            usdviewApi, parent=usdviewApi.qMainWindow
        )

        dock_widget = CollapsibleDockWidget(
            "🤖 USDChat", usdviewApi.qMainWindow)
        dock_widget.setWidget(active_chat_ui_instance)
        usdviewApi.qMainWindow.addDockWidget(
            Qt.RightDockWidgetArea, dock_widget)
        dock_widget.show()

        # Added Expanding size policy to dock_widget
        dock_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    else:
        active_chat_ui_instance.raise_()


Tf.Type.Define(USDChatPluginContainer)
