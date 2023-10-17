from PySide6.QtCore import QThread, Signal

from usdchat.utils.embed_usda import (create_and_store_embeddings,
                                      heartbeat_chromadb, reset_chromadb)
from usdchat.utils.usd_stage_resolve import resolve_stage


class EmbedThread(QThread):
    signal_embed_complete = Signal(list)
    signal_progress_update = Signal(int, str)

    def __init__(self, stage_path):
        super().__init__()
        self.stage_path = stage_path
        self._is_running = (
            True  # Add a flag to indicate whether the thread should continue running
        )

    def run(self):
        final_paths = resolve_stage(
            self.stage_path, self.signal_progress_update)
        reset_chromadb()
        create_and_store_embeddings(
            files=final_paths,
            signal_progress_update=self.signal_progress_update)
        self.signal_embed_complete.emit(final_paths)

    def stop(self):
        self._is_running = (
            False  # Set the flag to false to indicate that the thread should stop
        )

    # Optionally, you can override the following methods to handle cleanup
    # when the thread is finished or terminated
    def quit(self):
        self.stop()  # Ensure the thread is stopped before quitting
        super().quit()

    def wait(self, *args, **kwargs):
        result = super().wait(*args, **kwargs)
        # Optionally, add any additional cleanup here
        return result
