import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QProgressBar, QPushButton, QSpacerItem,
                               QVBoxLayout, QWidget)


def init_welcome_screen(self):
    self.usd_dependencies = 0
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

    self.vertical_spacer1 = QSpacerItem(20, 150)
    self.vertical_spacer2 = QSpacerItem(20, 150)
    self.vertical_spacer3 = QSpacerItem(20, 150)

    if self.standalone:
        rag_frame = QFrame(self.welcome_widget)
        rag_layout = QVBoxLayout(rag_frame)
        rag_layout.setContentsMargins(0, 0, 0, 0)
        rag_label = QLabel("Load stage for RAG", rag_frame)
        rag_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")
        rag_layout.addWidget(rag_label)
        self.working_dir_line_edit = QLineEdit(self.config.WORKING_DIRECTORY)
        self.working_dir_line_edit.setFixedHeight(30)
        self.browse_button = QPushButton("📂")
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Pick USD Stage"))
        dir_layout.addWidget(self.working_dir_line_edit)
        dir_layout.addWidget(self.browse_button)
        self.browse_button.setObjectName("browse_button")
        self.working_dir_line_edit.setObjectName("working_dir_line_edit")
        self.embed_stage_button = QPushButton("⌗ Embed Stage")
        self.embed_stage_button.setFixedHeight(30)
        self.embed_stage_button.clicked.connect(self.embed_stage)
        self.embed_stage_button.setObjectName("embed_stage_button")
        self.progress_label = QLabel("", self.welcome_widget)
        self.progress_bar = QProgressBar(self.welcome_widget)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        rag_layout.addLayout(dir_layout)
        rag_layout.addWidget(self.embed_stage_button)
        rag_layout.addWidget(self.progress_label)
        rag_layout.addWidget(self.progress_bar)

        self.welcome_layout.addItem(self.vertical_spacer3)
        self.welcome_layout.addWidget(rag_frame)
        self.browse_button.clicked.connect(self.browse_directory)

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
