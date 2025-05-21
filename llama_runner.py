import subprocess
import os

def run_llama(prompt):
    llama_bin = r"D:\AI_MODELS\gguf\llama.cpp\build\bin\Release\llama-cli.exe"
    model_path = r"D:\AI_MODELS\gguf\models\llama-2-7b-chat.Q4_K_M.gguf"

    try:
        result = subprocess.run(
            [llama_bin, "-m", model_path, "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
