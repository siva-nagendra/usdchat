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
from PySide6.QtCore import Qt, QTimer, QFile, Slot, QUrl, QSize, QTextStream
from PySide6.QtGui import QLinearGradient, QFont, QPalette, QColor, QPainter, QBrush
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import QQmlApplicationEngine


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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_stylesheet()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.conversation_layout = QVBoxLayout(self.scroll_area_widget_contents)
        self.conversation_layout.addStretch()

        self.welcome_label = QLabel(
            '<html><head/><body><p align="center"><span style=" font-size:24pt;">'
            "Welcome to USD Chat ✨</span></p>"
            '<p align="center"><span style=" font-size:14pt;">Your AI-powered USD Chat assistant!</span></p>'
            "</body></html>",
            self.scroll_area,
        )
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("background:transparent;")
        self.welcome_label.adjustSize()  # Adjust the size of the label based on its content

        # Ensure the label is centered within the scroll area
        scroll_area_width = self.scroll_area.width()
        scroll_area_height = self.scroll_area.height()
        label_width = self.welcome_label.width()
        label_height = self.welcome_label.height()

        x_position = (scroll_area_width) / 2
        y_position = (scroll_area_height) / 0.1

        self.welcome_label.setGeometry(
            x_position, y_position, label_width, label_height
        )

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
        self.activateWindow()
        self.raise_()
        # self.expand_width(300)

    def resizeEvent(self, event):
        self.scroll_area.updateGeometry()
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(500, 800)

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

    def submit_input(self):
        user_text = self.user_input.toPlainText()
        if user_text:
            self.welcome_label.hide()  # Hide the welcome label when user sends a message
            formatted_text = user_text.replace("\n", "<br>")
            self.append_message(
                f'<div style="text-align: right;">🤷‍♂️ You<hr>style="text-align: right;"{formatted_text}</div>',
                "user",
            )
            self.user_input.clear()

            bot_response = self.get_bot_response(user_text)
            self.append_message(bot_response, "bot")

    def get_bot_response(self, user_text):
        formatted_text = user_text.replace("\n", "<br>")
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
        return formatted_response
    
    def scroll_to_end(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def append_message(self, content, sender, content_format="text"):
        message_bubble = MessageBubble(content, sender)
        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft

        self.conversation_layout.addWidget(message_bubble, alignment=alignment)
        self.conversation_layout.setAlignment(message_bubble, alignment)

        # Ensure the scroll area stays scrolled to the bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        self.scroll_to_end()

        # Ensure the user input field is focused after appending a message
        self.user_input.setFocus()

    def get_message_style(self, sender):
        common_style = """
            border-radius: 10px;
            padding: 10px;
            max-width: 60%;
            margin: 5px 0;
        """
        if sender == "user":
            return f"""
                {common_style}
                background-color: #3684ac;
                color: white;
            """
        else:  # sender == "bot"
            return f"""
                {common_style}
                background-color: #676767;
                color: white;
            """

    def get_dock_widget(self):
        if not hasattr(self, "_dock_widget"):
            self._dock_widget = QDockWidget("🤖 USDChat", self.parent())
            self._dock_widget.setWidget(self)
            self._dock_widget.visibilityChanged.connect(self.handle_visibility_changed)
        return self._dock_widget

    def handle_visibility_changed(self, visible):
        if not visible:
            global active_chat_ui_instance
            active_chat_ui_instance = None

    def sizeHint(self):
        return QSize(500, 800)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
