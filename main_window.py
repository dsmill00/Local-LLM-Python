from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from backend.llama_runner import run_llama

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧠 LLaMA Assistant GUI")
        self.setMinimumSize(600, 400)

        self.layout = QVBoxLayout()

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your prompt here...")
        self.layout.addWidget(self.prompt_input)

        self.submit_button = QPushButton("Send Prompt")
        self.submit_button.clicked.connect(self.run_llama_and_display)
        self.layout.addWidget(self.submit_button)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.layout.addWidget(self.response_output)

        self.setLayout(self.layout)

    def run_llama_and_display(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.response_output.setText("⚠️ Prompt cannot be empty.")
            return

        self.response_output.setText("🧠 Thinking...")
        output = run_llama(prompt)
        self.response_output.setText(output)

