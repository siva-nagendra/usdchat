from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QProgressBar, QPushButton,
                               QSizePolicy, QVBoxLayout)


def rag_frame(self, widget):
    rag_frame = QFrame(widget)
    rag_frame.setObjectName("rag_frame")

    rag_layout = QVBoxLayout(rag_frame)
    rag_layout.setContentsMargins(0, 0, 0, 0)

    rag_label = QLabel("Create new collection", rag_frame)
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
        QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.embed_stage_button.setDisabled(True)

    create_collection_layout = QHBoxLayout()
    create_collection_layout.addWidget(self.collection_name_label)
    create_collection_layout.addWidget(self.embed_stage_button)

    self.progress_layout = QHBoxLayout()

    self.progress_label = QLabel("", self.welcome_widget)
    self.progress_label.setVisible(False)

    self.progress_bar = QProgressBar(self.welcome_widget)
    self.progress_bar.setVisible(False)
    self.progress_layout.addWidget(self.progress_label)
    self.progress_layout.addWidget(self.progress_bar)

    rag_layout.addLayout(dir_layout)
    rag_layout.addLayout(create_collection_layout)

    rag_layout.addLayout(self.progress_layout)
    rag_layout.setContentsMargins(0, 0, 0, 0)

    return rag_frame
