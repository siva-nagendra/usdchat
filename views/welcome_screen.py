from PySide6.QtWidgets import QLabel, QPushButton, QSpacerItem, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt

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
