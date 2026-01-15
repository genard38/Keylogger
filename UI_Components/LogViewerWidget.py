from tkinter import ttk, scrolledtext
import tkinter as tk
import os
import datetime


class LogViewerWidget:
    """Manage the log content viewer component"""

    def __init__(self, parent):
        self.current_filepath = None
        self._create_widget(parent)


    def _create_widget(self, parent):
        """Create the viewer widget"""
        # Date label
        self.date_label = ttk.Label(
            parent,
            text="No date selected",
            font=("Arial", 12, "bold")
        )
        self.date_label.pack(pady=5)

        # Text viewer
        view_frame = ttk.Frame(parent)
        view_frame.pack(fill=tk.BOTH, expand=True)

        self.text_widget = scrolledtext.ScrolledText(
            view_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Info label
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.info_label = ttk.Label(
            info_frame,
            text="Start keylogger or select a date to view logs",
            font=("Arial", 9),
            foreground="gray"
        )
        self.info_label.pack(side=tk.LEFT)


    def load_file(self, filepath, file_manager):
        """Load and display a log file"""
        self.current_filepath = filepath
        filename = os.path.basename(filepath)

        # Extract and display date
        try:
            date_part = filename.replace("keylog_", "").replace(".txt", "")
            date_obj = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            self.date_label.config(text=f"Log for: {date_obj.strftime('%B %d, %Y')}")
        except:
            self.date_label.config(text=f"Log: {filename}")

        # Load content
        self.text_widget.delete(1.0, tk.END)

        try:
            content = file_manager.read_file(filepath)
            self.text_widget.insert(1.0, content)
            self.text_widget.see(tk.END)
            self.info_label.config(text=f"Loaded: {filename}", foreground="green")
        except Exception as e:
            self.text_widget.insert(1.0, f"Error reading file: {str(e)}")
            self.info_label.config(text=str(e), foreground="red")


    def refresh_current(self, file_manager):
        """Refresh the currently displayed file"""
        if not self.current_filepath:
            return

        current_position = self.text_widget.yview()[0]

        try:
            content = file_manager.read_file(self.current_filepath)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, content)

            # Smart scroll: go to bottom if user was near bottom, otherwise maintain position
            if current_position > 0.9:
                self.text_widget.see(tk.END)
            else:
                self.text_widget.yview_moveto(current_position)
        except:
            pass  # File might be locked


    def clear(self):
        """Clear the viewer"""
        self.current_filepath = None
        self.text_widget.delete(1.0, tk.END)
        self.date_label.config(text="File deleted")