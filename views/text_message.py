from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QBrush, QColor, QTextDocument, QTextOption


class TextMessageWidget(QWidget):
    def __init__(self, text, sender, parent=None):
        super().__init__(parent)
        self.text = text
        self.sender = sender
        self.doc = QTextDocument()
        self.doc.setPlainText(self.text)
        self.doc.setDefaultTextOption(QTextOption(Qt.AlignCenter))
        self.doc.setDocumentMargin(10)  # Add some margin around the text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(54, 132, 172) if self.sender == "user" else QColor(103, 103, 103)
        painter.setBrush(QBrush(color))
        painter.setPen(color)
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawRoundedRect(rect, 10, 10)
        painter.translate(rect.topLeft())
        self.doc.drawContents(painter)
        painter.end()

    def sizeHint(self):
        return QSize(
            int(self.doc.idealWidth() + 20), int(self.doc.size().height() + 20)
        )
