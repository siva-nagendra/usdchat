from pxr.Usdviewq.qt import QtWidgets, QtCore

class ChatBotUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up UI elements
        self.conversation_box = QtWidgets.QTextEdit()
        self.conversation_box.setReadOnly(True)
        self.user_input = QtWidgets.QTextEdit()
        self.user_input.setFixedHeight(50)  # Set initial height to accommodate 2 lines
        self.user_input.textChanged.connect(self.update_word_count)
        self.submit_button = QtWidgets.QPushButton("Send")
        self.submit_button.setFixedSize(50, 20)  # Adjust the size of the button
        self.word_count_label = QtWidgets.QLabel("Word count: 0")
        self.word_count_label.setAlignment(QtCore.Qt.AlignRight)

        # Set up layout
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.submit_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.conversation_box)
        layout.addLayout(input_layout)
        layout.addWidget(self.word_count_label, alignment=QtCore.Qt.AlignRight)
        self.setLayout(layout)

        # Connect signals and slots
        self.submit_button.clicked.connect(self.submit_input)

        # Set window flags and raise the widget
        self.setWindowFlags(QtCore.Qt.Window)
        self.raise_()

        # Set a minimum height for the widget
        self.setMinimumHeight(750)  # Set the minimum height to 500 pixels or whatever value you prefer
        self.conversation_box.setMinimumHeight(500)  # Adjust the height of the text box

    def submit_input(self):
        user_text = self.user_input.toPlainText()
        if user_text:
            self.conversation_box.append(f"You: {user_text}")
            self.user_input.clear()

            bot_response = self.get_bot_response(user_text)
            self.conversation_box.append(f"Bot: {bot_response}")

    def get_bot_response(self, user_text):
        # This is where you would put your chatbot's response logic.
        # For now, we'll just echo back the user's message.
        return f"You said: {user_text}"

    def update_word_count(self):
        user_text = self.user_input.toPlainText()
        word_count = len(user_text.split())
        self.word_count_label.setText(f"Word count: {word_count}")
    
    def get_dock_widget(self, parent=None):
        dock_widget = QtWidgets.QDockWidget("USD Chat", parent)
        dock_widget.setWidget(self)
        return dock_widget

