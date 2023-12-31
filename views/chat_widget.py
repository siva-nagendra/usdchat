import logging
import os

from pxr import Usd
from PySide6.QtCore import QFile, QSize, Qt, QTextStream, QTimer, Signal
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                               QPushButton, QScrollArea, QSizePolicy,
                               QSpacerItem, QTextEdit, QVBoxLayout, QWidget)

from usdchat.chat_bot import Chat
from usdchat.chat_bridge import ChatBridge
from usdchat.services.chromadb_collections import ChromaDBCollections
from usdchat.utils import chat_thread, embed_thread, process_code
from usdchat.views.chat_bubble import ChatBubble
from usdchat.views.chromadb_collections_ui import collections_frame
from usdchat.views.welcome_screen import init_welcome_screen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setFixedHeight(self.fontMetrics().lineSpacing() + 20)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            selected_text = self.textCursor().selectedText()
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
        elif event.modifiers() & Qt.ShiftModifier and event.key() == Qt.Key_Return:
            new_height = self.height() + 20
            max_height = self.fontMetrics().lineSpacing() * 15 + 10
            new_height = min(new_height, max_height)
            self.setFixedHeight(new_height)
        elif event.key() == Qt.Key_Return:
            if self.parent_widget:
                self.reset_size()
                self.parent_widget.submit_input()
        else:
            doc_height = self.document().size().height()
            max_height = self.fontMetrics().lineSpacing() * 15 + 10
            new_height = min(doc_height + 10, max_height)
            self.setFixedHeight(new_height)

    def reset_size(self):
        default_height = self.fontMetrics().lineSpacing() + 20
        self.setFixedHeight(default_height)


class ChatBotUI(QWidget):
    signal_user_message = Signal(str)
    signal_python_execution_response = Signal(str, bool)
    signal_embed_stage = Signal(str)
    signal_progress_update = Signal(int, str)

    def __init__(
        self,
        config,
        conversation_manager=None,
        usdviewApi=None,
        parent=None,
        standalone=False,
    ):
        super().__init__(parent)
        self.usdviewApi = usdviewApi
        self.standalone = standalone
        self.config = config
        self.conversation_manager = conversation_manager
        self.setWindowTitle(self.config.APP_NAME)
        self.rag_mode = True
        self.model_name = self.config.MODEL
        self.init_ui()
        self.chromadb_collections = ChromaDBCollections(config=self.config)

        self.init_welcome_screen = init_welcome_screen(self)

        self.all_collections = self.chromadb_collections.all_collections()

        self.collection_combo_box.addItems(self.all_collections)

        self.collection_name = self.collection_combo_box.currentText()
        self.conversation_manager.new_session()
        self.chat_bot = Chat(self.model_name, config=self.config)
        self.chat_bridge = ChatBridge(
            self.chat_bot,
            self,
            usdviewApi=self.usdviewApi,
            config=self.config,
            conversation_manager=self.conversation_manager,
            standalone=self.standalone,
            collection_name=self.collection_name,
            rag_mode=self.rag_mode,
        )

        self.chat_thread = chat_thread.ChatThread(
            self.chat_bot, self, "", self.usdviewApi, config=self.config
        )

        self.load_stylesheet()
        self.connect_signals()
        self.activateWindow()
        self.raise_()

        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        width, height = (
            670,
            screen_size.height() - 100,
        )
        self.setMaximumWidth(width)
        self.resize(width, height)
        self.max_attempts = self.config.MAX_ATTEMPTS
        self.current_attempts = 0
        self.settings_widget_created = False

    def connect_signals(self):
        self.signal_user_message.connect(self.chat_bridge.get_bot_response)
        self.chat_bridge.signal_bot_response.connect(self.append_bot_response)
        self.chat_bridge.signal_python_code_ready.connect(
            self.run_python_code_in_main_thread
        )
        self.signal_user_message.connect(self.enable_stop_button)
        self.signal_embed_stage.connect(self.chat_bridge.embed_stage)
        self.chat_bridge.signal_progress_update.connect(
            self.on_progress_update)
        self.chat_bridge.signal_embed_complete.connect(
            self.enable_embed_stage_button)
        self.mode_switcher.signalRagModeChanged.connect(
            self.handle_rag_mode_change)
        # self.signal_user_message.connect(self.settings_ui)

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scroll_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget_contents)

        self.conversation_widget = QWidget(self.scroll_area_widget_contents)
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.addStretch()

        self.scroll_area_layout.addWidget(self.conversation_widget)

        self.user_input = AutoResizingTextEdit(self)
        self.user_input.setObjectName("user_input")
        self.user_input.setPlaceholderText("Ask me anything...")
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.clear_chat_button = QPushButton("🧹 Clear")
        self.clear_chat_button.setObjectName("clear_chat_button")
        self.clear_chat_button.setMinimumHeight(40)

        self.clear_chat_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_chat_button.clicked.connect(self.clear_chat_ui)

        self.submit_button = QPushButton("⎆ Send")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(40)
        self.submit_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addWidget(self.clear_chat_button)
        buttons_layout.addWidget(self.submit_button)
        buttons_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.submit_button.clicked.connect(self.toggle_send_stop)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.user_input)
        self.main_layout.addWidget(buttons_widget)
        self.setLayout(self.main_layout)
        self.setWindowFlags(Qt.Window)

    def browse_directory(self):
        stage_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select USD Stage")
        if stage_file_path:
            self.working_dir_line_edit.setText(stage_file_path)

    def enable_embed_stage_button(self):
        self.embed_stage_button.setText("💿 Create Collection")
        self.embed_stage_button.setProperty("stopMode", False)
        self.embed_stage_button.setStyle(self.embed_stage_button.style())
        self.progress_bar.setVisible(False)
        self.collection_combo_box.addItem(self.collection_name)
        self.collection_combo_box.setCurrentText(self.collection_name)
        self.all_collections = self.chromadb_collections.all_collections()

    def enable_stop_embed_stage_button(self):
        self.embed_stage_button.setText("✋ Stop Embedding")
        self.embed_stage_button.setProperty("stopMode", True)
        self.collection_name_label.setVisible(False)
        self.embed_stage_button.setStyle(self.embed_stage_button.style())

    def delete_collection(self):
        collection_name = self.collection_combo_box.currentText()
        if collection_name:
            self.chromadb_collections.delete_collection(collection_name)
            self.collection_combo_box.removeItem(
                self.collection_combo_box.currentIndex()
            )

    def reset_db(self):
        self.chromadb_collections.reset_db()
        self.collection_combo_box.clear()
        self.collection_combo_box.addItems(
            self.chromadb_collections.all_collections())

    def settings_ui(self):
        if not self.rag_mode:
            return
        if not self.settings_widget_created:
            self.settings_widget_container = QWidget(self)
            self.settings_layout = QVBoxLayout(self.settings_widget_container)
            self.settings_layout.setContentsMargins(0, 0, 0, 0)
            self._collections_frame = collections_frame(
                self, self.settings_widget_container
            )
            self.settings_layout.addWidget(self._collections_frame)
            self.collection_combo_box.addItems(self.all_collections)
            self.collection_combo_box.setCurrentText(self.collection_name)
            self.collection_combo_box.currentTextChanged.connect(
                self.handle_collection_change
            )
            self.main_layout.insertWidget(0, self.settings_widget_container)
            self.settings_widget_created = True
        return self.main_layout

    def check_if_embed_ready(self):
        self.embed_stage_path = self.working_dir_line_edit.text()
        if not self.is_valid_usd_file(self.embed_stage_path):
            self.embed_stage_button.setDisabled(True)
            self.collection_name_label.setVisible(True)
            self.collection_name_label.setText("Invalid USD File")
            return

        self.collection_name = os.path.splitext(
            os.path.basename(self.embed_stage_path)
        )[0]
        self.chat_bridge.collection_name = self.collection_name

        self.collection_name_label.setVisible(True)
        self.collection_name_label.setText(
            f"Collection: {self.collection_name}")
        self.embed_stage_button.setDisabled(False)

    def embed_stage(self):
        self.embed_stage_path = self.working_dir_line_edit.text()

        self.embed_thread = embed_thread.EmbedThread(
            self.embed_stage_path,
            collection_name=self.collection_name,
            config=self.config,
        )

        if self.embed_stage_button.text() == "💿 Create Collection":
            self.signal_embed_stage.emit(self.embed_stage_path)
            self.enable_stop_embed_stage_button()
        else:
            self.chat_bridge.clean_up_thread()
            self.enable_embed_stage_button()

    def handle_collection_change(self):
        self.collection_name = self.collection_combo_box.currentText()
        try:
            self.chat_bridge.collection_name = self.collection_name
        except BaseException:
            pass

    def handle_rag_mode_change(self, newRagMode):
        self.rag_mode = newRagMode
        self.chat_bridge.rag_mode = self.rag_mode
        self.hide_welcome_screen()
        self.scroll_area_layout.removeWidget(self.welcome_widget)
        init_welcome_screen(self)
        self.collection_combo_box.addItems(
            self.chromadb_collections.all_collections())
        self.collection_combo_box.setCurrentText(self.collection_name)

    def is_valid_usd_file(self, file_path):
        try:
            Usd.Stage.Open(file_path)
            return True
        except Exception:
            return False

    def on_progress_update(self, progress, message):
        self.progress_label.setText(message)
        self.progress_bar.setValue(progress)
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)

    def send_button_text(self, button):
        text = button.text()
        self.user_input.setPlainText(text)
        self.submit_input()
        self.hide_welcome_screen()

    def hide_welcome_screen(self):
        for i in reversed(range(self.welcome_layout.count())):
            widget = self.welcome_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.welcome_layout.deleteLater()

    def enable_send_button(self):
        self.submit_button.setText("⎆ Send")
        self.submit_button.setProperty("stopMode", False)
        self.submit_button.setStyle(self.submit_button.style())
        self.submit_button.setEnabled(True)
        self.user_input.setEnabled(True)

    def enable_stop_button(self):
        self.submit_button.setText("✋ Stop")
        self.submit_button.setProperty("stopMode", True)
        self.submit_button.setStyle(self.submit_button.style())
        self.submit_button.setEnabled(True)
        self.user_input.setEnabled(False)

    def toggle_send_stop(self):
        if self.submit_button.text() == "⎆ Send":
            self.submit_input()
        else:
            self.chat_bridge.clean_up_thread()
            self.enable_send_button()

    def clear_chat_ui(self):
        self.chat_bridge.clean_up_thread()
        if self.settings_widget_created:
            self.main_layout.removeWidget(self.settings_widget_container)
            self.settings_widget_container.deleteLater()
        self.scroll_area_layout.removeWidget(self.welcome_widget)
        self.conversation_layout.removeWidget(self.conversation_widget)
        self.conversation_widget.deleteLater()
        self.conversation_widget = QWidget(self.scroll_area_widget_contents)
        self.conversation_layout = QVBoxLayout(self.conversation_widget)
        self.conversation_layout.addStretch()
        self.scroll_area_layout.addWidget(self.conversation_widget)
        self.user_input.reset_size()
        self.user_input.clear()
        # if self.collection_combo_box:
        #     self.collection_combo_box.addItems(self.all_collections)
        #     self.collection_combo_box.setCurrentText(self.collection_name)

        init_welcome_screen(self)
        self.conversation_manager.new_session()
        self.chat_bridge.conversation_manager = self.conversation_manager

    def resizeEvent(self, event):
        self.scroll_area.updateGeometry()
        super().resizeEvent(event)

    def sizeHint(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        height = screen_size.height() - 100
        return QSize(500, height)

    def load_stylesheet(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(
            current_dir,
            "..",
            "resources",
            "stylesheet.qss")
        file = QFile(file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            self.setStyleSheet(stylesheet)
        else:
            logger.error(f"Failed to open {file_path}")

    def submit_input(self):
        try:
            user_input = self.user_input.toPlainText().strip()

            if not user_input:
                logger.warning("User input is empty. No action taken.")
                return
            self.welcome_widget.setVisible(False)
            self.append_message(user_input, "user")
            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )

            QApplication.processEvents()

            self.user_input.reset_size()

            self.user_input.clear()
            self.enable_stop_button()
            self.signal_user_message.emit(user_input)

        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def append_bot_response(self, bot_response):
        try:
            self.temp_bot_message.update_text(bot_response)
            self.scroll_to_end()
        except AttributeError as e:
            logger.error(f"Could not update message in UI due to error: {e}")

    def append_python_output(self, python_output, success, all_responses):
        logger.info(
            f"python_output: {python_output}, success: {success}, all_responses: {all_responses}"
        )
        if not python_output:
            return
        python_bot_message = self.append_message(
            """<div><b><span>🐍 Python Output</span></b></div><hr>""",
            "python_bot",
            success=success,
        )
        python_bot_message.update_text(python_output)
        if not success:
            python_bot_message.update_text(
                f"\nAttempting to fix the error...\n{self.current_attempts}/{self.max_attempts}"
            )
            self.temp_bot_message = self.append_message(
                """<div><b><span>🤖 USD Chat</span></b></div><hr>""", "bot"
            )
            self.signal_user_message.emit(
                f"{all_responses}\n\n\n I get the below error, please fix it. {python_output}"
            )
        self.scroll_to_end()

    def scroll_to_end(self):
        QTimer.singleShot(50, self._scroll_to_end)

    def _scroll_to_end(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def append_message(self, content, sender, success=True):
        chat_bubble = ChatBubble(content, sender, success=success)
        alignment = Qt.AlignRight if sender == "user" else Qt.AlignLeft
        self.conversation_layout.addWidget(chat_bubble, alignment=alignment)
        self.conversation_layout.setAlignment(chat_bubble, alignment)
        self.scroll_to_end()
        self.user_input.setFocus()
        return chat_bubble

    def run_python_code_in_main_thread(self, all_responses):
        output, success = process_code.process_chat_responses(
            all_responses, self.usdviewApi
        )
        if success:
            self.current_attempts = 0
            self.enable_send_button()
        else:
            self.current_attempts += 1

        if self.current_attempts >= self.max_attempts:
            self.current_attempts = 0
            self.signal_user_message.emit("stop")
            self.enable_send_button()

        self.append_python_output(output, success, all_responses)
        self.signal_python_execution_response.emit(output, success)
