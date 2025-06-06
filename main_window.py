# LLaMA 2 GUI Assistant main_window.py
from PySide6.QtWidgets import QMainWindow, QTextEdit, QPushButton, QLineEdit, QVBoxLayout, QWidget, QComboBox, QLabel, QFileDialog
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Signal, Qt 
from backend.llama_runner import LlamaRunnerThread
from backend.memory import load_memory, save_memory
from backend.prompt_optimizer import optimize_prompt
from backend.tokenizer import count_tokens_accurate as count_tokens
from ui.python_highlighter import PythonHighlighter
from backend.file_extractor import extract_text
import os



class ChatInputTextEdit(QTextEdit):
    message_submitted = Signal(str)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            # Submit on Enter
            text = self.toPlainText().strip()
            if text:
                self.message_submitted.emit(text)
                self.clear()
        elif event.key() == Qt.Key_Return and (event.modifiers() & Qt.ShiftModifier):
            # Insert newline
            self.insertPlainText("\n")
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 📏 Set global font size
        from PySide6.QtGui import QFont
        app_font = QFont("Segoe UI", 16)  # Try 12/14 usually ideal for readability
        self.setFont(app_font)

        self.resize(1000, 800)  # Bigger default window size


    # 🌓 Enable dark mode theme
        self.enable_dark_mode()

    # 🧠 Load memory + plugins
        self.chat_history = "SYSTEM: You are a helpful assistant."
        

    # 🧭 Prompt mode dropdown
        self.prompt_mode = QComboBox()
        self.prompt_mode.addItems(["Answer", "Assistant"])

    # 🧠 Skill context dropdown
        self.skill_context = QComboBox()
        self.skill_context.addItems(["General", "Python", "Raspberry Pi", "SQL", "JSON"])

    # 🪪 Title (based on prompt mode)
        self.setWindowTitle(f"LLaMA 2 GUI Assistant – Mode: {self.prompt_mode.currentText()}")

    # 🧾 Widgets
        self.input_box = ChatInputTextEdit()
        self.input_box.setPlaceholderText("Type your message here... (Shift+Enter = newline)")
        self.input_box.setFixedHeight(100)  # Adjust as needed
        self.input_box.message_submitted.connect(self.run_model)
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.highlighter = PythonHighlighter(self.output_box.document())
        self.load_file_button = QPushButton("📂 Load File to LLaMA")

        from backend.vector_store import VectorStore  

        # Vector ingest buttons
        self.load_vector_file_button = QPushButton("📂 Vector: Add File")
        self.load_vector_folder_button = QPushButton("📁 Vector: Add Folder")
        self.preview_chunks_button = QPushButton("🔍 Preview Vector Chunks")
        self.preview_chunks_button.clicked.connect(self.preview_vector_chunks)
        self.load_vector_file_button.clicked.connect(self.ingest_file_to_vector)
        self.load_vector_folder_button.clicked.connect(self.ingest_folder_to_vector)

        # Init vector store
        self.vector_store = VectorStore()

        self.load_file_button.clicked.connect(self.load_file_for_llama)
        self.runner = None

    # 📐 Layout
        layout = QVBoxLayout()
        layout.addWidget(self.skill_context)  # ⬅️ now included
        layout.addWidget(self.prompt_mode)        
        layout.addWidget(self.output_box)
        layout.addWidget(self.input_box)
        layout.addWidget(self.load_file_button)
        layout.addWidget(self.load_vector_file_button)
        layout.addWidget(self.load_vector_folder_button)
        layout.addWidget(self.preview_chunks_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
      


    # 🔗 Connect button
        #self.send_button.clicked.connect(self.run_model)

    # 🔄 Init state
        self.buffered_response = ""


        self.token_label = QLabel("Tokens: 0")
        layout.addWidget(self.token_label)
        self.input_box.textChanged.connect(self.update_token_bar)


    def run_model(self):
        #user_input = self.input_box.text().strip()
        user_input = self.input_box.toPlainText().strip()
        if not user_input:
            return
        
        from backend.vector_store import VectorStore
        store = VectorStore()

        # 🔍 Search vector DB for relevant info
        relevant_chunks = store.query(user_input, top_k=5)
        context_text = "\n".join([c["text"] for c in relevant_chunks])

        self.append_text(f"\nUSER: {user_input}", bold=True)
        self.buffered_response = ""

        mode = self.prompt_mode.currentText()
        if not self.chat_history:
            self.chat_history = "SYSTEM: You are a helpful assistant."

        MAX_TOTAL_TOKENS = 3800  # reserve buffer for system prompt and model output
        RESERVED_FOR_OPTIMIZER = 512
        TRIM_LIMIT = MAX_TOTAL_TOKENS - RESERVED_FOR_OPTIMIZER

        # Build prompt with contextual injection
        if mode == "Answer":
            prompt = f"SYSTEM: Use the following context:\n{context_text}\n\n" + \
            self.chat_history + f"\nUSER: {user_input}\nASSISTANT: Answer:\n"
        else:
            chat_lines = [line for line in self.chat_history.strip().split("\n") if not line.startswith("ASSISTANT:")]
            trimmed_history = []
            total_tokens = count_tokens(f"USER: {user_input}\nASSISTANT:")

            for line in reversed(chat_lines):
                tokens = count_tokens(line)
                if total_tokens + tokens > TRIM_LIMIT:
                    break
                trimmed_history.insert(0, line)
                total_tokens += tokens

            trimmed_history.append(f"USER: {user_input}")
            trimmed_history.append("ASSISTANT:")
            joined = "\n".join(trimmed_history)
            prompt = f"SYSTEM: Use the following context:\n{context_text}\n\n{joined}"


        if hasattr(self, 'runner') and self.runner and self.runner.isRunning():
            self.runner.terminate()

        skill = self.skill_context.currentText()

        # 🛡️ Apply final optimizer
        optimized_prompt = optimize_prompt(prompt.strip(), mode, user_input, skill)
        final_prompt = optimized_prompt.strip()        

        # 🧪 Real final count & safety net
        final_token_count = count_tokens(final_prompt)
        final_token_count += 1
       
        self.token_label.setText(f"Tokens: {final_token_count}")

        # 💾 Debug file
        with open("last_prompt_debug.txt", "w", encoding="utf-8") as f:
            f.write(final_prompt)

        if final_token_count > MAX_TOTAL_TOKENS:
            print(f"❌ REAL prompt too long: {final_token_count} tokens")
            self.append_text(f"[⛔ Prompt too long: {final_token_count} tokens — model limit is {MAX_TOTAL_TOKENS}]", bold=True)
            return

        print(f"🔍 Final Prompt ({final_token_count} tokens):\n{final_prompt}")

        self.setWindowTitle(f"LLaMA 2 GUI Assistant – Mode: {mode}")
        print("🔎 FINAL CLEAN PROMPT:\n", prompt)
        self.runner = LlamaRunnerThread(full_prompt=final_prompt)
        self.runner.output_received.connect(self.append_response_token)
        self.runner.finished.connect(self.on_response_complete)
        self.runner.start()



    def append_response_token(self, token: str):
        self.buffered_response += token
        self.highlight_new_token(token)

    def highlight_new_token(self, token: str):
        cursor = self.output_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#00dd66"))
        cursor.insertText(token, fmt)
        self.output_box.setTextCursor(cursor)
        self.output_box.ensureCursorVisible()

    def append_text(self, text, bold=False):
        cursor = self.output_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setFontWeight(75 if bold else 50)
        cursor.insertText(text + "\n", fmt)
        self.output_box.setTextCursor(cursor)
        self.output_box.ensureCursorVisible()
        self.output_box.verticalScrollBar().setValue(self.output_box.verticalScrollBar().maximum())
        self.input_box.clear()

    def on_response_complete(self):
        if not self.buffered_response.strip():
            self.append_text("[Notice: No response from model.]", bold=False)
            return
        self.check_typo_feedback()

    def check_typo_feedback(self):
        lines = self.chat_history.strip().split("\n")
        if len(lines) < 2:
            return
        user_line = lines[-2]
        response_line = self.buffered_response.strip().split("\n")[0]

        if "USER:" in user_line and not response_line.lower().startswith(user_line[6:].lower()):
            self.append_text("[Notice: Model corrected or inferred meaning from your input.]", bold=False)

    def enable_dark_mode(self):
        from PySide6.QtGui import QPalette, QColor

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, QColor(200, 200, 200))
        dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QLineEdit, QTextEdit {
                background-color: #1e1e1e;
                color: #dddddd;
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #333;
                color: #eee;
                border: 1px solid #666;
            }
            QComboBox {
                background-color: #2b2b2b;
                color: #eee;
            }
        """)

    def load_file_for_llama(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a file to send to LLaMA")
        if file_path:
            try:
                file_text = extract_text(file_path)
                self.input_box.setPlainText(file_text)  # display in input box
                self.append_text(f"[📂 Loaded and displayed file: {os.path.basename(file_path)}]", bold=True)
            except Exception as e:
                self.append_text(f"[❌ Error loading file: {str(e)}]", bold=True)

    def ingest_file_to_vector(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file for vectorization")
        if path:
            try:
                self.vector_store.ingest_file(path)
                self.append_text(f"[✅ File vectorized: {os.path.basename(path)}]", bold=True)
            except Exception as e:
                self.append_text(f"[❌ Error vectorizing file: {str(e)}]", bold=True)

    def ingest_folder_to_vector(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder for vectorization")
        if folder:
            try:
                self.vector_store.ingest_folder(folder)
                self.append_text(f"[✅ Folder vectorized: {os.path.basename(folder)}]", bold=True)
            except Exception as e:
                self.append_text(f"[❌ Error vectorizing folder: {str(e)}]", bold=True)

    def preview_vector_chunks(self):
        try:
            if not hasattr(self, "vector_store"):
                self.append_text("[⚠️ Vector store not initialized]", bold=True)
                return

            all_chunks = self.vector_store.get_all_chunks()
            if not all_chunks:
                self.append_text("[ℹ️ No vector chunks loaded]", bold=True)
                return

            self.append_text("[🔍 Previewing first 5 vector chunks...]", bold=True)
            for i, chunk in enumerate(all_chunks[:5]):
                preview = chunk.get("text", "")[:300]  # Trim to 300 chars
                self.append_text(f"\n[Chunk {i+1}]:\n{preview}")
        except Exception as e:
            self.append_text(f"[❌ Failed to preview chunks: {str(e)}]", bold=True)

    def update_token_bar(self):
        user_input = self.input_box.toPlainText()
        token_count = count_tokens(user_input)
        max_tokens = 3800

        if token_count > max_tokens:
            color = "red"
        elif token_count > max_tokens * 0.8:
            color = "orange"
        else:
            color = "lightgreen"

        self.token_label.setStyleSheet(f"color: {color}")
        self.token_label.setText(f"Tokens: {token_count}")

