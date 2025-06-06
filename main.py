# main.py
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from ui.main_window import MainWindow


def create_shortcut_once():
    try:
        import winshell
        from win32com.client import Dispatch

        shortcut_name = "LLaMA Assistant.lnk"
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, shortcut_name)

        if os.path.exists(shortcut_path):
            return  # Shortcut already exists, skip creation

        target = os.path.abspath("main.py")
        icon_path = os.path.abspath("icon.ico")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = os.path.dirname(target)
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        shortcut.save()
        print(f"📎 Shortcut created at: {shortcut_path}")
    except ImportError:
        print("⚠️ Shortcut creation skipped (missing winshell or pywin32)")


def main():
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 14))  # Set global font here

        window = MainWindow()
        window.show()

        if sys.platform == "win32":
            create_shortcut_once()

        sys.exit(app.exec())

    except Exception:
        print("🚨 An error occurred during startup!")
        traceback.print_exc()
        input("Press Enter to exit...")  # keeps CMD open


if __name__ == "__main__":
    main()
