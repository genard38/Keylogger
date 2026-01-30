from tkcalendar import Calendar
from UI_Components.FileTreeWidget import FileTreeWidget
from KeyloggerEngine import KeyloggerEngine
from LogFileManager import LogFileManager
from UI_Components.LogViewerWidget import LogViewerWidget
from PlatformUtils import PlatformUtils
from tkinter import ttk
import tkinter as tk
import threading
import datetime
import os


class KeyloggerViewerApp:
    """Main application orchestrating all components"""

    def __init__(self, root):
        self.root = root
        self.root.title("Keylogger with Viewer")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        # Initialize components
        self.get_active_window = PlatformUtils.setup_platform_libraries()
        self.file_manager = LogFileManager()
        self.keylogger = KeyloggerEngine(self.file_manager, self.get_active_window)

        # State
        self.current_executable = "Not running"
        self.search_var = tk.StringVar()  # Initialize here for safety

        # Build UI
        self.create_ui()

        # Start status updates
        self._update_status()

    def create_ui(self):
        """Create the complete UI"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


        #Use PanedWindow to make panels resizable (draggable)
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left_panel = ttk.Frame(paned_window, width=300)
        paned_window.add(left_panel, weight=0)




        # Control panel
        self._create_control_panel(left_panel)

        # File tree
        tree_label = ttk.Label(left_panel, text="Log Files", font=("Arial", 14, "bold"))
        tree_label.pack(pady=(0, 10))

        self.file_tree = FileTreeWidget(left_panel, self.file_manager)
        self.file_tree.on_file_selected = self._on_file_selected
        self.file_tree.on_file_deleted = self._on_file_deleted

        # Search box
        self._create_search_box(left_panel)

        # Calendar
        self._create_calendar(left_panel)

        # Right panel
        right_panel = ttk.Frame(main_frame)
        paned_window.add(right_panel, weight=1)


        # right_panel = ttk.Frame(main_frame)
        # right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status header
        self._create_status_header(right_panel)

        # Log viewer
        self.log_viewer = LogViewerWidget(right_panel)

    def _create_control_panel(self, parent):
        """Create keylogger control panel"""
        control_frame = ttk.LabelFrame(parent, text="Keylogger Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Logging",
            command=self._start_logging,
            style="Start.TButton"
        )
        self.start_btn.pack(fill=tk.X, pady=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="⏸ Stop Logging",
            command=self._stop_logging,
            state=tk.DISABLED,
            style="Stop.TButton"
        )
        self.stop_btn.pack(fill=tk.X, pady=5)

        self.logging_status = ttk.Label(
            control_frame,
            text="● Stopped",
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        self.logging_status.pack(pady=5)

    def _create_search_box(self, parent):
        """Create search box for file tree"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍", font=("Arial", 12)).pack(side=tk.LEFT, padx=(0, 5))
        # self.search_var is now initialized in __init__
        self.search_var.trace('w', lambda *args: self.file_tree.populate(self.search_var.get()))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_calendar(self, parent):
        """Create calendar widget"""
        calendar_label = ttk.Label(parent, text="Select Date", font=("Arial", 14, "bold"))
        calendar_label.pack(pady=(10, 10))

        self.calendar = Calendar(
            parent,
            selectmode='day',
            year=datetime.datetime.now().year,
            month=datetime.datetime.now().month,
            day=datetime.datetime.now().day,
            background="darkblue",
            foreground="white",
            headersbackground="lightblue",
            normalbackground="white",
            weekendbackground="lightyellow",
            selectbackground="red",
            font=("Arial", 10)
        )
        self.calendar.pack(fill=tk.BOTH, expand=True)

        load_btn = ttk.Button(parent, text="Load Selected Date", command=self._load_from_calendar)
        load_btn.pack(pady=10, fill=tk.X)

        refresh_btn = ttk.Button(parent, text="🔄 Refresh Current", command=self._refresh_viewer)
        refresh_btn.pack(pady=(0, 10), fill=tk.X)

    def _create_status_header(self, parent):
        """Create status header"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(status_frame, text="Status:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Arial", 11, "bold"),
            foreground="orange"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(status_frame, text="Tracking:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.executable_label = ttk.Label(
            status_frame,
            text=self.current_executable,
            font=("Arial", 10, "bold"),
            foreground="blue"
        )
        self.executable_label.pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

    # Event handlers
    def _start_logging(self):
        """Start the keylogger"""
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.logging_status.config(text="● Logging", foreground="green")
        self.status_label.config(text="Connected", foreground="green")

        # Start in thread
        threading.Thread(target=self.keylogger.start, daemon=True).start()

    def _stop_logging(self):
        """Stop the keylogger"""
        self.keylogger.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.logging_status.config(text="● Stopped", foreground="red")
        self.status_label.config(text="Ready", foreground="orange")
        self.current_executable = "Not running"

    def _on_file_selected(self, filepath):
        """Handle file selection from tree"""
        self.log_viewer.load_file(filepath, self.file_manager)

    def _on_file_deleted(self, filepath):
        """Handle file deletion"""
        if self.log_viewer.current_filepath == filepath:
            self.log_viewer.clear()

    def _load_from_calendar(self):
        """Load log file from calendar selection"""
        selected_date = self.calendar.get_date()
        date_obj = datetime.datetime.strptime(selected_date, "%m/%d/%y")
        filepath = self.file_manager.get_log_filename(date_obj)

        if os.path.exists(filepath):
            self.log_viewer.load_file(filepath, self.file_manager)
        else:
            self.log_viewer.text_widget.delete(1.0, tk.END)
            self.log_viewer.text_widget.insert(
                1.0,
                f"No log file found for {date_obj.strftime('%B %d, %Y')}\n\n"
                f"Expected file: {filepath}\n\n"
                f"This could mean:\n"
                f"• No keylogging data was recorded on this date\n"
                f"• The log file hasn't been created yet\n"
                f"• The keylogger wasn't running on this date"
            )
            self.log_viewer.date_label.config(text=f"Log for: {date_obj.strftime('%B %d, %Y')}")
            self.log_viewer.info_label.config(text="No log file found", foreground="orange")

    def _refresh_viewer(self):
        """Refresh the current viewer"""
        if self.keylogger.is_running:
            today = datetime.datetime.now()
            self.calendar.selection_set(today)
            self._load_from_calendar()
        else:
            self.log_viewer.refresh_current(self.file_manager)

    def _update_status(self):
        """Update status periodically"""
        if self.keylogger.is_running:
            try:
                self.current_executable = self.get_active_window()
                self.executable_label.config(text=self.current_executable)
            except:
                self.executable_label.config(text="Unknown")

            # Auto-refresh tree
            self.file_tree.populate(self.search_var.get())

            # Auto-refresh viewer if showing today's log
            if self.log_viewer.current_filepath:
                today_log = self.file_manager.get_log_filename()
                if self.log_viewer.current_filepath == today_log:
                    self.log_viewer.refresh_current(self.file_manager)
        else:
            self.executable_label.config(text="Not running")

        self.root.after(2000, self._update_status)