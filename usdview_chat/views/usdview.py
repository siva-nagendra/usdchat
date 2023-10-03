from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from PySide6 import QtWidgets, QtCore
from . import chat_widget
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QDockWidget, QLabel, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

active_chat_ui_instance = None

def onStartup(usdviewApi):
    load_chat_widget(usdviewApi)

class USDChatPluginContainer(PluginContainer):

    def registerPlugins(self, plugRegistry, usdviewApi):
        # Register command plugin to create and show ChatWidget
        self._load_chat_widget = plugRegistry.registerCommandPlugin(
            "USDChatPluginContainer.load_chat_widget",
            "Load Chat Widget",
            lambda usdviewApi: load_chat_widget(usdviewApi)
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

    def toggle_content(self):
        self._content_visible = not self._content_visible
        self.widget().setVisible(self._content_visible)
        if self._content_visible:
            self.toggle_button.setText("🤖 USDChat")
            self.toggle_button.setFont(QFont("Sans-serif", 12))  # Resetting to a standard font size
        else:
            self.toggle_button.setText("🤖")
            self.toggle_button.setFont(QFont("Sans-serif", 35))

def load_chat_widget(usdviewApi):
    global active_chat_ui_instance

    if active_chat_ui_instance is None or not active_chat_ui_instance.isVisible():
        active_chat_ui_instance = chat_widget.ChatBotUI(parent=usdviewApi.qMainWindow)
        dock_widget = CollapsibleDockWidget("🤖 USDChat", usdviewApi.qMainWindow)
        dock_widget.setWidget(active_chat_ui_instance)
        usdviewApi.qMainWindow.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
        dock_widget.show()
    else:
        active_chat_ui_instance.raise_()

Tf.Type.Define(USDChatPluginContainer)
