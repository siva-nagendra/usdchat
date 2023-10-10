import logging
import os

from PySide6.QtCore import QFile, QSize, Qt, QTextStream, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
)

from USDChat.chat_bot import Chat
from USDChat.chat_bridge import ChatBridge
from USDChat.config import Config
from USDChat.utils import chat_thread
from USDChat.utils.conversation_manager import ConversationManager
from USDChat.utils import process_code

logging.basicConfig(level=logging.WARNING)


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
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.label.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(self.rect().topLeft(), self.rect().bottomLeft())
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
            raise ValueError("Sender must be either 'user', 'bot', or 'python_bot'")

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 5, 5)

    def resizeEvent(self, event):
        self.layout.invalidate()
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
                f"border: 2px solid #444;"
                f"padding: 10px;"
                f"margin: 5px 0;"
                f"border-radius: 10px;"
                f"background-color: transparent;"
                f"'>"
                f"{formatted_text}"
                f"</div>"
            )
        elif self.sender == "python_bot":
            formatted_response = (
                f"<div style='"
                f"border: 2px solid #444;"
                f"padding: 10px;"
                f"margin: 5px 0;"
                f"border-radius: 10px;"
                f"background-color: transparent;"
                f"'>"
                f"{formatted_text}"
                f"</div>"
            )
        else:
            raise ValueError("Sender must be either 'user', 'bot', or 'python_bot'")

        return formatted_response

    def update_text(self, new_text):
        logging.info(f"updating text to {new_text}")
        self.current_text += new_text
        formatted_text = self.format_text(self.current_text)
        self.label.setText(formatted_text)
        self.label.adjustSize()
        self.adjustSize()
        logging.info(f"updated text to {formatted_text}")


class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setFixedHeight(self.fontMetrics().lineSpacing() + 20)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.modifiers() & Qt.ShiftModifier and event.key() == Qt.Key_Return:
            new_height = self.height() + 20
            max_height = self.fontMetrics().lineSpacing() * 15 + 10
            new_height = min(new_height, max_height)
            self.setFixedHeight(new_height)
        elif event.key() == Qt.Key_Return:
            if self.parent_widget:
                self.reset_size()
                self.parent_widget.submit_input()
        else:
            doc_height = self.document().size().height()
            max_height = self.fontMetrics().lineSpacing() * 15 + 10
            new_height = min(doc_height + 10, max_height)
            self.setFixedHeight(new_height)

    def reset_size(self):
        default_height = self.fontMetrics().lineSpacing() + 20
        self.setFixedHeight(default_height)


class ChatBotUI(QWidget):
    signal_user_message = Signal(str)
    signal_error_message = Signal(str)
    signal_python_execution_response = Signal(str, bool)

    def __init__(self, usdviewApi, parent=None):
        super().__init__(parent)
        self.usdviewApi = usdviewApi
        self.setWindowTitle(Config.APP_NAME)
        self.language_model = Config.MODEL
        self.chat_bot = Chat(self.language_model)
        self.chat_bridge = ChatBridge(self.chat_bot, self, self.usdviewApi)
        self.chat_thread = chat_thread.ChatThread(
            self.chat_bot, self, "", self.usdviewApi
        )
        self.conversation_manager = ConversationManager()

        self.init_ui()
        self.init_welcome_screen()
        self.conversation_manager.new_session()
        self.load_stylesheet()
        self.connectSignals()
        self.activateWindow()
        self.raise_()

        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        width, height = (
            670,
            screen_size.height() - 100,
        )
        self.setMaximumWidth(width)
        self.resize(width, height)

    def connectSignals(self):
        self.signal_user_message.connect(self.chat_bridge.get_bot_response)
        self.chat_bridge.signal_bot_response.connect(self.append_bot_response)
        self.chat_bridge.signal_python_code_ready.connect(
            self.run_python_code_in_main_thread
        )

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget_contents)

        self.conversation_widget = QWidget(self.scroll_area_widget_contents)
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.addStretch()

        self.scroll_area_layout.addWidget(self.conversation_widget)

        self.user_input = AutoResizingTextEdit(self)
        self.user_input.setObjectName("user_input")
        self.user_input.setPlaceholderText("Ask me anything...")
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.clear_chat_button = QPushButton("🧹 Clear")
        self.clear_chat_button.setObjectName("clear_chat_button")
        self.clear_chat_button.setMinimumHeight(40)

        self.clear_chat_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_chat_button.clicked.connect(self.clear_chat_ui)

        self.stop_response_button = QPushButton("✋ Stop")
        self.stop_response_button.setObjectName("clear_chat_button")
        self.stop_response_button.setMinimumHeight(40)

        self.stop_response_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.stop_response_button.clicked.connect(self.stop_chat_thread)

        self.submit_button = QPushButton("⎆ Send")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(40)
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addWidget(self.clear_chat_button)
        buttons_layout.addWidget(self.stop_response_button)
        buttons_layout.addWidget(self.submit_button)
        buttons_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_button.clicked.connect(self.submit_input)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.user_input)
        self.main_layout.addWidget(buttons_widget)
        self.setLayout(self.main_layout)
        self.setWindowFlags(Qt.Window)

    def init_welcome_screen(self):
        self.welcome_widget = QWidget(self.scroll_area_widget_contents)
        self.welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_text = (
            "<html><head/><body>"
            '<p align="center" style=" font-size:28pt;">Welcome to USD Chat ✨</p>'
            '<p align="center" style=" font-size:18pt;">Your AI powered chat assistant!</p>'
            "</body></html>"
        )

        self.welcome_label = QLabel(welcome_text, self.scroll_area_widget_contents)
        self.welcome_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.welcome_label.setStyleSheet("background:transparent;")
        self.welcome_label.adjustSize()

        self.welcome_layout.addWidget(self.welcome_label)

        self.button1 = QPushButton("🔍 What's in my stage?")
        self.button2 = QPushButton("❓ Difference between Payloads and References?")
        self.button3 = QPushButton("📦 Create example USD scene with LIVERPS.")
        self.button4 = QPushButton("📊 Plot 10 expensive prims from the current stage")

        vertical_spacer = QSpacerItem(
            20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self.welcome_layout.addItem(vertical_spacer)

        self.welcome_layout.addWidget(self.button1)
        self.welcome_layout.addWidget(self.button2)
        self.welcome_layout.addWidget(self.button3)
        self.welcome_layout.addWidget(self.button4)

        self.scroll_area_layout.addWidget(self.welcome_widget)

        self.button1.setFixedHeight(50)
        self.button2.setFixedHeight(50)
        self.button3.setFixedHeight(50)
        self.button4.setFixedHeight(50)

        self.button1.clicked.connect(lambda: self.send_button_text(self.button1))
        self.button2.clicked.connect(lambda: self.send_button_text(self.button2))
        self.button3.clicked.connect(lambda: self.send_button_text(self.button3))
        self.button4.clicked.connect(lambda: self.send_button_text(self.button4))

    def send_button_text(self, button):
        text = button.text()
        self.user_input.setPlainText(text)
        self.submit_input()
        self.hide_welcome_screen()

    def hide_welcome_screen(self):
        for i in reversed(range(self.welcome_layout.count())):
            widget = self.welcome_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.welcome_layout.deleteLater()

    def stop_chat_thread(self):
        self.chat_bridge.clean_up_thread()

    def clear_chat_ui(self):
        self.conversation_layout.removeWidget(self.conversation_widget)
        self.conversation_widget.deleteLater()
        self.conversation_widget = QWidget(self.scroll_area_widget_contents)
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.addStretch()
        self.scroll_area_layout.addWidget(self.conversation_widget)
        self.user_input.reset_size()
        self.user_input.clear()

        self.init_welcome_screen()
        self.conversation_manager.new_session()

    def resizeEvent(self, event):
        self.scroll_area.updateGeometry()
        super().resizeEvent(event)

    def sizeHint(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        height = screen_size.height() - 100
        return QSize(500, height)

    def load_stylesheet(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "..", "resources", "stylesheet.qss")
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
            self.welcome_widget.setVisible(False)
            self.append_message(user_input, "user")
            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )

            QApplication.processEvents()

            self.user_input.reset_size()

            self.user_input.clear()

            self.signal_user_message.emit(user_input)

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def append_bot_response(self, bot_response):
        try:
            self.temp_bot_message.update_text(bot_response)
            self.scroll_to_end()
        except AttributeError as e:
            logging.error(f"Could not update message in UI due to error: {e}")

    def append_python_output(self, python_output, success, all_responses):
        print(
            f"python_output: {python_output}, success: {success}, all_responses: {all_responses}"
        )
        if not python_output:
            return
        python_bot_message = self.append_message(
            """<div><b><span>🐍 Python Output</span></b></div><hr>""", "python_bot"
        )
        python_bot_message.update_text(python_output)
        self.scroll_to_end()

        if not success:
            python_bot_message.update_text("\n\nAttempting to fix the error...")
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

    def run_python_code_in_main_thread(self, code_to_run):
        # Extract and run the Python code here.
        python_code_snippets = process_code.extract_python_code(code_to_run)
        for snippet in python_code_snippets:
            output, success = process_code.execute_python_code(snippet, self.usdviewApi)
            self.signal_python_execution_response.emit(output, success)
            self.append_python_output(output, success, code_to_run)
