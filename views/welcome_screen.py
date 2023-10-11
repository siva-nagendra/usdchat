import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QSpacerItem,
                               QVBoxLayout, QWidget)


def init_welcome_screen(self):
    self.welcome_widget = QWidget(self.scroll_area_widget_contents)
    self.welcome_layout = QVBoxLayout(self.welcome_widget)
    welcome_text = (
        "<html><head/><body>"
        '<p align="center" style=" font-size:28pt;">USD Chat ✨</p>'
        "</body></html>"
    )

    self.welcome_label = QLabel(welcome_text, self.scroll_area_widget_contents)
    self.welcome_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
    self.welcome_label.setStyleSheet("background:transparent;")
    self.welcome_label.adjustSize()

    self.welcome_layout.addWidget(self.welcome_label)

    example_prompts = self.config.EXAMPLE_PROMPTS

    selected_prompts = random.sample(example_prompts, 4)

    button_frame = QFrame(self.welcome_widget)

    frame_layout = QVBoxLayout(button_frame)
    frame_layout.setContentsMargins(0, 0, 0, 0)
    frame_label = QLabel("Try it yourself", button_frame)
    frame_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")
    frame_layout.addWidget(frame_label)

    self.button1 = QPushButton(selected_prompts[0])
    self.button2 = QPushButton(selected_prompts[1])
    self.button3 = QPushButton(selected_prompts[2])
    self.button4 = QPushButton(selected_prompts[3])

    frame_layout.addWidget(self.button1)
    frame_layout.addWidget(self.button2)
    frame_layout.addWidget(self.button3)
    frame_layout.addWidget(self.button4)

    self.vertical_spacer1 = QSpacerItem(20, 200)
    self.vertical_spacer2 = QSpacerItem(20, 200)

    self.welcome_layout.addItem(self.vertical_spacer1)
    self.welcome_layout.addWidget(button_frame)
    self.welcome_layout.addItem(self.vertical_spacer2)
    self.welcome_layout.setContentsMargins(0, 0, 0, 0)

    self.scroll_area_layout.addWidget(self.welcome_widget)

    self.button1.setFixedHeight(40)
    self.button2.setFixedHeight(40)
    self.button3.setFixedHeight(40)
    self.button4.setFixedHeight(40)

    self.button1.clicked.connect(lambda: self.send_button_text(self.button1))
    self.button2.clicked.connect(lambda: self.send_button_text(self.button2))
    self.button3.clicked.connect(lambda: self.send_button_text(self.button3))
    self.button4.clicked.connect(lambda: self.send_button_text(self.button4))
