from UI_Components.KeyloggerViewerApp import KeyloggerViewerApp
from tkinter import ttk
import tkinter as tk


def main():
    root = tk.Tk()

    # Configure styles
    style = ttk.Style()
    style.theme_use('clam')  # A modern theme
    style.configure("Start.TButton", foreground="green")
    style.configure("Stop.TButton", foreground="red")

    app = KeyloggerViewerApp(root)

    # Handle window close
    def on_closing():
        # Ensure keylogger is stopped gracefully
        if hasattr(app, 'keylogger') and app.keylogger.is_running:
            app.keylogger.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()