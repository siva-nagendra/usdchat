from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout)


def collections_frame(self, widget):
    collections_frame = QFrame(widget)
    collections_frame.setObjectName("collections_frame")

    collections_layout = QVBoxLayout(collections_frame)
    collections_layout.setContentsMargins(0, 0, 0, 0)

    collection_manager_label = QLabel("Collection Manager", collections_frame)
    collection_manager_label.setStyleSheet(
        "color: #AAAAAA; font-weight: bold;")

    collections_layout.addWidget(collection_manager_label)

    self.collection_combo_box = QComboBox(collections_frame)
    self.collection_combo_box.setObjectName("collection_combo_box")
    self.collection_combo_box_label = QLabel(
        "All Collections", collections_frame)

    self.collection_combo_box.setFixedHeight(30)

    self.delete_button = QPushButton("❌ Delete", collections_frame)
    self.delete_button.setObjectName("delete_button")
    self.delete_button.setFixedHeight(28)
    self.delete_button.setFixedWidth(100)

    self.reset_db_button = QPushButton("🔄 ResetDB", collections_frame)
    self.reset_db_button.setObjectName("reset_db_button")
    self.reset_db_button.setFixedHeight(28)
    self.reset_db_button.setFixedWidth(100)

    all_collection_layout = QHBoxLayout()
    all_collection_layout.addWidget(self.collection_combo_box_label)
    all_collection_layout.addWidget(self.collection_combo_box)
    all_collection_layout.addWidget(self.delete_button)
    all_collection_layout.addWidget(self.reset_db_button)

    collections_layout.addLayout(all_collection_layout)
    collections_layout.setContentsMargins(0, 0, 0, 0)

    self.delete_button.clicked.connect(self.delete_collection)
    self.reset_db_button.clicked.connect(self.reset_db)

    return collections_frame
