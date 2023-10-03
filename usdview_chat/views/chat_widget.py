import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
    QDockWidget, QScrollArea, QLabel, QSizePolicy, 
)
from PySide6 import QtGui
from PySide6.QtCore import Qt, QTimer


class ChatBotUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_stylesheet()

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.conversation_layout = QVBoxLayout(self.scroll_area_widget_contents)
        self.conversation_layout.addStretch()  # This line adds a stretch at the beginning

        self.user_input = QTextEdit()
        self.user_input.setObjectName('user_input')
        self.user_input.setFixedHeight(200)

        self.submit_button = QPushButton("Send")
        self.submit_button.setObjectName('submit_button')

        self.audio_toggle_button = QPushButton("Audio On", self)
        self.audio_toggle_button.setObjectName('audio_toggle_button')
        self.audio_toggle_button.setCheckable(True)
        self.audio_toggle_button.setChecked(False)
        self.audio_toggle_button.clicked.connect(self.toggle_audio)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.audio_toggle_button)
        buttons_layout.addWidget(self.submit_button)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.user_input)
        self.main_layout.addLayout(buttons_layout)
        self.setLayout(self.main_layout)

        self.submit_button.clicked.connect(self.submit_input)
        self.setWindowFlags(Qt.Window)
        self.raise_()
        self.append_message("🪄 Welcome to USDChat bot! ✨", "bot_message")
        self.expand_width(300)


    def load_stylesheet(self):
        current_file_path = os.path.abspath(__file__)
        current_dir_path = os.path.dirname(current_file_path)
        stylesheet_path = os.path.join(current_dir_path, 'stylesheet.qss')

        with open(stylesheet_path, 'r') as file:
            stylesheet = file.read()
        self.setStyleSheet(stylesheet)

    def toggle_audio(self):
        if self.audio_toggle_button.isChecked():
            self.audio_toggle_button.setText("Audio On")
        else:
            self.audio_toggle_button.setText("Audio Off")

    def submit_input(self):
        user_text = self.user_input.toPlainText()
        if user_text:
            self.append_message(f"You: {user_text}", "user")
            self.user_input.clear()

            bot_response = self.get_bot_response(user_text)
            self.append_message(bot_response, "bot")

    def append_message(self, text, sender):
        message_label = QLabel()
        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft
        message_widget = QWidget()
        message_layout = QHBoxLayout(message_widget)

        message_label.setText(f"<div style='{self.get_message_style(sender)}'>{text}</div>")
        message_label.setWordWrap(True)  # Ensure word wrapping is enabled
        message_label.setMaximumWidth(250)

        if sender == "user":
            message_layout.addWidget(QWidget(), 1)  # Spacer
        message_layout.addWidget(message_label)
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
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

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
        return f"You said: {user_text}"

    def get_dock_widget(self):
        if not hasattr(self, '_dock_widget'):
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
