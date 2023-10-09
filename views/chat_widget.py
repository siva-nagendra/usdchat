import logging
import os

from PySide6.QtCore import QFile, QSize, Qt, QTextStream, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QTextEdit,
                               QVBoxLayout, QWidget)

from USDChat.chat_bot import Chat
from USDChat.chat_bridge import ChatBridge
from USDChat.config import Config
from USDChat.utils import chat_thread

logging.basicConfig(
    filename="app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class MessageBubble(QWidget):
    def __init__(self, text, sender, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.current_text = ""
        self.init_ui()
        self.update_text(text)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = self.label.font()
        font.setPointSize(12)  # Set a fixed font size
        self.label.setFont(font)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.label.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(
            self.rect().topLeft(),
            self.rect().bottomLeft())
        if self.sender == "user":
            gradient.setColorAt(0, QColor("#993366"))  # Darker Pink
            gradient.setColorAt(1, QColor("#663366"))  # Darker Purple
        elif self.sender == "bot":
            gradient.setColorAt(0, QColor("#336699"))  # Darker Cyan
            gradient.setColorAt(1, QColor("#336666"))  # Darker Teal
        elif self.sender == "python_bot":
            gradient.setColorAt(0, QColor("#336633"))  # Darker Green
            gradient.setColorAt(1, QColor("#226622"))  # Even Darker Green
        else:
            raise ValueError(
                "Sender must be either 'user', 'bot', or 'python_bot'")

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)  # No border outline
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 5, 5)

    def resizeEvent(self, event):
        self.layout.invalidate()  # Invalidate the current layout
        super().resizeEvent(event)

    def format_text(self, text):
        formatted_text = (
            f'<pre style="white-space: pre-wrap; word-wrap: break-word;">{text}</pre>'
        )
        if self.sender == "user":
            formatted_response = (
                '<div style="text-align: right;">'
                "<b><span>🤷‍♂️ You</span></b>"
                "<hr>"
                f'<div style="text-align: left;">{formatted_text}</div>'
                "</div>"
            )

        elif self.sender == "bot":
            formatted_response = (
                f"<div style='"
                f"border: 2px solid #444;"  # Border styling with darker color for visibility
                f"padding: 10px;"  # Padding inside the border
                f"margin: 5px 0;"  # Margin outside the border
                f"border-radius: 10px;"  # Rounded corners
                # No background color (transparent)
                f"background-color: transparent;"
                f"'>"
                f"{formatted_text}"
                f"</div>"
            )
        elif self.sender == "python_bot":
            formatted_response = (
                f"<div style='"
                f"border: 2px solid #444;"  # Border styling with darker color for visibility
                f"padding: 10px;"  # Padding inside the border
                f"margin: 5px 0;"  # Margin outside the border
                f"border-radius: 10px;"  # Rounded corners
                # No background color (transparent)
                f"background-color: transparent;"
                f"'>"
                f"{formatted_text}"
                f"</div>"
            )
        else:
            raise ValueError(
                "Sender must be either 'user', 'bot', or 'python_bot'")

        return formatted_response

    def update_text(self, new_text):
        logging.info(f"updating text to {new_text}")
        self.current_text += new_text  # Append the new text to the current text
        formatted_text = self.format_text(
            self.current_text)  # Format the current text
        self.label.setText(
            formatted_text
        )  # Set the label text to the formatted current text
        self.label.adjustSize()
        self.adjustSize()
        logging.info(f"updated text to {formatted_text}")


class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent  # Store the parent widget reference
        self.setFixedHeight(
            self.fontMetrics().lineSpacing() + 20
        )  # Set initial height for 1 line + padding

    def keyPressEvent(self, event):
        super().keyPressEvent(event)  # Move this line to the top of the method

        if event.modifiers() & Qt.ShiftModifier and event.key() == Qt.Key_Return:
            # If Shift+Enter is pressed, a new line is already inserted by the call to super().keyPressEvent(event) above
            # Increase the height of the text box by 25 units
            new_height = self.height() + 20
            max_height = (
                self.fontMetrics().lineSpacing() * 15 + 10
            )  # Max height for 6 lines + padding
            new_height = min(
                new_height, max_height
            )  # Ensure the new height does not exceed the maximum height
            self.setFixedHeight(new_height)
        elif event.key() == Qt.Key_Return:
            # If Enter is pressed without Shift, submit the text
            if self.parent_widget:
                # Ensure parent_widget is not None before calling submit_input
                self.parent_widget.submit_input()
        else:
            # Adjust the height of the text box based on its content
            doc_height = self.document().size().height()
            max_height = (
                self.fontMetrics().lineSpacing() * 15 + 10
            )  # Max height for 6 lines + padding
            new_height = min(doc_height + 10, max_height)  # +10 for padding
            self.setFixedHeight(new_height)

    def reset_size(self):
        default_height = (
            self.fontMetrics().lineSpacing() + 20
        )  # The default height for 1 line + padding
        self.setFixedHeight(default_height)


class ChatBotUI(QWidget):
    signal_user_message = Signal(str)
    signal_error_message = Signal(str)

    def __init__(self, usdviewApi, parent=None):
        super().__init__(parent)
        self.usdviewApi = usdviewApi
        self.setWindowTitle(Config.APP_NAME)
        self.language_model = Config.MODEL
        self.chat_bot = Chat(self.language_model)
        self.chat_bridge = ChatBridge(self.chat_bot, self, self.usdviewApi)
        self.chat_thread = chat_thread.ChatThread(
            self.chat_bot, "", self.usdviewApi)

        self.init_ui()
        self.load_stylesheet()
        self.connectSignals()
        self.activateWindow()
        self.raise_()

        # Set the initial size of the widget
        screen = QApplication.primaryScreen()  # Get the primary screen
        screen_size = screen.geometry()  # Get the screen geometry
        # Set width to screen width and height to screen height minus a small
        # margin
        width, height = (
            670,
            screen_size.height() - 100,
        )
        self.setMaximumWidth(width)
        self.resize(width, height)

    def connectSignals(self):
        self.signal_user_message.connect(self.chat_bridge.get_bot_response)
        self.chat_bridge.signal_bot_response.connect(self.append_bot_response)
        self.chat_thread.signal_python_exection_response.connect(
            self.append_python_output
        )

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_area_layout = QVBoxLayout(
            self.scroll_area_widget_contents
        )  # New layout for scroll_area_widget_contents

        self.conversation_widget = QWidget(
            self.scroll_area_widget_contents
        )  # New widget for conversation
        self.conversation_layout = QVBoxLayout(
            self.conversation_widget
        )  # Set conversation_layout to conversation_widget
        self.conversation_layout.addStretch()

        self.welcome_label = QLabel(
            '<html><head/><body><p align="center"><span style=" font-size:24pt;">'
            "Welcome to USD Chat ✨</span></p>"
            '<p align="center"><span style=" font-size:14pt;">Your AI-powered USD Chat assistant!</span></p>'
            "</body></html>", self.scroll_area_widget_contents, )
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("background:transparent;")
        self.welcome_label.adjustSize()  # Adjust the size of the label based on its content

        self.scroll_area_layout.addWidget(
            self.welcome_label
        )  # Add welcome_label to scroll_area_layout
        self.scroll_area_layout.addWidget(self.conversation_widget)

        self.user_input = AutoResizingTextEdit(self)
        self.user_input.setObjectName("user_input")
        self.user_input.setPlaceholderText("Ask me anything...")
        # self.user_input.setFixedHeight(10)
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_button = QPushButton("Send")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """
        )
        # self.submit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        buttons_widget = QWidget()
        # Assign the layout to a widget
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addWidget(self.submit_button)
        buttons_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Set the size policy on the widget

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.user_input)
        self.main_layout.addWidget(buttons_widget)
        self.setLayout(self.main_layout)

        self.submit_button.clicked.connect(self.submit_input)
        self.setWindowFlags(Qt.Window)

    def resizeEvent(self, event):
        self.scroll_area.updateGeometry()
        super().resizeEvent(event)

    def sizeHint(self):
        screen = QApplication.primaryScreen()  # Get the primary screen
        screen_size = screen.geometry()  # Get the screen geometry
        height = (
            screen_size.height() - 100
        )  # Set height to screen height minus a small margin
        return QSize(500, height)

    def load_stylesheet(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(
            current_dir,
            "..",
            "resources",
            "cyberpunk.qss")
        file = QFile(file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            self.setStyleSheet(stylesheet)
        else:
            logging.error(f"Failed to open {file_path}")

    def submit_input(self):
        try:
            user_input = self.user_input.toPlainText().strip()

            if not user_input:
                logging.warning("User input is empty. No action taken.")
                return
            self.welcome_label.hide()  # Hide the welcome label when user sends a message
            self.append_message(user_input, "user")  # Pass plain text now

            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )

            QApplication.processEvents()  # Process all pending events, including UI updates

            self.user_input.reset_size()

            self.user_input.clear()

            self.signal_user_message.emit(user_input)

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def append_bot_response(self, bot_response):
        try:
            self.temp_bot_message.update_text(
                bot_response)  # Pass plain text now
        except AttributeError as e:
            logging.error(f"Could not update message in UI due to error: {e}")

    def append_python_output(self, python_output, success, all_responses):
        if not python_output:
            return
        python_bot_message = self.append_message(
            """<div><b><span>🐍 Python Output</span></b></div><hr>""", "python_bot")
        python_bot_message.update_text(python_output)

        if not success:
            python_bot_message.update_text(
                "\n\nAttempting to fix the error...")
            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )
            self.signal_user_message.emit(f"{all_responses}\n {python_output}")

    def scroll_to_end(self):
        QTimer.singleShot(50, self._scroll_to_end)

    def _scroll_to_end(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def append_message(self, content, sender):
        message_bubble = MessageBubble(content, sender)
        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft
        self.conversation_layout.addWidget(message_bubble, alignment=alignment)
        self.conversation_layout.setAlignment(message_bubble, alignment)
        self.scroll_to_end()
        self.user_input.setFocus()
        return message_bubble

    def handle_visibility_changed(self, visible):
        if not visible:
            global active_chat_ui_instance
            active_chat_ui_instance = None

    def closeEvent(self, event):
        if self.chat_bot.full_message_history:  # Check if there's anything to save
            self.chat_bot.save_session_log()
        event.accept()  # Accept the close event
