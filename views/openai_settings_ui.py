import openai
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                               QVBoxLayout)


def openai_settings(self, widget):
    settings_frame = QFrame(widget)
    settings_frame.setObjectName("settings_frame")

    settings_layout = QVBoxLayout(settings_frame)
    settings_layout.setContentsMargins(0, 0, 0, 0)

    setttings_label = QLabel("Openai Settings", settings_frame)
    setttings_label.setStyleSheet("color: #AAAAAA; font-weight: bold;")

    settings_layout.addWidget(setttings_label)

    # Create combo box
    self.model_combo_box = QComboBox(settings_frame)
    self.model_combo_box.setObjectName("model_combo_box")
    self.model_combo_box_label = QLabel("Model", settings_frame)

    self.model_combo_box.setFixedHeight(40)
    model_lst = [model["id"]
                 for model in openai.Model.list()["data"] if "gpt" in model["id"]]

    self.model_combo_box.addItems(model_lst)

    all_settings_layout = QHBoxLayout()
    all_settings_layout.addWidget(self.model_combo_box_label)
    all_settings_layout.addWidget(self.model_combo_box)

    settings_layout.addLayout(all_settings_layout)
    settings_layout.setContentsMargins(0, 0, 0, 0)

    return settings_frame
