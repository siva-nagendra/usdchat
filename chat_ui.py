import sys
from PySide6.QtWidgets import QApplication
from views.chat_widget import ChatBotUI


def main():
    """
    Main function that initializes the QApplication and ChatBotUI objects, shows the UI, and starts the event loop.
    """
    app = QApplication(sys.argv)
    chat_ui = ChatBotUI()
    chat_ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
