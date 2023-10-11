import os
import sys

from PySide6.QtWidgets import QApplication
from usdchat.config.config import Config
from usdchat.utils.conversation_manager import ConversationManager
from usdchat.views.chat_widget import ChatBotUI

def get_file_from_current_path(filename):
    current_file_path = os.path.abspath(__file__)
    current_dir_path = os.path.dirname(current_file_path)
    req_path = os.path.join(current_dir_path, filename)
    return req_path

def main():
    config = Config()
    config.load_from_yaml(get_file_from_current_path("config/standalone_config.yaml"))
    conversation_manager = ConversationManager(new_session=True, config=config)

    app = QApplication(sys.argv)
    chat_ui = ChatBotUI(config=config, conversation_manager=conversation_manager, standalone=True)
    chat_ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
