import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from chat_bot import Chat, Executive
from chat_ui import ChatBotUI
from chat_bridge import ChatBridge

def main():
    app = QApplication(sys.argv)
    icon_path = 'resources/icons/app_icon.ico'
    app.setWindowIcon(QIcon(icon_path))

    # Provide the model name when creating a new Chat instance
    chat_bot = Chat("gpt-4") 

    chat_ui = ChatBotUI() 

    chat_bridge = ChatBridge(chat_bot, chat_ui)
    chat_bridge.start_conversation()

    chat_ui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
