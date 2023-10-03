from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        label = QLabel("⚙️ Settings UI")
        layout.addWidget(label)
        self.setLayout(layout)