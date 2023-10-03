import os
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
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from .text_message import TextMessageWidget


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
        self.submit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.audio_toggle_button = QPushButton("Audio Off", self)
        self.audio_toggle_button.setObjectName("audio_toggle_button")
        self.audio_toggle_button.setCheckable(True)
        self.audio_toggle_button.setChecked(False)
        self.audio_toggle_button.clicked.connect(self.toggle_audio)

        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)  # Assign the layout to a widget
        buttons_layout.addWidget(self.audio_toggle_button)
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
        self.raise_()
        self.expand_width(300)

    def resizeEvent(self, event):
        self.scroll_area.updateGeometry()
        super().resizeEvent(event)

    def load_stylesheet(self):
        stylesheet = """
            /* Global Styles */
            QWidget {
                font-family: "Arial", sans-serif;
                font-size: 14px;
            }

            /* User Input Styles */
            QTextEdit#user_input {
                background-color: #444;
                color: #fff;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 10px;  /* Added rounded rectangle effect */
            }

            /* Submit Button Styles */
            QPushButton#submit_button {
                background-color: #3684ac;
                color: #fff;
                border: none;
                padding: 5px 10px;
            }

            QPushButton#submit_button:pressed {
                background-color: #3596bd;
            }

            QPushButton#submit_button:hover {
                background-color: #2f7a9a;
            }

            /* Audio Toggle Button Styles */
            QPushButton#audio_toggle_button[checked="true"] {
                background-color: #2f7b2f;
                color: #fff;
                border: none;
                padding: 5px 10px;
            }

            QPushButton#audio_toggle_button[checked="false"] {
                background-color: #676767;
                color: #fff;
                border: none;
                padding: 5px 10px;
            }

            QPushButton#audio_toggle_button:hover {
                background-color: #5e5e5e;
            }

            /* Word Count Label Styles */
            QLabel#word_count_label {
                color: #aaa;
            }

            /* Message Styles */
            QLabel#user_message, QLabel#bot_message {
                border-radius: 10px;
                padding: 10px;
                max-width: 60%;
                border: 1px solid transparent;
            }

            QLabel#user_message {
                background-color: #3684ac;
                color: white;
            }

            QLabel#bot_message {
                background-color: #676767;
                color: white;
            }
        """
        self.setStyleSheet(stylesheet)

    def toggle_audio(self):
        if self.audio_toggle_button.isChecked():
            self.audio_toggle_button.setText("Audio On")
        else:
            self.audio_toggle_button.setText("Audio Off")

    def submit_input(self):
        user_text = self.user_input.toPlainText()
        if user_text:
            self.welcome_label.hide()  # Hide the welcome label when user sends a message
            formatted_text = user_text.replace("\n", "<br>")
            self.append_message(f"🤷‍♂️ You: <br>{formatted_text}", "user")
            self.user_input.clear()

            bot_response = self.get_bot_response(user_text)
            self.append_message(bot_response, "bot")

    def get_bot_response(self, user_text):
        formatted_text = user_text.replace("\n", "<br>")
        formatted_response = (
            f"<div style='color: grey;'>USDChat: 🤖</div>"
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

    def append_message(self, content, sender, content_format="text"):
        text_widget = TextMessageWidget(content, content_format)
        text_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Allow horizontal expansion

        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft

        message_widget = QWidget()
        message_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Allow horizontal expansion

        message_layout = QHBoxLayout(message_widget)

        if sender == "user":
            message_layout.addWidget(QWidget(), 1)  # Spacer
        message_layout.addWidget(text_widget)
        if sender == "bot":
            message_layout.addWidget(QWidget(), 1)  # Spacer

        self.conversation_layout.addWidget(message_widget, alignment=alignment)
        self.conversation_layout.setAlignment(message_widget, alignment)

        # Ensure the scroll area stays scrolled to the bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        self.scroll_to_end()

    def scroll_to_end(self):
        # Use a single-shot QTimer to delay the scrolling operation.
        QTimer.singleShot(
            0,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )

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

    def get_bot_response(self, user_text):
        formatted_response = (
            f"<div style='color: grey;'>USDChat: 🤖</div>"
            f"<div style='"
            f"border: 2px solid #444;"  # Border styling with darker color for visibility
            f"padding: 10px;"  # Padding inside the border
            f"margin: 5px 0;"  # Margin outside the border
            f"border-radius: 10px;"  # Rounded corners
            f"background-color: transparent;"  # No background color (transparent)
            f"'>"
            f"{user_text}"
            f"</div>"
        )
        return formatted_response

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

    def expand_width(self, value):
        current_width = self.width()
        new_width = current_width + value
        self.setFixedWidth(new_width)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
