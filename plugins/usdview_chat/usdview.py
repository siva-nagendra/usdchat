import logging
import os
import threading

from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDockWidget, QPushButton, QSizePolicy

from usdchat.config.config import Config
from usdchat.utils.conversation_manager import ConversationManager
from usdchat.views import chat_widget

logging.basicConfig(level=logging.WARNING)


active_chat_ui_instance = None


class USDViewAPIManager:
    __instance = None
    __lock = threading.Lock()
    __initialized_event = threading.Event()

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
                USDViewAPIManager.__initialized_event.set()
            else:
                raise Exception("usdviewApi already initialized")


def onStartup(usdviewApi):
    load_chat_widget(usdviewApi)


class USDChatPluginContainer(PluginContainer):
    def registerPlugins(self, plugRegistry, usdviewApi):
        USDViewAPIManager.setInstance(usdviewApi)
        self._load_chat_widget = plugRegistry.registerCommandPlugin(
            "USDChatPluginContainer.load_chat_widget",
            "Load Chat Widget",
            load_chat_widget,
        )
        onStartup(usdviewApi)

    def configureView(self, plugRegistry, plugUIBuilder):
        usdchat_menu = plugUIBuilder.findOrCreateMenu("🤖 USDChat")
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
        self._preferred_size = None

    def toggle_content(self):
        self._content_visible = not self._content_visible
        self.widget().setVisible(self._content_visible)
        if self._content_visible:
            self.toggle_button.setText("🤖 USDChat")
            self.toggle_button.setFont(QFont("Sans-serif", 12))
            if self._preferred_size:
                self.widget().resize(self._preferred_size)
        else:
            self.toggle_button.setText("🤖")
            self.toggle_button.setFont(QFont("Sans-serif", 35))
            self._preferred_size = self.widget().size()


def get_file_from_current_path(filename):
    current_file_path = os.path.abspath(__file__)
    current_dir_path = os.path.dirname(current_file_path)
    req_path = os.path.join(current_dir_path, filename)
    return req_path


def load_chat_widget(usdviewApi=None):
    global active_chat_ui_instance

    if usdviewApi is None:
        usdviewApi = USDViewAPIManager.getInstance()

    config = Config()
    config.load_from_yaml(
        get_file_from_current_path("usdview_chat_config.yaml"))
    conversation_manager = ConversationManager(new_session=True, config=config)

    if active_chat_ui_instance is None or not active_chat_ui_instance.isVisible():
        active_chat_ui_instance = chat_widget.ChatBotUI(
            config,
            conversation_manager=conversation_manager,
            usdviewApi=usdviewApi,
            parent=usdviewApi.qMainWindow,
        )

        dock_widget = CollapsibleDockWidget(
            "🤖 USDChat", usdviewApi.qMainWindow)
        dock_widget.setWidget(active_chat_ui_instance)
        usdviewApi.qMainWindow.addDockWidget(
            Qt.RightDockWidgetArea, dock_widget)
        dock_widget.show()

        dock_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    else:
        active_chat_ui_instance.raise_()


Tf.Type.Define(USDChatPluginContainer)
