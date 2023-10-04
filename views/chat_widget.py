import os
import sys
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QDockWidget,
    QScrollArea,
    QLabel,
    QSizePolicy,
    QApplication,
    QMainWindow,
)
from PySide6.QtCore import Qt, QTimer, QFile, Slot, QUrl, QSize, QTextStream, Signal
from PySide6.QtGui import QLinearGradient, QFont, QPalette, QColor, QPainter, QBrush, QTextOption
from USDChat.chat_bridge import ChatBridge
from USDChat.chat_bot import Chat
from USDChat.utils.utils import get_model

class MessageBubble(QWidget):
    def __init__(self, text, sender, parent=None):
        super().__init__(parent)
        self.text = text
        self.sender = sender
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.label = QLabel(self.text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(10, 10, 10, 10)  # Padding for the text
        self.setLayout(self.layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(self.rect().topLeft(), self.rect().bottomLeft())
        if self.sender == "user":
            gradient.setColorAt(0, QColor("#993366"))  # Darker Pink
            gradient.setColorAt(1, QColor("#663366"))  # Darker Purple
        else:
            gradient.setColorAt(0, QColor("#336699"))  # Darker Cyan
            gradient.setColorAt(1, QColor("#336666"))  # Darker Teal

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)  # No border outline
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 5, 5)


class ChatBotUI(QWidget):
    signal_user_message = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)

        self.language_model = get_model()
        self.chat_bot = Chat(self.language_model)
        self.chat_bridge = ChatBridge(self.chat_bot, self)

        self.init_ui()
        self.load_stylesheet()
        self.connectSignals()
        self.activateWindow()
        self.raise_()

    def connectSignals(self):
        # self.signal_user_message.connect(self.chat_bridge.get_bot_response)
        self.chat_bridge.signal_bot_response.connect(self.update_chat_ui)
    
    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget_contents)  # New layout for scroll_area_widget_contents

        self.conversation_widget = QWidget(self.scroll_area_widget_contents)  # New widget for conversation
        self.conversation_layout = QVBoxLayout(self.conversation_widget)  # Set conversation_layout to conversation_widget
        self.conversation_layout.addStretch()

        self.welcome_label = QLabel(
            '<html><head/><body><p align="center"><span style=" font-size:24pt;">'
            "Welcome to USD Chat ✨</span></p>"
            '<p align="center"><span style=" font-size:14pt;">Your AI-powered USD Chat assistant!</span></p>'
            "</body></html>",
            self.scroll_area_widget_contents,
        )
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("background:transparent;")
        self.welcome_label.adjustSize()  # Adjust the size of the label based on its content

        self.scroll_area_layout.addWidget(self.welcome_label)  # Add welcome_label to scroll_area_layout
        self.scroll_area_layout.addWidget(self.conversation_widget) 

        self.user_input = QTextEdit()
        self.user_input.setObjectName("user_input")
        self.user_input.setPlaceholderText("Ask me anything...")
        self.user_input.setFixedHeight(100)
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_button = QPushButton("Send")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setStyleSheet("""
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
        """)
        # self.submit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)  # Assign the layout to a widget
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

    def get_file_from_current_path(self, filename):
        current_file_path = os.path.abspath(__file__)
        current_dir_path = os.path.dirname(current_file_path)

        req_file = os.path.join(current_dir_path, filename)
        return req_file

    def load_stylesheet(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, '..', 'resources', 'cyberpunk.qss')
        file = QFile(file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            self.setStyleSheet(stylesheet)
        else:
            print(f"Failed to open {file_path}")

    def format_message(self, message, sender):
        formatted_text = f'<pre style="white-space: pre-wrap; word-wrap: break-word;">{message}</pre>'
        
        if sender == "user":
            formatted_response = (
                f'<div style="text-align: right;">'
                f'🤷‍♂️ You'
                f'<hr>'
                f'<div style="text-align: left;">'
                f'{formatted_text}'
                f'</div>'
                f'</div>'
            )
        elif sender == "bot":
            formatted_response = (
                f"<div>🤖 USDChat</div>"
                f"<hr>"
                f"<div style='"
                f"border: 2px solid #444;"  # Border styling with darker color for visibility
                f"padding: 10px;"  # Padding inside the border
                f"margin: 5px 0;"  # Margin outside the border
                f"border-radius: 10px;"  # Rounded corners
                f"background-color: transparent;"  # No background color (transparent)
                f"'>"
                f"{formatted_text}"
                f"</div>"
            )
        else:
            raise ValueError("Sender must be either 'user' or 'bot'")
        
        return formatted_response

    def submit_input(self):
        try:
            user_input = self.get_user_input()
            
            if not user_input:
                print("User input is empty. No action taken.")
                return

            self.welcome_label.hide()  # Hide the welcome label when user sends a message

            user_message = self.format_message(user_input, "user")
            
            self.append_message(user_message, "user")
            
            self.user_input.clear()
            
            self.get_bot_response(user_input)
                
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def get_user_input(self):
       return self.user_input.toPlainText()
    
    def get_bot_response(self, user_input):
        try:
            generated_text = self.chat_bridge.get_bot_response(user_input)
            return generated_text
        except AttributeError:
            print("Chat bridge not initialized.")
            return None

    def update_chat_ui(self, bot_response):
        try:
            bot_message = self.format_message(bot_response, "bot")
            self.append_message(bot_message, "bot")
        except AttributeError:
            print("Could not append message to UI.")

    def scroll_to_end(self):
        QTimer.singleShot(0, self._scroll_to_end)

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

    def handle_visibility_changed(self, visible):
        if not visible:
            global active_chat_ui_instance
            active_chat_ui_instance = None

    def sizeHint(self):
        return QSize(500, 800)
