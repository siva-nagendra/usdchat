import sys
from PySide6.QtWidgets import QApplication
from USDChat.views.chat_widget import ChatBotUI


def main():
    app = QApplication(sys.argv)
    chat_ui = ChatBotUI()
    chat_ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
