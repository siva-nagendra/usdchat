from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QPushButton, QSizePolicy,
                               QSpacerItem, QWidget)


class ModeSwitcher(QWidget):
    signalRagModeChanged = Signal(bool)

    def __init__(self, rag_mode):
        super().__init__()
        self.rag_mode = rag_mode
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame(self)
        self.frame.setLayout(self.layout)
        self.horizantal_spacer1 = QSpacerItem(10, 40)
        self.horizantal_spacer2 = QSpacerItem(10, 40)

        self.button_chat = QPushButton("Default Mode")
        self.button_rag = QPushButton("RAG Mode")
        self.button_chat.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.button_rag.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addItem(self.horizantal_spacer1)
        self.layout.addWidget(self.button_chat)
        self.layout.addWidget(self.button_rag)
        self.layout.addItem(self.horizantal_spacer2)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.frame)
        self.setLayout(main_layout)

        self.button_chat.setCheckable(True)
        self.button_rag.setCheckable(True)

        self.button_chat.clicked.connect(self.toggleButtons)
        self.button_rag.clicked.connect(self.toggleButtons)

        self.button_chat.setObjectName("buttonChat")
        self.button_rag.setObjectName("buttonRAG")
        self.frame.setObjectName("mainFrame")

        self.toggleButtons()

    def toggleButtons(self):
        sender = self.sender()
        if sender == self.button_chat:
            self.rag_mode = False
            self.button_chat.setChecked(True)
            self.button_rag.setChecked(False)
            sender.setText("Default Mode")
            self.signalRagModeChanged.emit(self.rag_mode)
        elif sender == self.button_rag:
            self.rag_mode = True
            self.button_chat.setChecked(False)
            self.button_rag.setChecked(True)
            sender.setText("RAG Mode")
            self.signalRagModeChanged.emit(self.rag_mode)
