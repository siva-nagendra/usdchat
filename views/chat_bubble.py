import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ChatBubble(QWidget):
    def __init__(self, text, sender, success=True, parent=None):
        super().__init__(parent)
        self.sender = sender
        self.current_text = ""
        self.success = success
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
            if self.success:
                gradient.setColorAt(0, QColor("#336633"))  # Darker Green
                gradient.setColorAt(1, QColor("#226622"))  # Even Darker Green
            else:
                gradient.setColorAt(0, QColor("#993333"))  # Dark Red
                gradient.setColorAt(1, QColor("#994422"))  # Orange-ish Red
        else:
            raise ValueError(
                "Sender must be either 'user', 'bot', or 'python_bot'")

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
            raise ValueError(
                "Sender must be either 'user', 'bot', or 'python_bot'")

        return formatted_response

    def update_text(self, new_text):
        logger.info(f"updating text to {new_text}")
        self.current_text += new_text
        formatted_text = self.format_text(self.current_text)
        self.label.setText(formatted_text)
        self.label.adjustSize()
        self.adjustSize()
        logger.info(f"updated text to {formatted_text}")
