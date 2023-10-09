import logging
import os

from PySide6.QtCore import QFile, QSize, Qt, QTextStream, QTimer, Signal, QThread
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QTextEdit,
                               QVBoxLayout, QWidget, QSpacerItem)

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
        self.is_updating = False
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
        self.is_updating = True
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
        self.is_updating = False


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
                self.parent_widget.toggle_send_stop()
                self.reset_size()
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

    def __init__(self, usdviewApi, parent=None):
        super().__init__(parent)
        self.usdviewApi = usdviewApi
        self.message_bubbles = []
        self.setWindowTitle(Config.APP_NAME)
        self.language_model = Config.MODEL
        self.chat_bot = Chat(self.language_model)
        self.chat_bridge = ChatBridge(self.chat_bot, self, self.usdviewApi)
        self.chat_thread = chat_thread.ChatThread(
            self.chat_bot, self, "", self.usdviewApi)
        
        self.init_ui()
        self.init_welcome_screen()
        self.load_stylesheet()
        self.connectSignals()
        self.activateWindow()
        self.raise_()
        self.monitor_activity()

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
        # self.chat_bridge.signal_thread_finished.connect(self.enable_send_button)

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

        # Add welcome_label to scroll_area_layout
        self.scroll_area_layout.addWidget(self.conversation_widget)

        # add a button before the user input that says "clear chat"
        self.clear_chat_button = QPushButton("🧹 Clear")
        self.clear_chat_button.setObjectName("clear_chat_button")
        self.clear_chat_button.setMinimumHeight(40)

        self.clear_chat_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_chat_button.clicked.connect(self.clear_chat_ui)

        self.user_input = AutoResizingTextEdit(self)
        self.user_input.setObjectName("user_input")
        self.user_input.setPlaceholderText("Ask me anything...")
        # self.user_input.setFixedHeight(10)
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_button = QPushButton("⎆ Send")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(40)
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_widget = QWidget()
        # Assign the layout to a widget
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addWidget(self.clear_chat_button)
        # buttons_layout.addStretch(0.5)
        buttons_layout.addWidget(self.submit_button)
        buttons_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Set the size policy on the widget

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.user_input)
        self.main_layout.addWidget(buttons_widget)
        self.setLayout(self.main_layout)
        self.setWindowFlags(Qt.Window)


        # self.submit_button.clicked.connect(self.submit_input)
        self.submit_button.clicked.connect(self.toggle_send_stop)
        # self.chat_bridge.signal_thread_finished.connect(self.enable_send_button)
    
    def init_welcome_screen(self):
        self.welcome_widget = QWidget(self.scroll_area_widget_contents)
        self.welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_text = (
            '<html><head/><body>'
            '<p align="center" style=" font-size:28pt;">Welcome to USD Chat ✨</p>'
            '<p align="center" style=" font-size:18pt;">Your AI powered chat assistant!</p>'
            '</body></html>'
        )

        
        self.welcome_label = QLabel(welcome_text, self.scroll_area_widget_contents)
        self.welcome_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.welcome_label.setStyleSheet("background:transparent;")
        self.welcome_label.adjustSize()

        self.welcome_layout.addWidget(self.welcome_label)

        # Create buttons with emojis
        self.button1 = QPushButton("🔍 What's in my stage?")
        self.button2 = QPushButton("❓ Difference between Payloads and References?")
        self.button3 = QPushButton("📦 Create example USD scene with LIVERPS.")
        self.button4 = QPushButton("📊 Plot expensive prims.")

        # Add a vertical spacer
        vertical_spacer = QSpacerItem(20, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.welcome_layout.addItem(vertical_spacer)

        self.welcome_layout.addWidget(self.button1)
        self.welcome_layout.addWidget(self.button2)
        self.welcome_layout.addWidget(self.button3)
        self.welcome_layout.addWidget(self.button4)

        self.scroll_area_layout.addWidget(self.welcome_widget)

        # Set button height to 50
        self.button1.setFixedHeight(50)
        self.button2.setFixedHeight(50)
        self.button3.setFixedHeight(50)
        self.button4.setFixedHeight(50)

        # Connect buttons to slots
        self.button1.clicked.connect(lambda: self.send_button_text(self.button1))
        self.button2.clicked.connect(lambda: self.send_button_text(self.button2))
        self.button3.clicked.connect(lambda: self.send_button_text(self.button3))
        self.button4.clicked.connect(lambda: self.send_button_text(self.button4))

    def send_button_text(self, button):
        text = button.text()
        self.user_input.setPlainText(text)
        self.toggle_send_stop()
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
        self.message_bubbles = []
        self.conversation_layout.removeWidget(self.conversation_widget)
        self.conversation_widget.deleteLater()
        self.conversation_widget = QWidget(
            self.scroll_area_widget_contents
        )
        self.conversation_layout = QVBoxLayout(
            self.conversation_widget
        )
        self.conversation_layout.addStretch()
        self.scroll_area_layout.addWidget(self.conversation_widget)
        self.welcome_widget.show()
        self.user_input.reset_size()
        self.user_input.clear()
        self.submit_button.setText("⎆ Send")
        self.submit_button.clicked.disconnect()
        self.submit_button.clicked.connect(self.toggle_send_stop)

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
            self.welcome_widget.hide()
            self.append_message(user_input, "user")  # Pass plain text now
            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )
            self.monitor_activity()
            QApplication.processEvents()  # Process all pending events, including UI updates

            self.user_input.reset_size()

            self.user_input.clear()

            self.signal_user_message.emit(user_input)
            
            self.toggle_send_stop()


        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def append_bot_response(self, bot_response):
        try:
            self.temp_bot_message.is_updating = True  # Indicate that the message is being updated
            self.temp_bot_message.update_text(bot_response)
            self.temp_bot_message.is_updating = False  # Done updating
            self.scroll_to_end()
            self.check_message_bubbles()  # Check the state of all message bubbles
        except AttributeError as e:
            logging.error(f"Could not update message in UI due to error: {e}")

    def append_python_output(self, python_output, success, all_responses):
        if not python_output:
            return
        python_bot_message = self.append_message(
            """<div><b><span>🐍 Python Output</span></b></div><hr>""", "python_bot")
        python_bot_message.is_updating = True  # Indicate that the message is being updated
        python_bot_message.update_text(python_output)
        python_bot_message.is_updating = False  # Done updating
        self.scroll_to_end()
        self.check_message_bubbles()  # Check the state of all message bubbles

        if not success:
            python_bot_message.is_updating = True  # Indicate that the message is being updated
            python_bot_message.update_text("\n\nAttempting to fix the error...")
            python_bot_message.is_updating = False  # Done updating
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
        self.message_bubbles.append(message_bubble)  # Append the new MessageBubble to the list
        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft
        self.conversation_layout.addWidget(message_bubble, alignment=alignment)
        self.conversation_layout.setAlignment(message_bubble, alignment)
        self.scroll_to_end()
        self.user_input.setFocus()
        return message_bubble
    
    def check_message_bubbles(self):
        any_updating = False
        for bubble in self.message_bubbles:
            if bubble.is_updating:
                any_updating = True
                break
        if any_updating:
            self.enable_stop_button()
        else:
            self.enable_send_button()
        
    def monitor_activity(self):
        self.check_message_bubbles()  # Check the state of all message bubbles
        QTimer.singleShot(100, self.monitor_activity)  # Call itself again

    def enable_send_button(self):
        # check if there are any active threads
        # QTimer.singleShot(50, self.chat_bridge.clean_up_thread)
        if not self.chat_bridge.active_thread_count:
            self.submit_button.setText("⎆ Send")
            self.submit_button.setProperty("stopMode", False)  # Add this line
            self.submit_button.setStyle(self.submit_button.style())
            self.submit_button.setEnabled(True)
            self.user_input.setEnabled(True)
    
    def enable_stop_button(self):
        self.submit_button.setText("✋ Stop")
        self.submit_button.setProperty("stopMode", True)  # Add this line
        self.submit_button.setStyle(self.submit_button.style())
        self.submit_button.setEnabled(True)
        self.user_input.setEnabled(False)
    
    def toggle_send_stop(self):
        if self.submit_button.text() == "⎆ Send":
            user_text = self.user_input.toPlainText().strip()
            if not user_text:
                logging.warning("User input is empty. No action taken.")
                return
            self.submit_input()
            self.enable_stop_button()
            self.check_message_bubbles()  # Check if any message bubble is updating
        else:
            self.stop_chat_thread()
            self.check_message_bubbles()  # Check if any message bubble is updating
    
    def check_message_bubbles(self):
        any_updating = False
        for i in range(self.conversation_layout.count()):
            widget = self.conversation_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'is_updating') and widget.is_updating:
                any_updating = True
                break  # No need to check further if we find at least one updating widget
        
        logging.debug(f"Any updating: {any_updating}")  # Debug line
        
        if any_updating:
            self.enable_stop_button()
        else:
            self.enable_send_button()
