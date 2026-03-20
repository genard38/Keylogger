import sys


import os
import ctypes
import platform

from PyQt6.QtWidgets import QApplication

from UI_Components.KeyloggerViewerApp import KeyloggerViewerApp
from UI_Components.ThemeManager import ThemeManager

def main():
    # QApplication is PyQt6's equivalent of dpg.create_context()
    # It Must be create before any widgets
    app = QApplication(sys.argv)
    app.setApplicationName("Keylogger with Viewer")

    # Create and show main window
    window = KeyloggerViewerApp()
    window.show()

    # app.exec() is render loop - replaces your manual while dpg.is_dearpygui_running() loop
    # It blocks here until the window is closed, then returns an exit code
    sys.exit(app.exec())

if __name__ == "__main__":
    main()