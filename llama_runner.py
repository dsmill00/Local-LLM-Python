# backend/llama_runner.py
import subprocess
import tempfile
import os
from PySide6.QtCore import QThread, Signal

LLAMA_CLI_PATH = r"D:\AI_MODELS\gguf\llama.cpp\build\bin\Release\llama-cli.exe"
MODEL_PATH = r"D:\AI_MODELS\gguf\models\llama-2-13b-chat.Q4_K_M.gguf"

class LlamaRunnerThread(QThread):
    output_received = Signal(str)

    def __init__(self, full_prompt: str = ""):
        super().__init__()
        self.full_prompt = full_prompt
        self.external_prompt_file = None  # for file-injected prompts

    def inject_file(self, filepath: str):
        # Build a temporary prompt file from loaded text
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                contents = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:  # fallback for non-UTF8
                contents = f.read()


        fd, temp_path = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            out.write(f"SYSTEM: You are a helpful assistant.\nUSER:\n{contents}\nASSISTANT:")

        self.external_prompt_file = temp_path
        self.start()  # Launch threaded `run()`

    def run(self):
        print("🧠 Launching model subprocess...")

        if self.external_prompt_file:
            prompt_file_path = self.external_prompt_file
        else:
            with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tmpfile:
                tmpfile.write(self.full_prompt)
                tmpfile.flush()
                prompt_file_path = tmpfile.name

        cmd = [
            LLAMA_CLI_PATH,
            "-m", MODEL_PATH,
            "-t", "16",
            "-ngl", "99",
            "--n-predict", "1024",
            "--file", prompt_file_path,
            "--reverse-prompt", "USER:",
        ]

        print("🧪 Launch CMD:", cmd)
        print("🧪 Prompt Sent to Model:\n", self.full_prompt or f"[from file: {prompt_file_path}]")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding='utf-8',  # this ensures it doesn't default to cp1252
            errors='replace'   # replaces un-decodable chars instead of crashing
)

        in_response = False
        for line in process.stdout:
            if "llama_model_loader" in line or "llama_tokenizer" in line:
                continue

            print("🧪 Model Output Line:", line.strip())

            if not in_response:
                if "Answer:" in line or "ASSISTANT:" in line:
                    in_response = True
                    self.output_received.emit(line)
                    continue
                continue

            self.output_received.emit(line)
            if "[end of text]" in line:
                break

        process.stdout.close()
        process.wait()
        self.output_received.emit("\n")

        # Clean up temp prompt file
        if self.external_prompt_file:
            os.remove(self.external_prompt_file)
            self.external_prompt_file = None

        self.quit()











