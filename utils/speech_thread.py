from PySide6.QtCore import QThread, Signal
from USDChat.services.text_to_speech import (
    text_to_speech,
)  # Import your text_to_speech function


class SpeechThread(QThread):
    finished_signal = Signal()  # Signal emitted when text_to_speech completes
    error_signal = Signal(str)  # Signal emitted on error, carrying the error message

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            text_to_speech(self.text)
            self.finished_signal.emit()  # Emit signal on success
        except Exception as e:
            print(f"Exception in SpeechThread: {e}")
            self.error_signal.emit(str(e))
