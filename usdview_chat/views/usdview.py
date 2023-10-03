from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer
from PySide6 import QtWidgets, QtCore
from . import chat_widget  # Assuming chat_widget.py is in the same directory

class USDChatPluginContainer(PluginContainer):

    def registerPlugins(self, plugRegistry, usdviewApi):
        # Register command plugin to create and show ChatWidget
        self._load_chat_widget = plugRegistry.registerCommandPlugin(
            "USDChatPluginContainer.load_chat_widget",
            "Load Chat Widget",
            lambda usdviewApi: load_chat_widget(usdviewApi)
        )

    def configureView(self, plugRegistry, plugUIBuilder):
        # Create or find the USDChat menu
        usdchat_menu = plugUIBuilder.findOrCreateMenu("🤖 USDChat")
        # Add the command plugin to the menu
        usdchat_menu.addItem(self._load_chat_widget)

def load_chat_widget(usdviewApi):
    chat_ui_instance = chat_widget.ChatBotUI()
    dock_widget = chat_ui_instance.get_dock_widget(parent=usdviewApi.qMainWindow)
    usdviewApi.qMainWindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
    dock_widget.show()
    return dock_widget

Tf.Type.Define(USDChatPluginContainer)
