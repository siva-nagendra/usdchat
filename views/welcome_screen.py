import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QProgressBar, QPushButton,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from usdchat.views.mode_switcher import ModeSwitcher


def init_welcome_screen(self):
    self.mode_switcher = ModeSwitcher(rag_mode=self.rag_mode)
    self.mode_switcher.signalRagModeChanged.connect(self.handleRagModeChange)
    self.welcome_widget = QWidget(self.scroll_area_widget_contents)
    self.welcome_layout = QVBoxLayout(self.welcome_widget)
    welcome_text = (
        "<html><head/><body>"
        '<p align="center" style=" font-size:28pt; font-weight: bold;">USD Chat ✨</p>'
        "</body></html>")

    self.welcome_label = QLabel(welcome_text, self.scroll_area_widget_contents)
    self.welcome_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
    self.welcome_label.setStyleSheet("background:transparent;")
    self.welcome_label.adjustSize()

    self.welcome_layout.addWidget(self.welcome_label)

    self.vertical_spacer1 = QSpacerItem(20, 200)
    self.vertical_spacer2 = QSpacerItem(20, 80)
    self.vertical_spacer3 = QSpacerItem(20, 100)
    self.vertical_spacer4 = QSpacerItem(20, 50)

    self.welcome_layout.addItem(self.vertical_spacer4)
    self.welcome_layout.addWidget(self.mode_switcher)
    if self.rag_mode:
        self.mode_switcher.button_rag.setChecked(True)

        rag_frame = QFrame(self.welcome_widget)
        rag_frame.setObjectName("rag_frame")

        rag_layout = QVBoxLayout(rag_frame)
        rag_layout.setContentsMargins(0, 0, 0, 0)

        rag_label = QLabel("Load stage for RAG", rag_frame)
        rag_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")

        rag_layout.addWidget(rag_label)

        self.working_dir_line_edit = QLineEdit()
        self.working_dir_line_edit.setPlaceholderText("Pick a valid USD File")
        self.working_dir_line_edit.setFixedHeight(30)
        self.working_dir_line_edit.setObjectName("working_dir_line_edit")

        self.browse_button = QPushButton("📂")
        self.browse_button.setObjectName("browse_button")

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("USD Stage"))
        dir_layout.addWidget(self.working_dir_line_edit)
        dir_layout.addWidget(self.browse_button)

        self.collection_name_label = QLabel("")
        self.collection_name_label.setVisible(False)

        self.embed_stage_button = QPushButton("💿 Create Collection")
        self.embed_stage_button.setFixedHeight(30)
        self.embed_stage_button.setObjectName("embed_stage_button")
        self.embed_stage_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.embed_stage_button.setDisabled(True)

        create_collection_layout = QHBoxLayout()
        create_collection_layout.addWidget(self.collection_name_label)
        create_collection_layout.addWidget(self.embed_stage_button)

        self.progress_label = QLabel("", self.welcome_widget)
        self.progress_label.setVisible(False)

        self.progress_bar = QProgressBar(self.welcome_widget)
        self.progress_bar.setVisible(False)

        # Create combo box
        self.collection_combo_box = QComboBox(rag_frame)
        self.collection_combo_box.setObjectName("collection_combo_box")
        self.collection_combo_box_label = QLabel(
            "Choose Collection to chat with", rag_frame
        )
        self.collection_combo_box_label.setStyleSheet(
            "color: #AAAAAA; font-weight: bold;"
        )

        self.collection_combo_box.addItems(
            self.chat_bridge.chromadb_collections.all_collections()
        )

        all_collection_layout = QHBoxLayout()
        all_collection_layout.addWidget(self.collection_combo_box_label)
        all_collection_layout.addWidget(self.collection_combo_box)

        rag_layout.addLayout(dir_layout)
        rag_layout.addLayout(create_collection_layout)

        rag_layout.addWidget(self.progress_label)
        rag_layout.addWidget(self.progress_bar)
        rag_layout.addLayout(all_collection_layout)
        rag_layout.setContentsMargins(0, 0, 0, 0)

        self.welcome_layout.addItem(self.vertical_spacer3)
        self.welcome_layout.addWidget(rag_frame)

        self.browse_button.clicked.connect(self.browse_directory)
        self.working_dir_line_edit.textChanged.connect(
            self.check_if_embed_ready)
        self.embed_stage_button.clicked.connect(self.embed_stage)

    else:
        self.vertical_spacer3 = QSpacerItem(20, 220)
        self.welcome_layout.addItem(self.vertical_spacer3)
        self.mode_switcher.button_chat.setChecked(True)

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
