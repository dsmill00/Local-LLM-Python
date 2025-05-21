import sys
import os

# Add the root directory (D:\AI_Assistant_GUI) to Python's import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow as AIAssistant

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIAssistant()
    window.show()
    sys.exit(app.exec())