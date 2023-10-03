from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


class TextMessageWidget(QWidget):
    def __init__(self, text, content_format="text"):
        super().__init__()
        self.content_format = content_format
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout = QVBoxLayout(self)
        self.layout.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Allow horizontal expansion
        self.label = QLabel()
        self.label.setText(text)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Allow horizontal expansion
        self.layout.addWidget(self.label)
        self.layout.setAlignment(Qt.AlignTop)
        # Markdown Formatting
        if self.content_format == "markdown":
            self.content = markdown.markdown(self.content)

        # Code Formatting
        elif self.content_format == "code":
            lexer = get_lexer_by_name("python")  # specify the language
            formatter = HtmlFormatter()
            self.content = highlight(self.content, lexer, formatter)

        self.label.setText(self.content)
        self.layout.addWidget(self.label)
