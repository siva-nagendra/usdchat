from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsWidget(QWidget):
    """
    A widget that displays the settings UI.

    Attributes:
        None

    Methods:
        __init__(self, parent=None)
            Initializes the SettingsWidget.

            Args:
                parent (QWidget): The parent widget. Defaults to None.

        init_ui(self)
            Initializes the UI of the SettingsWidget.
    """

    def __init__(self, parent=None):
        """
        Initializes the SettingsWidget.

        Args:
            parent (QWidget): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI of the SettingsWidget.
        """
        layout = QVBoxLayout()
        label = QLabel("⚙️ Settings UI")
        layout.addWidget(label)
        self.setLayout(layout)
